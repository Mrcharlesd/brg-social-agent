import pytest
from pydantic import ValidationError


def _slide(title: str = "Title", body: str = "Body", speaker_note: str = "Note"):
    from engines.generation.models import CarouselSlide
    return CarouselSlide(title=title, body=body, speaker_note=speaker_note)


def _carousel():
    from engines.generation.models import CarouselContent
    return CarouselContent(
        hook_slide=_slide(),
        content_slides=[_slide() for _ in range(3)],
        cta_slide=_slide(),
    )


def _package():
    from engines.generation.models import (
        ContentPackage, PostContent, ScriptContent,
        QuoteContent, StoryContent, StoryFrame,
    )
    return ContentPackage(
        post_id="test-id",
        trend_title="Test Topic",
        trend_url="https://example.com",
        mood="dark",
        carousel=_carousel(),
        post=PostContent(body="Leadership is a discipline. " * 10),
        script=ScriptContent(hook="H", body="B", cta="C", duration_seconds=45),
        quote=QuoteContent(
            quote="Execution is the only strategy that matters.",
            attribution="— Charles Butler, Battle Rhythm Group",
        ),
        story=StoryContent(
            frames=[
                StoryFrame(text="Hook text", purpose="hook"),
                StoryFrame(text="Insight text", purpose="insight"),
                StoryFrame(text="CTA text", purpose="cta"),
            ]
        ),
        generated_at="2026-01-01T00:00:00+00:00",
    )


def test_content_package_is_frozen():
    pkg = _package()
    with pytest.raises(ValidationError):
        pkg.mood = "light"  # type: ignore


def test_make_post_id_is_deterministic():
    from engines.generation.models import make_post_id
    assert make_post_id("Same Title") == make_post_id("Same Title")


def test_make_post_id_differs_for_different_titles():
    from engines.generation.models import make_post_id
    assert make_post_id("Title One") != make_post_id("Title Two")


def test_make_post_id_max_length():
    from engines.generation.models import make_post_id
    long_title = "A" * 200
    assert len(make_post_id(long_title)) <= 50


def test_carousel_content_slides_min_3():
    from engines.generation.models import CarouselContent
    with pytest.raises(ValidationError):
        CarouselContent(
            hook_slide=_slide(),
            content_slides=[_slide(), _slide()],  # only 2 — must fail
            cta_slide=_slide(),
        )


def test_carousel_content_slides_max_8():
    from engines.generation.models import CarouselContent
    with pytest.raises(ValidationError):
        CarouselContent(
            hook_slide=_slide(),
            content_slides=[_slide() for _ in range(9)],  # 9 > 8 — must fail
            cta_slide=_slide(),
        )


def test_story_must_have_exactly_3_frames():
    from engines.generation.models import StoryContent, StoryFrame
    with pytest.raises(ValidationError):
        StoryContent(
            frames=[
                StoryFrame(text="a", purpose="hook"),
                StoryFrame(text="b", purpose="insight"),
            ]  # only 2 — must fail
        )


def test_script_duration_min_20():
    from engines.generation.models import ScriptContent
    with pytest.raises(ValidationError):
        ScriptContent(hook="h", body="b", cta="c", duration_seconds=19)


def test_script_duration_max_60():
    from engines.generation.models import ScriptContent
    with pytest.raises(ValidationError):
        ScriptContent(hook="h", body="b", cta="c", duration_seconds=61)


def test_content_package_mood_must_be_light_or_dark():
    from engines.generation.models import (
        ContentPackage, PostContent, ScriptContent,
        QuoteContent, StoryContent, StoryFrame,
    )
    with pytest.raises(ValidationError):
        ContentPackage(
            post_id="x",
            trend_title="T",
            trend_url="https://example.com",
            mood="blue",  # invalid — must fail
            carousel=_carousel(),
            post=PostContent(body="body"),
            script=ScriptContent(hook="h", body="b", cta="c", duration_seconds=30),
            quote=QuoteContent(quote="Q.", attribution="— CB"),
            story=StoryContent(frames=[
                StoryFrame(text="a", purpose="hook"),
                StoryFrame(text="b", purpose="insight"),
                StoryFrame(text="c", purpose="cta"),
            ]),
            generated_at="2026-01-01T00:00:00+00:00",
        )


def test_content_package_round_trips_to_json():
    pkg = _package()
    json_str = pkg.model_dump_json()
    from engines.generation.models import ContentPackage
    restored = ContentPackage.model_validate_json(json_str)
    assert restored.post_id == pkg.post_id
    assert restored.mood == pkg.mood
