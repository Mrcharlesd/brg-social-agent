import sys
import json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from unittest.mock import patch, MagicMock

from engines.visual import run_visual_pipeline
from tests.conftest import make_test_config


def test_pipeline_returns_empty_when_queue_dir_missing(tmp_path):
    config = make_test_config(tmp_path=tmp_path)
    # queue_dir is set to tmp_path/queue, which doesn't exist yet
    result = run_visual_pipeline(config)
    assert result == []


def test_pipeline_returns_empty_when_queue_is_empty(tmp_path):
    config = make_test_config(tmp_path=tmp_path)
    (tmp_path / "queue").mkdir(parents=True)
    result = run_visual_pipeline(config)
    assert result == []


def test_pipeline_skips_dir_without_content_json(tmp_path):
    config = make_test_config(tmp_path=tmp_path)
    post_dir = tmp_path / "queue" / "orphan-post-00000000"
    post_dir.mkdir(parents=True)
    with patch("engines.visual.render_package") as mock_render:
        result = run_visual_pipeline(config)
    assert result == []
    mock_render.assert_not_called()


def test_pipeline_processes_valid_content_package(tmp_path, sample_content_package_dict):
    config = make_test_config(tmp_path=tmp_path)
    post_id = sample_content_package_dict["post_id"]
    post_dir = tmp_path / "queue" / post_id
    post_dir.mkdir(parents=True)
    (post_dir / "content.json").write_text(
        json.dumps(sample_content_package_dict), encoding="utf-8"
    )

    with patch("engines.visual.render_package") as mock_render:
        mock_render.return_value = {
            "carousel": [post_dir / "carousel_slide_000.png"],
            "quote": [post_dir / "quote.png"],
            "story": [post_dir / "story_frame_000.png"],
            "thumbnail": [post_dir / "thumbnail.png"],
        }
        result = run_visual_pipeline(config)

    assert result == [post_id]
    mock_render.assert_called_once()


def test_pipeline_skips_already_rendered_packages(tmp_path, sample_content_package_dict):
    config = make_test_config(tmp_path=tmp_path)
    post_id = sample_content_package_dict["post_id"]
    post_dir = tmp_path / "queue" / post_id
    post_dir.mkdir(parents=True)
    (post_dir / "content.json").write_text(
        json.dumps(sample_content_package_dict), encoding="utf-8"
    )
    # Simulate existing PNG (already rendered)
    (post_dir / "quote.png").write_bytes(b"")

    with patch("engines.visual.render_package") as mock_render:
        result = run_visual_pipeline(config)

    assert result == []
    mock_render.assert_not_called()


def test_pipeline_continues_when_one_render_fails(tmp_path, sample_content_package_dict):
    config = make_test_config(tmp_path=tmp_path)

    # Create two post dirs
    ids = ["post-aaa-00000000", "post-bbb-11111111"]
    for post_id in ids:
        post_dir = tmp_path / "queue" / post_id
        post_dir.mkdir(parents=True)
        pkg = dict(sample_content_package_dict)
        pkg["post_id"] = post_id
        (post_dir / "content.json").write_text(json.dumps(pkg), encoding="utf-8")

    call_count = 0

    def side_effect(package, brand, out_dir):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise RuntimeError("Playwright crashed")
        return {"carousel": [], "quote": [], "story": [], "thumbnail": []}

    with patch("engines.visual.render_package", side_effect=side_effect):
        result = run_visual_pipeline(config)

    # First package failed, second succeeded
    assert result == ["post-bbb-11111111"]


def test_pipeline_continues_on_invalid_content_json(tmp_path):
    config = make_test_config(tmp_path=tmp_path)
    post_dir = tmp_path / "queue" / "bad-package-00000000"
    post_dir.mkdir(parents=True)
    (post_dir / "content.json").write_text("not valid json", encoding="utf-8")

    with patch("engines.visual.render_package") as mock_render:
        result = run_visual_pipeline(config)

    assert result == []
    mock_render.assert_not_called()


def test_pipeline_passes_brand_context_to_renderer(tmp_path, sample_content_package_dict, sample_brand):
    config = make_test_config(tmp_path=tmp_path)
    post_id = sample_content_package_dict["post_id"]
    post_dir = tmp_path / "queue" / post_id
    post_dir.mkdir(parents=True)
    (post_dir / "content.json").write_text(
        json.dumps(sample_content_package_dict), encoding="utf-8"
    )

    with patch("engines.visual.load_brand_context", return_value=sample_brand) as mock_lbc:
        with patch("engines.visual.render_package") as mock_render:
            mock_render.return_value = {"carousel": [], "quote": [], "story": [], "thumbnail": []}
            run_visual_pipeline(config)

    mock_lbc.assert_called_once_with(config)
    # brand passed as second arg to render_package
    _, call_brand, _ = mock_render.call_args.args
    assert call_brand is sample_brand
