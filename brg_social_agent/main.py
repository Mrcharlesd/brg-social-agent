import logging
from config import load_config
from engines.intelligence import run_intelligence_pipeline

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def main():
    config = load_config()
    log.info("Starting BRG Social Media Agent — Phase 1: Content Intelligence")
    items = run_intelligence_pipeline(config)
    log.info(f"Pipeline complete. {len(items)} trending topics written to {config.trends_file}")


if __name__ == "__main__":
    main()
