from dataclasses import dataclass
from datetime import datetime, timezone


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
