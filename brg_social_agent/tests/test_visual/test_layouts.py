import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from jinja2 import Environment, FileSystemLoader

from engines.visual.brand import BrandContext

LAYOUTS_DIR = Path(__file__).parent.parent.parent / "engines" / "visual" / "layouts"


@pytest.fixture
def jinja_env():
    return Environment(loader=FileSystemLoader(str(LAYOUTS_DIR)), autoescape=False)


@pytest.fixture
def test_brand():
    return BrandContext(
        primary_color="#1A1A2E",
        accent_color="#E94560",
        font_family="Inter",
        logo_svg="<svg><rect/></svg>",
        headshot_path=None,
    )


def _base_carousel_ctx(brand, **kwargs):
    ctx = dict(
        brand=brand, mood="dark", slide_title="Test Title",
        slide_body="Test body text.", slide_index=0,
        total_slides=5, is_hook=True, is_cta=False,
    )
    ctx.update(kwargs)
    return ctx


# ---------- carousel.html ----------

def test_carousel_renders_slide_title(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand)
    )
    assert "Test Title" in html


def test_carousel_dark_mood_uses_primary_color_as_bg(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand, mood="dark")
    )
    assert "#1A1A2E" in html


def test_carousel_light_mood_uses_white_bg(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand, mood="light")
    )
    assert "#FFFFFF" in html or "ffffff" in html.lower()


def test_carousel_hook_slide_shows_brg_label(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand, is_hook=True, is_cta=False)
    )
    assert "Battle Rhythm Group" in html


def test_carousel_cta_slide_shows_follow_text(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand, is_hook=False, is_cta=True)
    )
    # CTA slide body should include the follow/CTA text
    assert "Follow" in html or "BRG" in html


def test_carousel_injects_accent_color(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand)
    )
    assert "#E94560" in html


def test_carousel_shows_slide_counter_on_content_slide(jinja_env, test_brand):
    html = jinja_env.get_template("carousel.html").render(
        **_base_carousel_ctx(test_brand, is_hook=False, is_cta=False, slide_index=2, total_slides=5)
    )
    assert "5" in html  # total_slides appears in counter


# ---------- quote.html ----------

def test_quote_renders_quote_text(jinja_env, test_brand):
    html = jinja_env.get_template("quote.html").render(
        brand=test_brand, mood="dark",
        quote_text="Excellence is a habit.", attribution="Charles Butler",
        show_headshot=False, headshot_path="",
    )
    assert "Excellence is a habit." in html


def test_quote_renders_attribution(jinja_env, test_brand):
    html = jinja_env.get_template("quote.html").render(
        brand=test_brand, mood="dark",
        quote_text="Test quote.", attribution="Charles Butler — BRG",
        show_headshot=False, headshot_path="",
    )
    assert "Charles Butler" in html


def test_quote_headshot_hidden_when_show_headshot_false(jinja_env, test_brand):
    html = jinja_env.get_template("quote.html").render(
        brand=test_brand, mood="dark",
        quote_text="Test.", attribution="Test.",
        show_headshot=False, headshot_path="/some/path.jpg",
    )
    assert "/some/path.jpg" not in html


def test_quote_headshot_visible_when_show_headshot_true(jinja_env, test_brand):
    html = jinja_env.get_template("quote.html").render(
        brand=test_brand, mood="dark",
        quote_text="Test.", attribution="Test.",
        show_headshot=True, headshot_path="/path/to/headshot.jpg",
    )
    assert "/path/to/headshot.jpg" in html


def test_quote_injects_accent_color(jinja_env, test_brand):
    html = jinja_env.get_template("quote.html").render(
        brand=test_brand, mood="dark",
        quote_text="Test.", attribution="Test.",
        show_headshot=False, headshot_path="",
    )
    assert "#E94560" in html


# ---------- story.html ----------

def test_story_renders_frame_text(jinja_env, test_brand):
    html = jinja_env.get_template("story.html").render(
        brand=test_brand, mood="dark",
        frame_text="Leaders act before they feel ready.",
        frame_purpose="hook", frame_index=0,
    )
    assert "Leaders act before they feel ready." in html


def test_story_hook_frame_shows_hook_label(jinja_env, test_brand):
    html = jinja_env.get_template("story.html").render(
        brand=test_brand, mood="dark",
        frame_text="Test.", frame_purpose="hook", frame_index=0,
    )
    assert "Hook" in html


def test_story_cta_frame_shows_action_label(jinja_env, test_brand):
    html = jinja_env.get_template("story.html").render(
        brand=test_brand, mood="dark",
        frame_text="Test.", frame_purpose="cta", frame_index=2,
    )
    assert "Action" in html or "BRG" in html


def test_story_progress_bar_marks_correct_frame(jinja_env, test_brand):
    html = jinja_env.get_template("story.html").render(
        brand=test_brand, mood="dark",
        frame_text="Test.", frame_purpose="insight", frame_index=1,
    )
    assert "complete" in html  # progress segment CSS class


# ---------- thumbnail.html ----------

def test_thumbnail_renders_hook_text(jinja_env, test_brand):
    html = jinja_env.get_template("thumbnail.html").render(
        brand=test_brand, mood="dark",
        hook_text="What separates great leaders from average ones?",
        topic_title="Discipline Over Motivation",
    )
    assert "What separates great leaders from average ones?" in html


def test_thumbnail_renders_topic_title(jinja_env, test_brand):
    html = jinja_env.get_template("thumbnail.html").render(
        brand=test_brand, mood="dark",
        hook_text="Test hook.",
        topic_title="Discipline Over Motivation",
    )
    assert "Discipline Over Motivation" in html


def test_thumbnail_shows_brg_branding(jinja_env, test_brand):
    html = jinja_env.get_template("thumbnail.html").render(
        brand=test_brand, mood="dark",
        hook_text="Test.", topic_title="Test.",
    )
    assert "Battle Rhythm Group" in html or "BRG" in html
