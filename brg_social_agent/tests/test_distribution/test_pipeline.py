import sys
import json
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engines.distribution import run_distribution_pipeline
from tests.conftest import make_test_config


def _write_content(post_dir: Path, content_dict: dict) -> None:
    post_dir.mkdir(parents=True, exist_ok=True)
    (post_dir / "content.json").write_text(json.dumps(content_dict), encoding="utf-8")


def _write_png(post_dir: Path, filename: str = "carousel_slide_000.png") -> Path:
    p = post_dir / filename
    p.write_bytes(b"\x89PNG")
    return p


def test_returns_empty_list_when_queue_dir_missing(tmp_path):
    config = make_test_config(tmp_path)
    result = run_distribution_pipeline(config)
    assert result == []


def test_skips_post_without_content_json(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_dir = Path(config.queue_dir) / "no-content-dir"
    post_dir.mkdir(parents=True)
    _write_png(post_dir)
    with patch("engines.distribution.InstagramPublisher") as MockIG:
        result = run_distribution_pipeline(config)
    assert result == []
    MockIG.return_value.publish_carousel.assert_not_called()


def test_skips_unrendered_post(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_dir = Path(config.queue_dir) / sample_content_package_dict["post_id"]
    _write_content(post_dir, sample_content_package_dict)
    # No PNG files — not yet rendered
    with patch("engines.distribution.InstagramPublisher") as MockIG:
        result = run_distribution_pipeline(config)
    assert result == []
    MockIG.return_value.publish_carousel.assert_not_called()


def test_distributes_to_instagram_when_enabled(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "carousel_slide_000.png")

    with patch("engines.distribution.InstagramPublisher") as MockIG:
        MockIG.return_value.publish_carousel.return_value = "media-1"
        result = run_distribution_pipeline(config)

    assert result == [post_id]
    MockIG.return_value.publish_carousel.assert_called_once()


def test_distributes_to_linkedin_when_enabled(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["linkedin"],
        linkedin_person_id="li-abc",
        linkedin_access_token="li-tok",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "quote.png")

    with patch("engines.distribution.LinkedInPublisher") as MockLI:
        MockLI.return_value.publish_post.return_value = "urn:li:ugcPost:1"
        result = run_distribution_pipeline(config)

    assert result == [post_id]
    MockLI.return_value.publish_post.assert_called_once()


def test_skips_already_distributed_post(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "carousel_slide_000.png")
    # Pre-write state marking instagram done
    state_data = {"post_id": post_id, "platforms": {"instagram": "2026-06-19T12:00:00+00:00"}}
    (post_dir / "distributed.json").write_text(json.dumps(state_data), encoding="utf-8")

    with patch("engines.distribution.InstagramPublisher") as MockIG:
        result = run_distribution_pipeline(config)

    assert result == []
    MockIG.return_value.publish_carousel.assert_not_called()


def test_continues_on_distribution_failure(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "carousel_slide_000.png")

    with patch("engines.distribution.InstagramPublisher") as MockIG:
        MockIG.return_value.publish_carousel.side_effect = Exception("API error")
        result = run_distribution_pipeline(config)

    assert result == []  # failed, but no exception propagated


def test_saves_state_after_distribution(tmp_path, sample_content_package_dict):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "carousel_slide_000.png")

    with patch("engines.distribution.InstagramPublisher") as MockIG:
        MockIG.return_value.publish_carousel.return_value = "media-1"
        run_distribution_pipeline(config)

    state_path = post_dir / "distributed.json"
    assert state_path.exists()
    state_data = json.loads(state_path.read_text(encoding="utf-8"))
    assert "instagram" in state_data["platforms"]


def test_returns_post_id_when_one_platform_fails_but_other_succeeds(
    tmp_path, sample_content_package_dict
):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="ig-123",
        instagram_access_token="ig-tok",
        image_base_url="https://example.com/queue",
        linkedin_person_id="li-abc",
        linkedin_access_token="li-tok",
    )
    post_id = sample_content_package_dict["post_id"]
    post_dir = Path(config.queue_dir) / post_id
    _write_content(post_dir, sample_content_package_dict)
    _write_png(post_dir, "carousel_slide_000.png")
    _write_png(post_dir, "quote.png")

    with patch("engines.distribution.InstagramPublisher") as MockIG, \
         patch("engines.distribution.LinkedInPublisher") as MockLI:
        MockIG.return_value.publish_carousel.side_effect = Exception("IG API error")
        MockLI.return_value.publish_post.return_value = "urn:li:ugcPost:1"
        result = run_distribution_pipeline(config)

    assert result == [post_id]
