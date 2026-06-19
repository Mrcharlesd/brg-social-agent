import json
import logging
from datetime import datetime, timezone

import anthropic

from config import Config
from .models import (
    CarouselContent,
    CarouselSlide,
    ContentPackage,
    PostContent,
    QuoteContent,
    ScriptContent,
    StoryContent,
    StoryFrame,
    make_post_id,
)
from .templates import BRG_SYSTEM_PROMPT, render_content_prompt

log = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 4096


def generate_content_package(item: dict, config: Config) -> ContentPackage:
    """
    Call Claude to generate all five BRG content formats for a single trend item.
    Returns a validated, frozen ContentPackage.
    Raises ValueError on invalid JSON or Pydantic schema mismatch.
    """
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    prompt = render_content_prompt(
        topic=item["title"],
        context=item.get("body", ""),
        source=item.get("source", ""),
    )
    log.info("Generating content for: %s", item["title"])

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=BRG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = message.content[0].text.strip()
    try:
        data = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Claude returned non-JSON for '{item['title']}': {exc}"
        ) from exc

    return _build_package(data, item)


def _build_package(data: dict, item: dict) -> ContentPackage:
    """Parse Claude's JSON response dict into a validated ContentPackage."""
    carousel_raw = data["carousel"]
    return ContentPackage(
        post_id=make_post_id(item["title"]),
        trend_title=item["title"],
        trend_url=item.get("url", ""),
        mood=data["mood"],
        carousel=CarouselContent(
            hook_slide=CarouselSlide(**carousel_raw["hook_slide"]),
            content_slides=[
                CarouselSlide(**s) for s in carousel_raw["content_slides"]
            ],
            cta_slide=CarouselSlide(**carousel_raw["cta_slide"]),
        ),
        post=PostContent(body=data["post"]["body"]),
        script=ScriptContent(**data["script"]),
        quote=QuoteContent(**data["quote"]),
        story=StoryContent(
            frames=[StoryFrame(**f) for f in data["story"]["frames"]]
        ),
        keywords=data.get("keywords", []),
        hashtags=data.get("hashtags", []),
        location_signals=[],
        generated_at=datetime.now(timezone.utc),
    )
