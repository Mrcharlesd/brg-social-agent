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
    Source(name="MIT Sloan Management Review", type=SourceType.RSS,
           url="https://sloanreview.mit.edu/rss/"),
    Source(name="Fast Company Leadership", type=SourceType.RSS,
           url="https://www.fastcompany.com/leadership/rss"),
    Source(name="Entrepreneur", type=SourceType.RSS,
           url="https://www.entrepreneur.com/latest.rss"),
    # Reddit (optional — only active when REDDIT_CLIENT_ID is set)
    Source(name="Reddit Entrepreneur", type=SourceType.REDDIT, subreddit="Entrepreneur"),
    Source(name="Reddit Leadership", type=SourceType.REDDIT, subreddit="leadership"),
    Source(name="Reddit Self Improvement", type=SourceType.REDDIT, subreddit="selfimprovement"),
    # Google Trends
    Source(name="Google Trends", type=SourceType.TRENDS),
]
