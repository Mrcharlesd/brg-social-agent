import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from tests.conftest import make_test_config

from engines.visual.brand import BrandContext, load_brand_context


def test_brand_context_has_correct_colors():
    config = make_test_config()
    brand = load_brand_context(config)
    assert brand.primary_color == "#1A1A2E"
    assert brand.accent_color == "#E94560"
    assert brand.font_family == "Inter"


def test_brand_context_is_immutable():
    config = make_test_config()
    brand = load_brand_context(config)
    with pytest.raises(Exception):
        brand.primary_color = "#ffffff"


def test_brand_context_logo_missing_returns_empty_string(tmp_path):
    config = make_test_config(tmp_path=tmp_path, logo_path=str(tmp_path / "no_logo.svg"))
    brand = load_brand_context(config)
    assert brand.logo_svg == ""


def test_brand_context_loads_logo_svg(tmp_path):
    svg_content = "<svg><rect width='100' height='100'/></svg>"
    logo_file = tmp_path / "test_logo.svg"
    logo_file.write_text(svg_content, encoding="utf-8")
    config = make_test_config(tmp_path=tmp_path, logo_path=str(logo_file))
    brand = load_brand_context(config)
    assert brand.logo_svg == svg_content


def test_brand_context_headshot_missing_returns_none(tmp_path):
    config = make_test_config(tmp_path=tmp_path, headshot_path=str(tmp_path / "no_photo.jpg"))
    brand = load_brand_context(config)
    assert brand.headshot_path is None


def test_brand_context_headshot_exists_returns_path(tmp_path):
    hs_file = tmp_path / "headshot.jpg"
    hs_file.write_bytes(b"\xff\xd8\xff")  # minimal JPEG magic bytes
    config = make_test_config(tmp_path=tmp_path, headshot_path=str(hs_file))
    brand = load_brand_context(config)
    assert brand.headshot_path is not None
    assert "headshot.jpg" in brand.headshot_path
