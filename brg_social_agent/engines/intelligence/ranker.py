import json
import logging
import math
import os
from dataclasses import replace
from datetime import datetime, timedelta, timezone

from .scraper import ContentItem

log = logging.getLogger(__name__)

BRG_KEYWORDS = [
    "leadership", "coaching", "business", "entrepreneur", "productivity",
    "team", "culture", "mindset", "growth", "strategy", "faith", "purpose",
    "execution", "accountability", "performance", "vision", "mission",
    "discipline", "resilience", "transformation",
]


def recency_score(timestamp: datetime, half_life_hours: float = 24.0) -> float:
    age_hours = (datetime.now(timezone.utc) - timestamp).total_seconds() / 3600
    return math.exp(-age_hours / half_life_hours * math.log(2))


def engagement_score(likes: int, shares: int, comments: int) -> float:
    total = likes + (shares * 2) + (comments * 1.5)
    return min(total / 1000.0, 1.0)


def relevance_score(title: str, body: str) -> float:
    text = f"{title} {body}".lower()
    matches = sum(1 for kw in BRG_KEYWORDS if kw in text)
    return min(matches / 5.0, 1.0)


def load_seen_topics(seen_file: str) -> dict[str, str]:
    if not os.path.exists(seen_file):
        return {}
    try:
        with open(seen_file) as f:
            return json.load(f)
    except json.JSONDecodeError:
        log.warning("seen_topics.json is corrupt — resetting duplicate history")
        return {}


def is_duplicate(title: str, seen: dict[str, str], days: int = 14) -> bool:
    key = title.lower()
    if key not in seen:
        return False
    cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days)
    return datetime.fromisoformat(seen[key]) > cutoff_dt


def mark_seen(title: str, seen: dict[str, str], seen_file: str) -> None:
    seen[title.lower()] = datetime.now(timezone.utc).isoformat()
    os.makedirs(os.path.dirname(seen_file) or ".", exist_ok=True)
    with open(seen_file, "w") as f:
        json.dump(seen, f, indent=2)


def rank(
    items: list[ContentItem],
    seen_file: str,
    top_n: int = 20,
) -> list[ContentItem]:
    seen = load_seen_topics(seen_file)
    filtered = [item for item in items if not is_duplicate(item.title, seen)]
    scored = []
    for item in filtered:
        r = recency_score(item.timestamp)
        e = engagement_score(item.likes, item.shares, item.comments)
        v = relevance_score(item.title, item.body)
        scored.append(replace(item, score=round((r * 0.3) + (e * 0.3) + (v * 0.4), 4)))
    return sorted(scored, key=lambda x: x.score, reverse=True)[:top_n]
