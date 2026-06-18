import pytest
from datetime import timezone
from unittest.mock import patch, MagicMock
from engines.intelligence.scraper import ContentItem, scrape_rss
from engines.intelligence.sources import Source, SourceType


def _mock_rss_feed():
    entry = MagicMock()
    entry.title = "5 Leadership Lessons for Entrepreneurs"
    entry.summary = "How to build a high-performing team through accountability."
    entry.link = "https://forbes.com/article/123"
    entry.published_parsed = (2026, 6, 18, 10, 0, 0, 0, 169, 0)
    feed = MagicMock()
    feed.entries = [entry]
    return feed


def test_scrape_rss_returns_content_items():
    source = Source(name="Forbes Leadership", type=SourceType.RSS,
                    url="https://forbes.com/leadership/feed/")
    with patch("engines.intelligence.scraper.feedparser.parse",
               return_value=_mock_rss_feed()):
        items = scrape_rss(source)
    assert len(items) == 1
    assert isinstance(items[0], ContentItem)
    assert items[0].title == "5 Leadership Lessons for Entrepreneurs"
    assert items[0].source == "Forbes Leadership"
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_rss_handles_missing_published_date():
    entry = MagicMock()
    entry.title = "Article without date"
    entry.summary = "Summary text"
    entry.link = "https://example.com/article"
    entry.published_parsed = None
    feed = MagicMock()
    feed.entries = [entry]
    source = Source(name="Test RSS", type=SourceType.RSS, url="https://test.com/feed")
    with patch("engines.intelligence.scraper.feedparser.parse", return_value=feed):
        items = scrape_rss(source)
    assert len(items) == 1
    assert items[0].timestamp is not None
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_rss_limits_to_ten_entries():
    entries = []
    for i in range(15):
        e = MagicMock()
        e.title = f"Article {i}"
        e.summary = "Summary"
        e.link = f"https://example.com/{i}"
        e.published_parsed = (2026, 6, 18, 10, 0, 0, 0, 169, 0)
        entries.append(e)
    feed = MagicMock()
    feed.entries = entries
    source = Source(name="Test", type=SourceType.RSS, url="https://test.com/feed")
    with patch("engines.intelligence.scraper.feedparser.parse", return_value=feed):
        items = scrape_rss(source)
    assert len(items) == 10
