import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from engines.orchestrator import PhaseResult, RunResult, run_full_pipeline
from tests.conftest import make_test_config


def test_run_result_to_dict_includes_all_phases():
    phase = PhaseResult(name="intelligence", ids=["a", "b"])
    result = RunResult(started_at="2026-01-01T00:00:00+00:00", finished_at="2026-01-01T00:01:00+00:00", phases=[phase])
    d = result.to_dict()
    assert d["started_at"] == "2026-01-01T00:00:00+00:00"
    assert d["finished_at"] == "2026-01-01T00:01:00+00:00"
    assert len(d["phases"]) == 1
    assert d["phases"][0] == {"name": "intelligence", "ids": ["a", "b"], "error": None}


def test_phase_result_captures_error_message():
    phase = PhaseResult(name="generation", ids=[], error="API timeout")
    d = phase.__dict__
    assert d["error"] == "API timeout"
    assert d["ids"] == []


def test_run_full_pipeline_calls_all_four_phases(tmp_path):
    config = make_test_config(tmp_path)
    with patch("engines.orchestrator.run_intelligence_pipeline", return_value=[{"title": "t1"}]) as mock_intel, \
         patch("engines.orchestrator.run_generation_pipeline", return_value=["id1"]) as mock_gen, \
         patch("engines.orchestrator.run_visual_pipeline", return_value=["id1"]) as mock_vis, \
         patch("engines.orchestrator.run_distribution_pipeline", return_value=["id1"]) as mock_dist:
        result = run_full_pipeline(config)
    mock_intel.assert_called_once_with(config)
    mock_gen.assert_called_once_with(config)
    mock_vis.assert_called_once_with(config)
    mock_dist.assert_called_once_with(config)
    assert len(result.phases) == 4


def test_run_full_pipeline_records_ids_per_phase(tmp_path):
    config = make_test_config(tmp_path)
    with patch("engines.orchestrator.run_intelligence_pipeline", return_value=[{"title": "t1"}]), \
         patch("engines.orchestrator.run_generation_pipeline", return_value=["gen-1", "gen-2"]), \
         patch("engines.orchestrator.run_visual_pipeline", return_value=["gen-1"]), \
         patch("engines.orchestrator.run_distribution_pipeline", return_value=["gen-1"]):
        result = run_full_pipeline(config)
    gen_phase = next(p for p in result.phases if p.name == "generation")
    assert gen_phase.ids == ["gen-1", "gen-2"]
    assert gen_phase.error is None


def test_run_full_pipeline_isolates_phase_error(tmp_path):
    config = make_test_config(tmp_path)
    with patch("engines.orchestrator.run_intelligence_pipeline", side_effect=RuntimeError("network down")), \
         patch("engines.orchestrator.run_generation_pipeline", return_value=[]) as mock_gen, \
         patch("engines.orchestrator.run_visual_pipeline", return_value=[]) as mock_vis, \
         patch("engines.orchestrator.run_distribution_pipeline", return_value=[]) as mock_dist:
        result = run_full_pipeline(config)
    intel_phase = next(p for p in result.phases if p.name == "intelligence")
    assert intel_phase.error == "network down"
    assert intel_phase.ids == []
    mock_gen.assert_called_once()
    mock_vis.assert_called_once()
    mock_dist.assert_called_once()


def test_run_full_pipeline_has_started_and_finished_timestamps(tmp_path):
    config = make_test_config(tmp_path)
    with patch("engines.orchestrator.run_intelligence_pipeline", return_value=[]), \
         patch("engines.orchestrator.run_generation_pipeline", return_value=[]), \
         patch("engines.orchestrator.run_visual_pipeline", return_value=[]), \
         patch("engines.orchestrator.run_distribution_pipeline", return_value=[]):
        result = run_full_pipeline(config)
    assert result.started_at.endswith("+00:00") or result.started_at.endswith("Z")
    assert result.finished_at >= result.started_at
