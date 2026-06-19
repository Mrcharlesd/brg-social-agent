import json
import os
import pytest
from datetime import datetime, timedelta, timezone
from engines.intelligence.scraper import ContentItem
from engines.intelligence.ranker import (
    recency_score,
    engagement_score,
    relevance_score,
    rank,
    mark_seen,
    load_seen_topics,
    is_duplicate,
)


def _item(title="Leadership and coaching strategy",
          body="Mindset growth discipline accountability",
          hours_old=1, likes=100, shares=10, comments=20) -> ContentItem:
    return ContentItem(
        title=title, body=body,
        url="https://example.com",
        source="Test",
        timestamp=datetime.now(timezone.utc) - timedelta(hours=hours_old),
        likes=likes, shares=shares, comments=comments,
    )


# --- Scoring unit tests ---

def test_recency_score_fresh_item_near_one():
    score = recency_score(datetime.now(timezone.utc))
    assert score > 0.99


def test_recency_score_day_old_is_half():
    ts = datetime.now(timezone.utc) - timedelta(hours=24)
    score = recency_score(ts)
    assert 0.45 < score < 0.55


def test_recency_score_very_old_item_near_zero():
    ts = datetime.now(timezone.utc) - timedelta(hours=168)
    score = recency_score(ts)
    assert score < 0.05


def test_engagement_score_caps_at_one():
    score = engagement_score(likes=10000, shares=5000, comments=2000)
    assert score == 1.0


def test_engagement_score_zero_for_no_engagement():
    assert engagement_score(0, 0, 0) == 0.0


def test_relevance_score_on_topic_above_half():
    score = relevance_score(
        "Leadership coaching for entrepreneurs",
        "business mindset growth strategy"
    )
    assert score > 0.5


def test_relevance_score_off_topic_is_zero():
    score = relevance_score("Best pizza recipes", "cooking tips for beginners")
    assert score == 0.0


# --- Duplicate suppression ---

def test_is_duplicate_returns_false_when_not_seen(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = load_seen_topics(seen_file)
    assert not is_duplicate("Brand new topic", seen)


def test_is_duplicate_returns_true_within_14_days(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership topic", seen, seen_file)
    seen = load_seen_topics(seen_file)
    assert is_duplicate("Leadership topic", seen)


def test_is_duplicate_case_insensitive(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership Topic", seen, seen_file)
    seen = load_seen_topics(seen_file)
    assert is_duplicate("leadership topic", seen)


def test_is_duplicate_returns_false_after_14_days(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Old topic", seen, seen_file)
    # back-date entry beyond the 14-day window
    seen["old topic"] = (datetime.now(timezone.utc) - timedelta(days=15)).isoformat()
    with open(seen_file, "w") as f:
        json.dump(seen, f)
    seen = load_seen_topics(seen_file)
    assert not is_duplicate("Old topic", seen)


# --- rank() integration ---

def test_rank_returns_sorted_highest_first(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    low = _item(title="pizza recipes cooking", body="food tips", hours_old=72, likes=0)
    high = _item(title="leadership coaching business", body="mindset growth strategy",
                 hours_old=1, likes=500, comments=100)
    ranked = rank([low, high], seen_file)
    assert ranked[0].title == "leadership coaching business"


def test_rank_limits_to_top_n(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    items = [_item(title=f"Leadership article {i}") for i in range(30)]
    ranked = rank(items, seen_file, top_n=20)
    assert len(ranked) == 20


def test_rank_excludes_seen_duplicates(tmp_path):
    seen_file = str(tmp_path / "seen.json")
    seen = {}
    mark_seen("Leadership topic", seen, seen_file)
    items = [_item(title="Leadership topic"), _item(title="New business growth strategy")]
    ranked = rank(items, seen_file)
    titles = [r.title for r in ranked]
    assert "Leadership topic" not in titles
    assert "New business growth strategy" in titles
