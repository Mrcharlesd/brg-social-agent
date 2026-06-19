import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engines.distribution.state import DistributionState, load_state, save_state


def test_load_state_returns_empty_state_when_no_file(tmp_path):
    post_dir = tmp_path / "my-post-abc12345"
    post_dir.mkdir()
    state = load_state(post_dir)
    assert state.post_id == "my-post-abc12345"
    assert state.platforms == {}


def test_load_state_reads_existing_distributed_json(tmp_path):
    post_dir = tmp_path / "my-post-abc12345"
    post_dir.mkdir()
    data = {
        "post_id": "my-post-abc12345",
        "platforms": {"instagram": "2026-06-19T12:00:00+00:00"},
    }
    (post_dir / "distributed.json").write_text(json.dumps(data), encoding="utf-8")
    state = load_state(post_dir)
    assert state.post_id == "my-post-abc12345"
    assert "instagram" in state.platforms


def test_save_state_writes_distributed_json(tmp_path):
    post_dir = tmp_path / "my-post-abc12345"
    post_dir.mkdir()
    state = DistributionState(
        post_id="my-post-abc12345",
        platforms={"linkedin": "2026-06-19T12:00:00+00:00"},
    )
    save_state(state, post_dir)
    written = json.loads(
        (post_dir / "distributed.json").read_text(encoding="utf-8")
    )
    assert written["post_id"] == "my-post-abc12345"
    assert written["platforms"]["linkedin"] == "2026-06-19T12:00:00+00:00"


def test_is_distributed_to_returns_false_when_platform_absent():
    state = DistributionState(post_id="test-post", platforms={})
    assert state.is_distributed_to("instagram") is False


def test_is_distributed_to_returns_true_when_platform_present():
    state = DistributionState(
        post_id="test-post",
        platforms={"instagram": "2026-06-19T12:00:00+00:00"},
    )
    assert state.is_distributed_to("instagram") is True


def test_mark_distributed_returns_new_state_with_platform_added():
    state = DistributionState(post_id="test-post", platforms={})
    updated = state.mark_distributed("linkedin")
    assert "linkedin" in updated.platforms
    assert updated.post_id == "test-post"


def test_mark_distributed_does_not_mutate_original():
    state = DistributionState(post_id="test-post", platforms={})
    _ = state.mark_distributed("linkedin")
    assert state.platforms == {}
