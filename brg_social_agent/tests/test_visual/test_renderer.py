import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import MagicMock, patch

from engines.generation.models import ContentPackage
from engines.visual.brand import BrandContext
from engines.visual.renderer import _build_specs, render_package
from tests.conftest import make_test_config


# ---- fixtures ----

@pytest.fixture
def package(sample_content_package_dict):
    return ContentPackage.model_validate(sample_content_package_dict)


@pytest.fixture
def brand(sample_brand):
    return sample_brand


# ---- _build_specs tests (no Playwright needed) ----

def test_build_specs_returns_four_content_types(package, brand):
    specs = _build_specs(package, brand)
    assert set(specs.keys()) == {"carousel", "quote", "story", "thumbnail"}


def test_build_specs_carousel_count_matches_slides(package, brand):
    specs = _build_specs(package, brand)
    total_slides = 1 + len(package.carousel.content_slides) + 1
    assert len(specs["carousel"]) == total_slides


def test_build_specs_carousel_first_is_hook(package, brand):
    specs = _build_specs(package, brand)
    first = specs["carousel"][0]
    assert first.context["is_hook"] is True
    assert first.context["is_cta"] is False


def test_build_specs_carousel_last_is_cta(package, brand):
    specs = _build_specs(package, brand)
    last = specs["carousel"][-1]
    assert last.context["is_hook"] is False
    assert last.context["is_cta"] is True


def test_build_specs_carousel_slide_index_sequential(package, brand):
    specs = _build_specs(package, brand)
    for i, spec in enumerate(specs["carousel"]):
        assert spec.context["slide_index"] == i


def test_build_specs_carousel_uses_correct_dimensions(package, brand):
    specs = _build_specs(package, brand)
    for spec in specs["carousel"]:
        assert spec.width == 1080
        assert spec.height == 1080


def test_build_specs_quote_uses_correct_dimensions(package, brand):
    specs = _build_specs(package, brand)
    assert len(specs["quote"]) == 1
    assert specs["quote"][0].width == 1080
    assert specs["quote"][0].height == 1080


def test_build_specs_story_has_three_frames(package, brand):
    specs = _build_specs(package, brand)
    assert len(specs["story"]) == 3


def test_build_specs_story_uses_correct_dimensions(package, brand):
    specs = _build_specs(package, brand)
    for spec in specs["story"]:
        assert spec.width == 1080
        assert spec.height == 1920


def test_build_specs_story_frame_purposes_match_package(package, brand):
    specs = _build_specs(package, brand)
    expected = [f.purpose for f in package.story.frames]
    actual = [s.context["frame_purpose"] for s in specs["story"]]
    assert actual == expected


def test_build_specs_thumbnail_uses_correct_dimensions(package, brand):
    specs = _build_specs(package, brand)
    assert len(specs["thumbnail"]) == 1
    assert specs["thumbnail"][0].width == 1280
    assert specs["thumbnail"][0].height == 720


def test_build_specs_carousel_filenames_are_zero_padded(package, brand):
    specs = _build_specs(package, brand)
    assert specs["carousel"][0].output_filename == "carousel_slide_000.png"
    assert specs["carousel"][1].output_filename == "carousel_slide_001.png"


def test_build_specs_story_filenames_are_zero_padded(package, brand):
    specs = _build_specs(package, brand)
    assert specs["story"][0].output_filename == "story_frame_000.png"
    assert specs["story"][1].output_filename == "story_frame_001.png"


def test_build_specs_quote_passes_quote_text(package, brand):
    specs = _build_specs(package, brand)
    assert specs["quote"][0].context["quote_text"] == package.quote.quote


def test_build_specs_quote_headshot_has_file_prefix_when_present(package, sample_brand):
    # Build a brand with a headshot path set
    brand_with_headshot = BrandContext(
        primary_color=sample_brand.primary_color,
        accent_color=sample_brand.accent_color,
        font_family=sample_brand.font_family,
        logo_svg=sample_brand.logo_svg,
        headshot_path="/path/to/headshot.jpg",
    )
    specs = _build_specs(package, brand_with_headshot)
    ctx = specs["quote"][0].context
    assert ctx["headshot_path"] == "file:///path/to/headshot.jpg"
    assert ctx["show_headshot"] is True


def test_build_specs_quote_headshot_empty_when_none(package, sample_brand):
    specs = _build_specs(package, sample_brand)  # sample_brand.headshot_path is None
    ctx = specs["quote"][0].context
    assert ctx["headshot_path"] == ""
    assert ctx["show_headshot"] is False


def test_build_specs_thumbnail_passes_hook_and_title(package, brand):
    specs = _build_specs(package, brand)
    ctx = specs["thumbnail"][0].context
    assert ctx["hook_text"] == package.script.hook
    assert ctx["topic_title"] == package.trend_title


# ---- render_package unit tests (Playwright mocked) ----

def _make_mock_playwright():
    """Return (mock_sync_playwright, mock_browser, mock_page) with correct chain wired up."""
    mock_page = MagicMock()
    mock_browser = MagicMock()
    mock_browser.new_page.return_value = mock_page
    mock_pw_instance = MagicMock()
    mock_pw_instance.chromium.launch.return_value = mock_browser
    mock_sync_playwright = MagicMock()
    mock_sync_playwright.return_value.__enter__.return_value = mock_pw_instance
    mock_sync_playwright.return_value.__exit__.return_value = False
    return mock_sync_playwright, mock_browser, mock_page


def test_render_package_creates_output_dir(tmp_path, package, brand):
    mock_pw, _, _ = _make_mock_playwright()
    out_dir = tmp_path / "render_out"
    assert not out_dir.exists()

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        render_package(package, brand, out_dir)

    assert out_dir.exists()


def test_render_package_returns_four_content_type_keys(tmp_path, package, brand):
    mock_pw, _, _ = _make_mock_playwright()

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        results = render_package(package, brand, tmp_path / "out")

    assert set(results.keys()) == {"carousel", "quote", "story", "thumbnail"}


def test_render_package_screenshot_called_for_each_spec(tmp_path, package, brand):
    mock_pw, _, mock_page = _make_mock_playwright()
    specs = _build_specs(package, brand)
    expected_screenshot_count = sum(len(v) for v in specs.values())

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        render_package(package, brand, tmp_path / "out")

    assert mock_page.screenshot.call_count == expected_screenshot_count


def test_render_package_closes_browser_on_completion(tmp_path, package, brand):
    mock_pw, mock_browser, _ = _make_mock_playwright()

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        render_package(package, brand, tmp_path / "out")

    mock_browser.close.assert_called_once()


def test_render_package_closes_browser_on_exception(tmp_path, package, brand):
    mock_pw, mock_browser, mock_page = _make_mock_playwright()
    mock_page.screenshot.side_effect = RuntimeError("Playwright crash")

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        with pytest.raises(RuntimeError, match="Playwright crash"):
            render_package(package, brand, tmp_path / "out")

    mock_browser.close.assert_called_once()


def test_render_package_sets_viewport_per_spec(tmp_path, package, brand):
    mock_pw, _, mock_page = _make_mock_playwright()

    with patch("engines.visual.renderer.sync_playwright", mock_pw):
        render_package(package, brand, tmp_path / "out")

    viewport_calls = mock_page.set_viewport_size.call_args_list
    # At least one 1080×1080 and one 1080×1920 and one 1280×720
    sizes = [c.args[0] for c in viewport_calls]
    assert {"width": 1080, "height": 1080} in sizes
    assert {"width": 1080, "height": 1920} in sizes
    assert {"width": 1280, "height": 720} in sizes


# ---- Integration test (requires: playwright install chromium) ----

@pytest.mark.integration
def test_render_package_outputs_correct_image_dimensions(tmp_path, package, brand):
    """Requires `playwright install chromium`. Run with: pytest -m integration"""
    from PIL import Image

    out_dir = tmp_path / "output"
    results = render_package(package, brand, out_dir)

    # Carousel slides: check first slide dimensions
    carousel_paths = results["carousel"]
    assert len(carousel_paths) == 1 + len(package.carousel.content_slides) + 1
    img = Image.open(carousel_paths[0])
    assert img.size == (1080, 1080)

    # Quote
    img = Image.open(results["quote"][0])
    assert img.size == (1080, 1080)

    # Story frames
    assert len(results["story"]) == 3
    img = Image.open(results["story"][0])
    assert img.size == (1080, 1920)

    # Thumbnail
    img = Image.open(results["thumbnail"][0])
    assert img.size == (1280, 720)
