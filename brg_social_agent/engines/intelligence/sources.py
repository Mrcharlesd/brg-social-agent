from dataclasses import dataclass
from enum import Enum
from typing import Optional


class SourceType(str, Enum):
    RSS = "rss"
    REDDIT = "reddit"
    YOUTUBE = "youtube"
    TRENDS = "trends"


@dataclass
class Source:
    name: str
    type: SourceType
    url: Optional[str] = None
    subreddit: Optional[str] = None
    youtube_channel_id: Optional[str] = None


SOURCES: list[Source] = [
    # News / RSS
    Source(name="Forbes Leadership", type=SourceType.RSS,
           url="https://www.forbes.com/leadership/feed/"),
    Source(name="Harvard Business Review", type=SourceType.RSS,
           url="https://hbr.org/rss/topic/leadership"),
    Source(name="Inc Magazine", type=SourceType.RSS,
           url="https://www.inc.com/rss.html"),
    # Reddit
    Source(name="Reddit Entrepreneur", type=SourceType.REDDIT, subreddit="Entrepreneur"),
    Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership"),
    Source(name="Reddit Self Improvement", type=SourceType.REDDIT, subreddit="selfimprovement"),
    # Google Trends
    Source(name="Google Trends", type=SourceType.TRENDS),
]
