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
