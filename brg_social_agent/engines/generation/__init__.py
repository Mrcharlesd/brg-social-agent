import json
import logging
from pathlib import Path

from config import Config
from .quality import voice_check
from .seo import add_location_signals, validate_hashtags
from .writer import generate_content_package

log = logging.getLogger(__name__)


def run_generation_pipeline(config: Config) -> list[str]:
    """
    Read trends.json, generate BRG content for each trend, write content.json per item.
    Returns the list of post_ids that were successfully written.
    Skips items that raise exceptions or fail voice quality check twice.
    """
    trends_path = Path(config.trends_file)
    if not trends_path.exists():
        log.warning("trends.json not found at %s — nothing to generate", trends_path)
        return []

    with open(trends_path, encoding="utf-8") as f:
        trends = json.load(f)

    post_ids: list[str] = []

    for item in trends.get("items", []):
        title = item.get("title", "unknown")

        try:
            package = generate_content_package(item, config)
        except Exception as exc:
            log.warning("Generation failed for %r: %s", title, exc)
            continue

        # First quality check
        try:
            passes = voice_check(package, config)
        except Exception as exc:
            log.warning("Voice check error for %r: %s — skipping", title, exc)
            continue

        if not passes:
            log.info("Voice check failed — retrying generation for: %s", title)
            try:
                package = generate_content_package(item, config)
            except Exception as exc:
                log.warning("Retry generation failed for %r: %s", title, exc)
                continue

            # Second quality check
            try:
                passes = voice_check(package, config)
            except Exception as exc:
                log.warning("Retry voice check error for %r: %s — skipping", title, exc)
                continue

            if not passes:
                log.warning("Skipping %r — failed voice check twice", title)
                continue

        package = validate_hashtags(package)
        package = add_location_signals(package)

        out_dir = Path(config.queue_dir) / package.post_id
        out_dir.mkdir(parents=True, exist_ok=True)
        content_path = out_dir / "content.json"
        with open(content_path, "w", encoding="utf-8") as f:
            f.write(package.model_dump_json(indent=2))

        log.info("Wrote %s", content_path)
        post_ids.append(package.post_id)

    return post_ids
