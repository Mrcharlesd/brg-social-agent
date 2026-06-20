import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from main import run_agent, _write_run_log
from engines.orchestrator import PhaseResult, RunResult
from tests.conftest import make_test_config


def _make_run_result(started="2026-01-01T00:00:00+00:00", finished="2026-01-01T00:01:00+00:00"):
    phases = [
        PhaseResult(name="intelligence", ids=[{"title": "t"}]),
        PhaseResult(name="generation", ids=["id1"]),
        PhaseResult(name="visual", ids=["id1"]),
        PhaseResult(name="distribution", ids=["id1"]),
    ]
    return RunResult(started_at=started, finished_at=finished, phases=phases)


def test_write_run_log_creates_file(tmp_path):
    config = make_test_config(tmp_path)
    result = _make_run_result()
    _write_run_log(result, config)
    logs_dir = Path(config.logs_dir)
    log_files = list(logs_dir.glob("run-*.json"))
    assert len(log_files) == 1
    data = json.loads(log_files[0].read_text(encoding="utf-8"))
    assert data["started_at"] == "2026-01-01T00:00:00+00:00"
    assert len(data["phases"]) == 4


def test_write_run_log_filename_matches_started_at_timestamp(tmp_path):
    config = make_test_config(tmp_path)
    result = _make_run_result(started="2026-06-19T12:34:56+00:00")
    _write_run_log(result, config)
    logs_dir = Path(config.logs_dir)
    log_files = list(logs_dir.glob("run-*.json"))
    assert log_files[0].name == "run-20260619123456.json"


def test_run_agent_all_calls_full_pipeline_and_archive(tmp_path):
    config = make_test_config(tmp_path)
    mock_result = _make_run_result()
    with patch("main.run_full_pipeline", return_value=mock_result) as mock_pipe, \
         patch("main.archive_distributed_posts", return_value=["id1"]) as mock_archive, \
         patch("main._write_run_log") as mock_log:
        run_agent(config, phase="all")
    mock_pipe.assert_called_once_with(config)
    mock_archive.assert_called_once_with(config)
    mock_log.assert_called_once_with(mock_result, config)


def test_run_agent_intel_calls_only_intelligence_pipeline(tmp_path):
    config = make_test_config(tmp_path)
    with patch("main.run_intelligence_pipeline", return_value=[]) as mock_intel, \
         patch("main.run_full_pipeline") as mock_full:
        run_agent(config, phase="intel")
    mock_intel.assert_called_once_with(config)
    mock_full.assert_not_called()


def test_run_agent_generate_calls_only_generation_pipeline(tmp_path):
    config = make_test_config(tmp_path)
    with patch("main.run_generation_pipeline", return_value=[]) as mock_gen, \
         patch("main.run_full_pipeline") as mock_full:
        run_agent(config, phase="generate")
    mock_gen.assert_called_once_with(config)
    mock_full.assert_not_called()


def test_run_agent_visual_calls_only_visual_pipeline(tmp_path):
    config = make_test_config(tmp_path)
    with patch("main.run_visual_pipeline", return_value=[]) as mock_vis, \
         patch("main.run_full_pipeline") as mock_full:
        run_agent(config, phase="visual")
    mock_vis.assert_called_once_with(config)
    mock_full.assert_not_called()


def test_run_agent_distribute_calls_distribution_and_archive(tmp_path):
    config = make_test_config(tmp_path)
    with patch("main.run_distribution_pipeline", return_value=["id1"]) as mock_dist, \
         patch("main.archive_distributed_posts", return_value=[]) as mock_archive, \
         patch("main.run_full_pipeline") as mock_full:
        run_agent(config, phase="distribute")
    mock_dist.assert_called_once_with(config)
    mock_archive.assert_called_once_with(config)
    mock_full.assert_not_called()


def test_write_run_log_json_contains_phases_and_timestamps(tmp_path):
    config = make_test_config(tmp_path)
    result = _make_run_result(
        started="2026-06-19T08:00:00+00:00",
        finished="2026-06-19T08:01:30+00:00",
    )
    _write_run_log(result, config)
    logs_dir = Path(config.logs_dir)
    log_files = list(logs_dir.glob("run-*.json"))
    data = json.loads(log_files[0].read_text(encoding="utf-8"))
    assert data["finished_at"] == "2026-06-19T08:01:30+00:00"
    phase_names = [p["name"] for p in data["phases"]]
    assert phase_names == ["intelligence", "generation", "visual", "distribution"]
