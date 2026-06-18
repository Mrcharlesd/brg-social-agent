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
        try:
            ts = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
        except (AttributeError, TypeError):
            ts = datetime.now(timezone.utc)
        items.append(ContentItem(
            title=getattr(entry, "title", "").strip(),
            body=getattr(entry, "summary", "")[:1000].strip(),
            url=getattr(entry, "link", ""),
            source=source.name,
            timestamp=ts,
        ))
    return items
