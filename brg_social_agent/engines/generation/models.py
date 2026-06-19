import hashlib
import re
from datetime import datetime, timezone
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


def make_post_id(title: str) -> str:
    """Generate a deterministic, filesystem-safe post ID from a trend title."""
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]
    digest = hashlib.md5(title.encode()).hexdigest()[:8]
    return f"{slug}-{digest}"


class CarouselSlide(BaseModel):
    model_config = ConfigDict(frozen=True)
    title: str
    body: str
    speaker_note: str


class CarouselContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    hook_slide: CarouselSlide
    content_slides: list[CarouselSlide] = Field(min_length=3, max_length=8)
    cta_slide: CarouselSlide


class PostContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    body: str = Field(min_length=1)


class ScriptContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    hook: str
    body: str
    cta: str
    duration_seconds: int = Field(ge=20, le=60)


class QuoteContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    quote: str
    attribution: str


class StoryFrame(BaseModel):
    model_config = ConfigDict(frozen=True)
    text: str
    purpose: Literal["hook", "insight", "cta"]


class StoryContent(BaseModel):
    model_config = ConfigDict(frozen=True)
    frames: list[StoryFrame] = Field(min_length=3, max_length=3)


class ContentPackage(BaseModel):
    model_config = ConfigDict(frozen=True)
    post_id: str
    trend_title: str
    trend_url: str
    mood: Literal["light", "dark"]
    carousel: CarouselContent
    post: PostContent
    script: ScriptContent
    quote: QuoteContent
    story: StoryContent
    keywords: list[str] = Field(default_factory=list)
    hashtags: list[str] = Field(default_factory=list)
    location_signals: list[str] = Field(default_factory=list)
    generated_at: datetime
