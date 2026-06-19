import logging
from dataclasses import dataclass, field
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from playwright.sync_api import sync_playwright

from engines.generation.models import ContentPackage
from .brand import BrandContext

log = logging.getLogger(__name__)

LAYOUTS_DIR = Path(__file__).parent / "layouts"

_CAROUSEL_W, _CAROUSEL_H = 1080, 1080
_QUOTE_W, _QUOTE_H = 1080, 1080
_STORY_W, _STORY_H = 1080, 1920
_THUMBNAIL_W, _THUMBNAIL_H = 1280, 720


@dataclass(frozen=True)
class _RenderSpec:
    template_name: str
    width: int
    height: int
    context: dict
    output_filename: str


def _build_specs(package: ContentPackage, brand: BrandContext) -> dict[str, list[_RenderSpec]]:
    """Build render specs for all content types without touching the browser."""
    all_slides = (
        [package.carousel.hook_slide]
        + list(package.carousel.content_slides)
        + [package.carousel.cta_slide]
    )
    total = len(all_slides)

    carousel_specs: list[_RenderSpec] = [
        _RenderSpec(
            template_name="carousel.html",
            width=_CAROUSEL_W,
            height=_CAROUSEL_H,
            context={
                "brand": brand,
                "mood": package.mood,
                "slide_title": slide.title,
                "slide_body": slide.body,
                "slide_index": i,
                "total_slides": total,
                "is_hook": i == 0,
                "is_cta": i == total - 1,
            },
            output_filename=f"carousel_slide_{i:03d}.png",
        )
        for i, slide in enumerate(all_slides)
    ]

    quote_specs: list[_RenderSpec] = [
        _RenderSpec(
            template_name="quote.html",
            width=_QUOTE_W,
            height=_QUOTE_H,
            context={
                "brand": brand,
                "mood": package.mood,
                "quote_text": package.quote.quote,
                "attribution": package.quote.attribution,
                "show_headshot": brand.headshot_path is not None,
                "headshot_path": brand.headshot_path or "",
            },
            output_filename="quote.png",
        )
    ]

    story_specs: list[_RenderSpec] = [
        _RenderSpec(
            template_name="story.html",
            width=_STORY_W,
            height=_STORY_H,
            context={
                "brand": brand,
                "mood": package.mood,
                "frame_text": frame.text,
                "frame_purpose": frame.purpose,
                "frame_index": i,
            },
            output_filename=f"story_frame_{i:03d}.png",
        )
        for i, frame in enumerate(package.story.frames)
    ]

    thumbnail_specs: list[_RenderSpec] = [
        _RenderSpec(
            template_name="thumbnail.html",
            width=_THUMBNAIL_W,
            height=_THUMBNAIL_H,
            context={
                "brand": brand,
                "mood": package.mood,
                "hook_text": package.script.hook,
                "topic_title": package.trend_title,
            },
            output_filename="thumbnail.png",
        )
    ]

    return {
        "carousel": carousel_specs,
        "quote": quote_specs,
        "story": story_specs,
        "thumbnail": thumbnail_specs,
    }


def render_package(
    package: ContentPackage,
    brand: BrandContext,
    out_dir: Path,
) -> dict[str, list[Path]]:
    """
    Render all visuals for a content package to out_dir as PNG files.
    Returns {content_type: [output_paths]}.
    Raises on Playwright failure (caller handles retries/logging).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    specs = _build_specs(package, brand)
    env = Environment(loader=FileSystemLoader(str(LAYOUTS_DIR)), autoescape=False)

    results: dict[str, list[Path]] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        try:
            for content_type, render_specs in specs.items():
                paths: list[Path] = []
                for spec in render_specs:
                    html = env.get_template(spec.template_name).render(**spec.context)
                    page.set_viewport_size({"width": spec.width, "height": spec.height})
                    page.set_content(html, wait_until="networkidle")
                    out_path = out_dir / spec.output_filename
                    page.screenshot(path=str(out_path), full_page=False)
                    paths.append(out_path)
                    log.debug("Rendered %s", out_path)
                results[content_type] = paths
        finally:
            browser.close()

    return results
