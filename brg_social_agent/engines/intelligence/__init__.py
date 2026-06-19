import json
import os
from datetime import datetime, timezone

from config import Config
from .scraper import scrape_all
from .ranker import rank, mark_seen, load_seen_topics


def run_intelligence_pipeline(config: Config) -> list[dict]:
    """Scrape all sources, rank, write top 20 to trends.json. Returns items as list of dicts."""
    raw_items = scrape_all(config)
    top_items = rank(raw_items, config.seen_topics_file)

    os.makedirs(os.path.dirname(config.trends_file), exist_ok=True)
    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "items": [item.to_dict() for item in top_items],
    }
    with open(config.trends_file, "w") as f:
        json.dump(output, f, indent=2)

    seen = load_seen_topics(config.seen_topics_file)
    for item in top_items:
        mark_seen(item.title, seen, config.seen_topics_file)

    return output["items"]
