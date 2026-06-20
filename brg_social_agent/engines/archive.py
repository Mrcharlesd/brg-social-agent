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
