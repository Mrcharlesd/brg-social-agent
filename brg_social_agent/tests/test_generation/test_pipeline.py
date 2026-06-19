import json
from pathlib import Path
from unittest.mock import patch

from engines.generation.models import (
    CarouselContent, CarouselSlide, ContentPackage,
    PostContent, QuoteContent, ScriptContent,
    StoryContent, StoryFrame,
)
from config import Config


def _make_config(tmp_path: Path) -> Config:
    config = Config.__new__(Config)
    config.anthropic_api_key = "test-key"
    config.trends_file = str(tmp_path / "trends.json")
    config.queue_dir = str(tmp_path / "queue")
    return config


def _slide() -> CarouselSlide:
    return CarouselSlide(title="T", body="B", speaker_note="N")


def _make_package(post_id: str = "test-topic-abc12345") -> ContentPackage:
    return ContentPackage(
        post_id=post_id,
        trend_title="Test Topic",
        trend_url="https://example.com",
        mood="dark",
        carousel=CarouselContent(
            hook_slide=_slide(),
            content_slides=[_slide(), _slide(), _slide()],
            cta_slide=_slide(),
        ),
        post=PostContent(body="Leadership is a discipline. " * 10),
        script=ScriptContent(hook="H", body="B", cta="C", duration_seconds=30),
        quote=QuoteContent(quote="Quote.", attribution="— CB"),
        story=StoryContent(
            frames=[
                StoryFrame(text="a", purpose="hook"),
                StoryFrame(text="b", purpose="insight"),
                StoryFrame(text="c", purpose="cta"),
            ]
        ),
        hashtags=["#Leadership"] * 10,
        generated_at="2026-01-01T00:00:00+00:00",
    )


def _write_trends(tmp_path: Path, items: list[dict]) -> None:
    with open(tmp_path / "trends.json", "w") as f:
        json.dump({"generated_at": "2026-01-01T00:00:00+00:00", "items": items}, f)


_SAMPLE_ITEM = {
    "title": "Test Topic",
    "body": "Context text about leadership.",
    "source": "HBR",
    "url": "https://hbr.org",
    "timestamp": "2026-01-01T00:00:00+00:00",
    "likes": 0,
    "shares": 0,
    "comments": 0,
    "score": 0.75,
}


def test_pipeline_writes_content_json(tmp_path):
    from engines.generation import run_generation_pipeline
    _write_trends(tmp_path, [_SAMPLE_ITEM])
    config = _make_config(tmp_path)
    pkg = _make_package()

    with patch("engines.generation.generate_content_package", return_value=pkg), \
         patch("engines.generation.voice_check", return_value=True):
        post_ids = run_generation_pipeline(config)

    assert len(post_ids) == 1
    content_file = Path(config.queue_dir) / post_ids[0] / "content.json"
    assert content_file.exists()
    data = json.loads(content_file.read_text())
    assert data["trend_title"] == "Test Topic"


def test_pipeline_returns_empty_list_when_no_trends_file(tmp_path):
    from engines.generation import run_generation_pipeline
    config = _make_config(tmp_path)
    # trends.json not written — file does not exist
    assert run_generation_pipeline(config) == []


def test_pipeline_skips_item_on_two_voice_check_failures(tmp_path):
    from engines.generation import run_generation_pipeline
    _write_trends(tmp_path, [_SAMPLE_ITEM])
    config = _make_config(tmp_path)
    pkg = _make_package()

    with patch("engines.generation.generate_content_package", return_value=pkg), \
         patch("engines.generation.voice_check", return_value=False):
        post_ids = run_generation_pipeline(config)

    assert post_ids == []


def test_pipeline_succeeds_after_one_voice_check_retry(tmp_path):
    from engines.generation import run_generation_pipeline
    _write_trends(tmp_path, [_SAMPLE_ITEM])
    config = _make_config(tmp_path)
    pkg = _make_package()

    # First check fails, second passes
    voice_results = [False, True]

    with patch("engines.generation.generate_content_package", return_value=pkg), \
         patch("engines.generation.voice_check", side_effect=voice_results):
        post_ids = run_generation_pipeline(config)

    assert len(post_ids) == 1


def test_pipeline_skips_item_on_generation_exception(tmp_path):
    from engines.generation import run_generation_pipeline
    _write_trends(tmp_path, [_SAMPLE_ITEM])
    config = _make_config(tmp_path)

    with patch(
        "engines.generation.generate_content_package",
        side_effect=ValueError("Claude error"),
    ):
        post_ids = run_generation_pipeline(config)

    assert post_ids == []


def test_pipeline_processes_multiple_items(tmp_path):
    from engines.generation import run_generation_pipeline
    items = [
        {**_SAMPLE_ITEM, "title": f"Topic {i}"}
        for i in range(3)
    ]
    _write_trends(tmp_path, items)
    config = _make_config(tmp_path)

    packages = [_make_package(post_id=f"topic-{i}-00000000") for i in range(3)]

    with patch("engines.generation.generate_content_package", side_effect=packages), \
         patch("engines.generation.voice_check", return_value=True):
        post_ids = run_generation_pipeline(config)

    assert len(post_ids) == 3
