from dataclasses import dataclass
from datetime import datetime, timezone
import feedparser

from .sources import Source


@dataclass
class ContentItem:
    title: str
    body: str
    url: str
    source: str
    timestamp: datetime
    likes: int = 0
    shares: int = 0
    comments: int = 0
    score: float = 0.0

    def __post_init__(self):
        if self.timestamp.tzinfo is None:
            raise ValueError("ContentItem.timestamp must be timezone-aware UTC")

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "body": self.body,
            "url": self.url,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "likes": self.likes,
            "shares": self.shares,
            "comments": self.comments,
            "score": self.score,
        }


def scrape_rss(source: Source) -> list[ContentItem]:
    """Scrape RSS feed and return up to 10 ContentItems."""
    feed = feedparser.parse(source.url)
    items = []
    for entry in feed.entries[:10]:
        ts_tuple = getattr(entry, "published_parsed", None)
        if ts_tuple:
            ts = datetime(*ts_tuple[:6], tzinfo=timezone.utc)
        else:
            ts = datetime.now(timezone.utc)
        items.append(ContentItem(
            title=getattr(entry, "title", "").strip(),
            body=getattr(entry, "summary", "")[:1000].strip(),
            url=getattr(entry, "link", ""),
            source=source.name,
            timestamp=ts,
        ))
    return items


def scrape_reddit(source: Source, reddit) -> list[ContentItem]:
    """Scrape Reddit subreddit and return ContentItems."""
    subreddit = reddit.subreddit(source.subreddit)
    items = []
    for post in subreddit.hot(limit=25):
        if post.stickied:
            continue
        items.append(ContentItem(
            title=post.title,
            body=post.selftext[:500].strip(),
            url=f"https://reddit.com{post.permalink}",
            source=source.name,
            timestamp=datetime.fromtimestamp(post.created_utc, tz=timezone.utc),
            likes=post.score,
            comments=post.num_comments,
        ))
    return items
