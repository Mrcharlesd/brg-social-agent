# BRG Social Media Agent Phase 5: Orchestration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Wire Phases 1–4 into a single autonomous run loop with post archiving, run logging, and a CLI entrypoint that supports both full runs and targeted single-phase invocations.

**Architecture:** A new `engines/orchestrator.py` calls all four pipeline functions in sequence, error-isolating each phase so a failure in one doesn't abort the others. A new `engines/archive.py` moves fully-distributed posts from `queue/` to `posted/`. `main.py` is updated to delegate to the orchestrator, write a timestamped JSON run log, and accept a `--phase` flag for targeted runs.

**Tech Stack:** Python 3.11+, stdlib only (`argparse`, `shutil`, `re`, `json`, `dataclasses`), pytest, existing phase engine functions.

## Global Constraints

- Python 3.9 runtime in practice; use `from __future__ import annotations` in any file that uses `str | None` or other union syntax in annotations.
- All `read_text()` / `write_text()` calls use `encoding="utf-8"`.
- All new dataclasses use `@dataclass(frozen=True)`.
- No new third-party dependencies — stdlib only for Phase 5 additions.
- Git root: `BRG Academy/BRG System/` — all git commands run from there.
- Python source root (for imports): `brg_social_agent/` — all production imports are relative to this directory.
- Test files outside a sub-package add `sys.path.insert(0, str(Path(__file__).parent.parent))` to reach the source root.
- Test suite command: `python3 -m pytest tests/ -q -m "not integration"` (run from `brg_social_agent/`).
- `make_test_config(tmp_path, **overrides)` from `tests/conftest.py` is the only way to build a `Config` in tests.
- When patching in tests, use the namespace where the name is **imported**, not where it is defined (e.g., patch `engines.orchestrator.run_intelligence_pipeline`, not `engines.intelligence.run_intelligence_pipeline`).
- `shutil.move(str(src), str(dst))` for moving directories.
- Active-platform check mirrors the distribution pipeline: a platform is active when it appears in `config.enabled_platforms` AND its identity credential is non-empty (`instagram_account_id` for instagram, `linkedin_person_id` for linkedin).
- Run log path pattern: `data/logs/run-YYYYMMDDHHMMSS.json` where the timestamp is derived from `RunResult.started_at` (ISO 8601, first 19 chars, digits only).

---

## File Map

| Action | Path |
|--------|------|
| Create | `brg_social_agent/engines/orchestrator.py` |
| Create | `brg_social_agent/engines/archive.py` |
| Modify | `brg_social_agent/main.py` |
| Create | `brg_social_agent/tests/test_orchestrator.py` |
| Create | `brg_social_agent/tests/test_archive.py` |
| Create | `brg_social_agent/tests/test_main.py` |

---

## Interfaces Produced by Existing Phases (read-only)

These signatures come from the already-implemented phases. Do not change them.

```python
# Phase 1 — engines/intelligence/__init__.py
def run_intelligence_pipeline(config: Config) -> list[dict]: ...

# Phase 2 — engines/generation/__init__.py
def run_generation_pipeline(config: Config) -> list[str]: ...

# Phase 3 — engines/visual/__init__.py
def run_visual_pipeline(config: Config) -> list[str]: ...

# Phase 4 — engines/distribution/__init__.py
def run_distribution_pipeline(config: Config) -> list[str]: ...

# Phase 4 state — engines/distribution/state.py
@dataclass(frozen=True)
class DistributionState:
    post_id: str
    platforms: dict[str, str]
    def is_distributed_to(self, platform: str) -> bool: ...

def load_state(post_dir: Path) -> DistributionState: ...
```

---

## Task 1: Orchestrator

**Files:**
- Create: `brg_social_agent/engines/orchestrator.py`
- Test: `brg_social_agent/tests/test_orchestrator.py`

**Interfaces:**
- Consumes: all four `run_*_pipeline(config)` functions (see above)
- Produces:
  ```python
  @dataclass(frozen=True)
  class PhaseResult:
      name: str
      ids: list[str]
      error: str | None = None

  @dataclass(frozen=True)
  class RunResult:
      started_at: str   # ISO 8601 UTC
      finished_at: str  # ISO 8601 UTC
      phases: list[PhaseResult]
      def to_dict(self) -> dict: ...

  def run_full_pipeline(config: Config) -> RunResult: ...
  ```

- [ ] **Step 1: Write the failing tests**

Create `brg_social_agent/tests/test_orchestrator.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd "/Users/charlesd.butler/Documents/Claude/Projects/Agentic OS/BRG Academy/BRG System/brg_social_agent"
python3 -m pytest tests/test_orchestrator.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'engines.orchestrator'`

- [ ] **Step 3: Implement `engines/orchestrator.py`**

```python
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone

from config import Config
from engines.distribution import run_distribution_pipeline
from engines.generation import run_generation_pipeline
from engines.intelligence import run_intelligence_pipeline
from engines.visual import run_visual_pipeline

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PhaseResult:
    name: str
    ids: list[str]
    error: str | None = None


@dataclass(frozen=True)
class RunResult:
    started_at: str
    finished_at: str
    phases: list[PhaseResult] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "phases": [
                {"name": p.name, "ids": p.ids, "error": p.error}
                for p in self.phases
            ],
        }


def run_full_pipeline(config: Config) -> RunResult:
    started_at = datetime.now(timezone.utc).isoformat()
    phases: list[PhaseResult] = []

    _PHASES = [
        ("intelligence", run_intelligence_pipeline),
        ("generation", run_generation_pipeline),
        ("visual", run_visual_pipeline),
        ("distribution", run_distribution_pipeline),
    ]

    for name, fn in _PHASES:
        try:
            ids = fn(config)
            phases.append(PhaseResult(name=name, ids=list(ids)))
        except Exception as exc:
            log.error("Phase %s failed: %s", name, exc)
            phases.append(PhaseResult(name=name, ids=[], error=str(exc)))

    finished_at = datetime.now(timezone.utc).isoformat()
    return RunResult(started_at=started_at, finished_at=finished_at, phases=phases)
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_orchestrator.py -v
```

Expected: `6 passed`

- [ ] **Step 5: Commit**

```bash
cd "/Users/charlesd.butler/Documents/Claude/Projects/Agentic OS/BRG Academy/BRG System"
git add brg_social_agent/engines/orchestrator.py brg_social_agent/tests/test_orchestrator.py
git commit -m "feat: Phase 5 orchestrator — run_full_pipeline with per-phase error isolation"
```

---

## Task 2: Post Archiver

**Files:**
- Create: `brg_social_agent/engines/archive.py`
- Test: `brg_social_agent/tests/test_archive.py`

**Interfaces:**
- Consumes:
  - `load_state(post_dir: Path) -> DistributionState` from `engines.distribution.state`
  - `config.enabled_platforms: list[str]`
  - `config.instagram_account_id: str`, `config.linkedin_person_id: str`
  - `config.queue_dir: str`, `config.posted_dir: str`
- Produces:
  ```python
  def _active_platforms(config: Config) -> list[str]: ...
  def archive_distributed_posts(config: Config) -> list[str]: ...
  ```
  Returns list of post_id strings that were moved to `posted/`.

**Archive rule:** A post directory is archived when `state.is_distributed_to(p)` is `True` for every platform in `_active_platforms(config)`. If there are no active platforms, nothing is archived.

- [ ] **Step 1: Write the failing tests**

Create `brg_social_agent/tests/test_archive.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_archive.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'engines.archive'`

- [ ] **Step 3: Implement `engines/archive.py`**

```python
from __future__ import annotations

import logging
import shutil
from pathlib import Path

from config import Config
from engines.distribution.state import load_state

log = logging.getLogger(__name__)


def _active_platforms(config: Config) -> list[str]:
    active = []
    if "instagram" in config.enabled_platforms and config.instagram_account_id:
        active.append("instagram")
    if "linkedin" in config.enabled_platforms and config.linkedin_person_id:
        active.append("linkedin")
    return active


def archive_distributed_posts(config: Config) -> list[str]:
    queue_dir = Path(config.queue_dir)
    posted_dir = Path(config.posted_dir)

    if not queue_dir.exists():
        return []

    active = _active_platforms(config)
    if not active:
        log.info("No active platforms — skipping archive step")
        return []

    posted_dir.mkdir(parents=True, exist_ok=True)
    archived_ids: list[str] = []

    for post_dir in sorted(queue_dir.iterdir()):
        if not post_dir.is_dir():
            continue

        try:
            state = load_state(post_dir)
        except Exception as exc:
            log.warning("Cannot read distribution state for %s: %s", post_dir.name, exc)
            continue

        if all(state.is_distributed_to(p) for p in active):
            dest = posted_dir / post_dir.name
            shutil.move(str(post_dir), str(dest))
            log.info("Archived %s → posted/", post_dir.name)
            archived_ids.append(post_dir.name)

    return archived_ids
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_archive.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Commit**

```bash
cd "/Users/charlesd.butler/Documents/Claude/Projects/Agentic OS/BRG Academy/BRG System"
git add brg_social_agent/engines/archive.py brg_social_agent/tests/test_archive.py
git commit -m "feat: Phase 5 post archiver — move fully-distributed posts to posted/"
```

---

## Task 3: Main Entrypoint + Run Logging

**Files:**
- Modify: `brg_social_agent/main.py`
- Create: `brg_social_agent/tests/test_main.py`

**Interfaces:**
- Consumes:
  - `run_full_pipeline(config: Config) -> RunResult` from `engines.orchestrator`
  - `archive_distributed_posts(config: Config) -> list[str]` from `engines.archive`
  - `run_intelligence_pipeline`, `run_generation_pipeline`, `run_visual_pipeline`, `run_distribution_pipeline` from their respective modules
- Produces:
  ```python
  def run_agent(config: Config, phase: str = "all") -> None: ...
  def main() -> None: ...
  ```
  `run_agent` is the testable core; `main()` parses args and calls `run_agent`.

**Run log format** (written to `config.logs_dir/run-YYYYMMDDHHMMSS.json` for `--phase all` only):
```json
{
  "started_at": "2026-06-19T12:00:00+00:00",
  "finished_at": "2026-06-19T12:01:30+00:00",
  "phases": [
    {"name": "intelligence", "ids": [...], "error": null},
    {"name": "generation",   "ids": [...], "error": null},
    {"name": "visual",       "ids": [...], "error": null},
    {"name": "distribution", "ids": [...], "error": null}
  ]
}
```

- [ ] **Step 1: Write the failing tests**

Create `brg_social_agent/tests/test_main.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python3 -m pytest tests/test_main.py -v 2>&1 | head -20
```

Expected: `ImportError: cannot import name 'run_agent' from 'main'`

- [ ] **Step 3: Implement the updated `main.py`**

Replace the entire file with:

```python
import argparse
import json
import logging
import re
from pathlib import Path

from config import load_config, Config
from engines.archive import archive_distributed_posts
from engines.distribution import run_distribution_pipeline
from engines.generation import run_generation_pipeline
from engines.intelligence import run_intelligence_pipeline
from engines.orchestrator import RunResult, run_full_pipeline
from engines.visual import run_visual_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _write_run_log(result: RunResult, config: Config) -> None:
    logs_dir = Path(config.logs_dir)
    logs_dir.mkdir(parents=True, exist_ok=True)
    ts = re.sub(r"[^0-9]", "", result.started_at[:19])
    path = logs_dir / f"run-{ts}.json"
    path.write_text(json.dumps(result.to_dict(), indent=2), encoding="utf-8")
    log.info("Run log written to %s", path)


def run_agent(config: Config, phase: str = "all") -> None:
    if phase == "all":
        result = run_full_pipeline(config)
        archived = archive_distributed_posts(config)
        _write_run_log(result, config)
        log.info(
            "Run complete — %s",
            {p.name: len(p.ids) for p in result.phases},
        )
        log.info("Archived %d post(s) to posted/", len(archived))

    elif phase == "intel":
        items = run_intelligence_pipeline(config)
        log.info("Intelligence complete — %d trends written", len(items))

    elif phase == "generate":
        ids = run_generation_pipeline(config)
        log.info("Generation complete — %d packages queued", len(ids))

    elif phase == "visual":
        ids = run_visual_pipeline(config)
        log.info("Visual complete — %d packages rendered", len(ids))

    elif phase == "distribute":
        ids = run_distribution_pipeline(config)
        archived = archive_distributed_posts(config)
        log.info(
            "Distribution complete — %d distributed, %d archived",
            len(ids),
            len(archived),
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="BRG Social Media Agent")
    parser.add_argument(
        "--phase",
        choices=["all", "intel", "generate", "visual", "distribute"],
        default="all",
        help="Run a single phase instead of the full pipeline (default: all)",
    )
    args = parser.parse_args()
    config = load_config()
    run_agent(config, args.phase)


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python3 -m pytest tests/test_main.py -v
```

Expected: `8 passed`

- [ ] **Step 5: Run the full test suite**

```bash
python3 -m pytest tests/ -q -m "not integration"
```

Expected: `180 passed` (158 existing + 6 orchestrator + 8 archive + 8 main), 0 failures.

- [ ] **Step 6: Commit**

```bash
cd "/Users/charlesd.butler/Documents/Claude/Projects/Agentic OS/BRG Academy/BRG System"
git add brg_social_agent/main.py brg_social_agent/tests/test_main.py
git commit -m "feat: Phase 5 main entrypoint — full pipeline orchestration with --phase flag and run logging"
```

---

## Self-Review

**Spec coverage:**
- Full pipeline run (all 4 phases in sequence): ✅ Task 1 `run_full_pipeline`
- Phase-level error isolation: ✅ Task 1 `try/except` per phase
- Post archiving (fully-distributed → posted/): ✅ Task 2 `archive_distributed_posts`
- Run log (JSON timestamped file): ✅ Task 3 `_write_run_log`
- CLI entrypoint (`python main.py`): ✅ Task 3 `main()`
- `--phase` flag for targeted runs: ✅ Task 3 `--phase all|intel|generate|visual|distribute`
- Archive called for `all` and `distribute` phases: ✅ Task 3 `run_agent`
- No new third-party deps: ✅ stdlib only (`shutil`, `re`, `json`, `argparse`, `dataclasses`)

**Placeholder scan:** Clean — all steps have concrete code.

**Type consistency:**
- `run_full_pipeline(config: Config) -> RunResult` — used in Task 3 import ✅
- `archive_distributed_posts(config: Config) -> list[str]` — used in Task 3 ✅
- `_write_run_log(result: RunResult, config: Config) -> None` — consistent across Task 3 ✅
- `PhaseResult.ids: list[str]` — Task 3 test does `len(p.ids)` ✅

Note: `run_intelligence_pipeline` returns `list[dict]` but all tests mock it, so the `list(ids)` call in `run_full_pipeline` handles the mixed return types correctly (it coerces to list).
