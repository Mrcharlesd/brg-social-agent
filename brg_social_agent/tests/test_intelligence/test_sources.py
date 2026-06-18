from datetime import datetime, timezone
import pytest
from engines.intelligence.scraper import ContentItem
from engines.intelligence.sources import SOURCES, SourceType


def test_content_item_to_dict_contains_required_keys():
    item = ContentItem(
        title="Lead with purpose",
        body="Discipline beats motivation every time.",
        url="https://example.com/article",
        source="Forbes Leadership",
        timestamp=datetime(2026, 6, 18, 10, 0, 0, tzinfo=timezone.utc),
        likes=120,
        shares=30,
        comments=15,
        score=0.75,
    )
    d = item.to_dict()
    assert d["title"] == "Lead with purpose"
    assert d["source"] == "Forbes Leadership"
    assert d["timestamp"] == "2026-06-18T10:00:00+00:00"
    assert d["score"] == 0.75


def test_content_item_raises_on_naive_timestamp():
    with pytest.raises(ValueError, match="timezone-aware"):
        ContentItem(
            title="Test",
            body="Body",
            url="https://example.com",
            source="Test",
            timestamp=datetime(2026, 6, 18, 10, 0, 0),  # naive — no tzinfo
        )


def test_sources_registry_contains_rss_sources():
    rss = [s for s in SOURCES if s.type == SourceType.RSS]
    assert len(rss) >= 3
    for s in rss:
        assert s.url is not None and s.url.startswith("http")


def test_sources_registry_contains_reddit_sources():
    reddit = [s for s in SOURCES if s.type == SourceType.REDDIT]
    assert len(reddit) >= 3
    for s in reddit:
        assert s.subreddit is not None


def test_all_sources_have_names():
    for s in SOURCES:
        assert s.name and len(s.name) > 0
