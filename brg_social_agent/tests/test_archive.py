import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.archive import _active_platforms, archive_distributed_posts
from tests.conftest import make_test_config


def _write_state(post_dir: Path, platforms: dict) -> None:
    post_dir.mkdir(parents=True, exist_ok=True)
    (post_dir / "content.json").write_text("{}", encoding="utf-8")
    (post_dir / "distributed.json").write_text(
        json.dumps({"post_id": post_dir.name, "platforms": platforms}), encoding="utf-8"
    )


def test_active_platforms_returns_both_when_both_configured(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="ig-123",
        linkedin_person_id="li-abc",
    )
    assert _active_platforms(config) == ["instagram", "linkedin"]


def test_active_platforms_excludes_platform_with_missing_credential(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="",
        linkedin_person_id="li-abc",
    )
    assert _active_platforms(config) == ["linkedin"]


def test_active_platforms_returns_empty_when_none_configured(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="",
        linkedin_person_id="",
    )
    assert _active_platforms(config) == []


def test_archive_moves_fully_distributed_post(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="ig-123",
        linkedin_person_id="li-abc",
    )
    post_dir = Path(config.queue_dir) / "post-abc"
    _write_state(post_dir, {"instagram": "2026-01-01T00:00:00+00:00", "linkedin": "2026-01-01T00:01:00+00:00"})

    result = archive_distributed_posts(config)

    assert result == ["post-abc"]
    assert not post_dir.exists()
    assert (Path(config.posted_dir) / "post-abc").exists()


def test_archive_skips_partially_distributed_post(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="ig-123",
        linkedin_person_id="li-abc",
    )
    post_dir = Path(config.queue_dir) / "post-partial"
    _write_state(post_dir, {"instagram": "2026-01-01T00:00:00+00:00"})

    result = archive_distributed_posts(config)

    assert result == []
    assert post_dir.exists()


def test_archive_skips_post_with_no_state_file(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
    )
    post_dir = Path(config.queue_dir) / "post-no-state"
    post_dir.mkdir(parents=True, exist_ok=True)

    result = archive_distributed_posts(config)

    assert result == []
    assert post_dir.exists()


def test_archive_returns_empty_when_queue_dir_missing(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
    )
    result = archive_distributed_posts(config)
    assert result == []


def test_archive_returns_empty_when_no_active_platforms(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram", "linkedin"],
        instagram_account_id="",
        linkedin_person_id="",
    )
    post_dir = Path(config.queue_dir) / "post-xyz"
    _write_state(post_dir, {})

    result = archive_distributed_posts(config)

    assert result == []
    assert post_dir.exists()


def test_archive_creates_posted_dir_if_missing(tmp_path):
    config = make_test_config(
        tmp_path,
        enabled_platforms=["instagram"],
        instagram_account_id="ig-123",
    )
    post_dir = Path(config.queue_dir) / "post-new"
    _write_state(post_dir, {"instagram": "2026-01-01T00:00:00+00:00"})

    assert not Path(config.posted_dir).exists()
    archive_distributed_posts(config)
    assert Path(config.posted_dir).exists()
