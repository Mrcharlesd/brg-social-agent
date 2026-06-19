import logging
from pathlib import Path

from config import Config
from engines.generation.models import ContentPackage

from .brand import load_brand_context
from .renderer import render_package

log = logging.getLogger(__name__)


def run_visual_pipeline(config: Config) -> list[str]:
    """
    Scan queue_dir for unrendered content packages and render their visuals.
    A package is considered already rendered if any .png file exists in its directory.
    Idempotent — safe to call multiple times.
    Returns list of post_ids rendered in this run.
    """
    queue_dir = Path(config.queue_dir)
    if not queue_dir.exists():
        log.warning("queue_dir not found at %s — nothing to render", queue_dir)
        return []

    brand = load_brand_context(config)
    post_ids: list[str] = []

    for post_dir in sorted(queue_dir.iterdir()):
        if not post_dir.is_dir():
            continue

        content_path = post_dir / "content.json"
        if not content_path.exists():
            continue

        if any(post_dir.glob("*.png")):
            log.info("Skipping %s — already rendered", post_dir.name)
            continue

        try:
            package = ContentPackage.model_validate_json(
                content_path.read_text(encoding="utf-8")
            )
        except Exception as exc:
            log.warning("Failed to load content package at %s: %s", content_path, exc)
            continue

        try:
            results = render_package(package, brand, post_dir)
        except Exception as exc:
            log.warning("Render failed for %s: %s", post_dir.name, exc)
            continue

        total = sum(len(paths) for paths in results.values())
        log.info("Rendered %d images for %s", total, package.post_id)
        post_ids.append(package.post_id)

    return post_ids
