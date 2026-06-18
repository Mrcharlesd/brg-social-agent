from dataclasses import dataclass, field
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
