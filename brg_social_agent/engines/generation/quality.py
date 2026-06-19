import json
import logging

import anthropic

from config import Config
from .models import ContentPackage
from .templates import BRG_SYSTEM_PROMPT, render_quality_prompt

log = logging.getLogger(__name__)

_MODEL = "claude-sonnet-4-6"
_MAX_TOKENS = 256


def voice_check(package: ContentPackage, config: Config) -> bool:
    """
    Ask Claude to evaluate BRG voice compliance for this content package.
    Returns True if the content passes, False on failure or non-JSON response.
    Retry logic lives in the pipeline — this function makes exactly one API call.
    """
    client = anthropic.Anthropic(api_key=config.anthropic_api_key)
    prompt = render_quality_prompt(
        post_body=package.post.body,
        carousel_hook_title=package.carousel.hook_slide.title,
        carousel_hook_body=package.carousel.hook_slide.body,
    )

    message = client.messages.create(
        model=_MODEL,
        max_tokens=_MAX_TOKENS,
        system=BRG_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError:
        log.warning("voice_check: Claude returned non-JSON — treating as fail: %.200s", raw)
        return False

    passes = bool(result.get("passes", False))
    if not passes:
        log.warning("voice_check: FAIL — %s", result.get("reason", "no reason given"))
    return passes
