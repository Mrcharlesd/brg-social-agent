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
