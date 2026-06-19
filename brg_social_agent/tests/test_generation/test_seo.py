import pytest
from engines.generation.models import (
    CarouselContent, CarouselSlide, ContentPackage,
    PostContent, QuoteContent, ScriptContent,
    StoryContent, StoryFrame,
)


def _slide() -> CarouselSlide:
    return CarouselSlide(title="T", body="B", speaker_note="N")


def _make_package(hashtags: list[str], post_body: str = "The post body.") -> ContentPackage:
    return ContentPackage(
        post_id="test-id",
        trend_title="Test",
        trend_url="https://example.com",
        mood="dark",
        carousel=CarouselContent(
            hook_slide=_slide(),
            content_slides=[_slide(), _slide(), _slide()],
            cta_slide=_slide(),
        ),
        post=PostContent(body=post_body),
        script=ScriptContent(hook="H", body="B", cta="C", duration_seconds=30),
        quote=QuoteContent(quote="Quote.", attribution="— CB"),
        story=StoryContent(
            frames=[
                StoryFrame(text="a", purpose="hook"),
                StoryFrame(text="b", purpose="insight"),
                StoryFrame(text="c", purpose="cta"),
            ]
        ),
        hashtags=hashtags,
        generated_at="2026-01-01T00:00:00+00:00",
    )


def test_validate_hashtags_trims_to_max_15():
    from engines.generation.seo import validate_hashtags
    pkg = _make_package([f"#Tag{i}" for i in range(20)])
    result = validate_hashtags(pkg)
    assert len(result.hashtags) == 15


def test_validate_hashtags_pads_to_min_10():
    from engines.generation.seo import validate_hashtags
    pkg = _make_package(["#Leadership", "#BRG"])
    result = validate_hashtags(pkg)
    assert len(result.hashtags) >= 10


def test_validate_hashtags_leaves_valid_count_unchanged():
    from engines.generation.seo import validate_hashtags
    twelve_tags = [f"#Tag{i}" for i in range(12)]
    pkg = _make_package(twelve_tags)
    result = validate_hashtags(pkg)
    assert len(result.hashtags) == 12


def test_validate_hashtags_does_not_mutate_original():
    from engines.generation.seo import validate_hashtags
    twenty_tags = [f"#Tag{i}" for i in range(20)]
    pkg = _make_package(twenty_tags)
    _ = validate_hashtags(pkg)
    assert len(pkg.hashtags) == 20  # original unchanged (frozen model)


def test_add_location_signals_appends_to_post_body():
    from engines.generation.seo import add_location_signals
    pkg = _make_package(["#Leadership"] * 10, post_body="Execution matters.")
    result = add_location_signals(pkg)
    assert result.post.body.startswith("Execution matters.")
    assert "Chicago, IL" in result.post.body


def test_add_location_signals_populates_location_signals_field():
    from engines.generation.seo import add_location_signals
    pkg = _make_package(["#Leadership"] * 10)
    result = add_location_signals(pkg)
    assert len(result.location_signals) > 0
    assert any("IL" in loc or "TX" in loc or "GA" in loc for loc in result.location_signals)


def test_add_location_signals_does_not_mutate_original():
    from engines.generation.seo import add_location_signals
    pkg = _make_package(["#Leadership"] * 10, post_body="Original body.")
    _ = add_location_signals(pkg)
    assert pkg.post.body == "Original body."  # frozen model unchanged
