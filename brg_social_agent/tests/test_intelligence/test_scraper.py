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


def _mock_reddit_post(title="Leadership mindset shift", score=450,
                      num_comments=87, selftext="Build your team's accountability."):
    post = MagicMock()
    post.title = title
    post.selftext = selftext
    post.permalink = "/r/leadership/comments/abc123/title"
    post.created_utc = 1750240800.0  # 2026-06-18 10:00:00 UTC
    post.score = score
    post.num_comments = num_comments
    post.stickied = False
    return post


def test_scrape_reddit_returns_content_items():
    import praw
    source = Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership")
    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.hot.return_value = [_mock_reddit_post()]
    with patch("engines.intelligence.scraper.praw.Reddit", return_value=mock_reddit):
        from engines.intelligence.scraper import scrape_reddit
        items = scrape_reddit(source, mock_reddit)
    assert len(items) == 1
    assert items[0].title == "Leadership mindset shift"
    assert items[0].likes == 450
    assert items[0].comments == 87
    assert items[0].timestamp.tzinfo == timezone.utc


def test_scrape_reddit_skips_stickied_posts():
    import praw
    stickied = _mock_reddit_post(title="Stickied announcement")
    stickied.stickied = True
    normal = _mock_reddit_post(title="Normal post")
    source = Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership")
    mock_reddit = MagicMock()
    mock_reddit.subreddit.return_value.hot.return_value = [stickied, normal]
    with patch("engines.intelligence.scraper.praw.Reddit", return_value=mock_reddit):
        from engines.intelligence.scraper import scrape_reddit
        items = scrape_reddit(source, mock_reddit)
    assert len(items) == 1
    assert items[0].title == "Normal post"
