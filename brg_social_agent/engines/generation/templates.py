from jinja2 import Environment, BaseLoader

_env = Environment(loader=BaseLoader(), autoescape=False)

BRG_SYSTEM_PROMPT = """\
You are the content strategist for Battle Rhythm Group (BRG), a leadership \
development and business coaching brand founded by Charles Butler.

BRG Voice Rules:
- Direct and authoritative — no hedging, no passive voice
- Actionable — every piece must give the reader something to do or think differently about
- Forbidden words and phrases: game changer, level up, next level, crush it, hustle, grind, unleash, supercharge
- Faith-integrated where natural — not preachy, never forced
- Audience: leaders, executives, entrepreneurs, high-performers
- Charles' credentials: U.S. Army Veteran, CEO, Executive Coach, Author

Return valid JSON only. No markdown fences, no explanation, no preamble."""

_CONTENT_GENERATION_TEMPLATE = """\
Generate a complete BRG social media content package for this trending leadership topic.

TOPIC: {{ topic }}
CONTEXT: {{ context }}
SOURCE: {{ source }}

Return this exact JSON structure (no other text):
{
  "mood": "light",
  "carousel": {
    "hook_slide": {"title": "...", "body": "...", "speaker_note": "..."},
    "content_slides": [
      {"title": "...", "body": "...", "speaker_note": "..."}
    ],
    "cta_slide": {"title": "...", "body": "...", "speaker_note": "..."}
  },
  "post": {"body": "..."},
  "script": {"hook": "...", "body": "...", "cta": "...", "duration_seconds": 45},
  "quote": {"quote": "...", "attribution": "— Charles Butler, Battle Rhythm Group"},
  "story": {
    "frames": [
      {"text": "...", "purpose": "hook"},
      {"text": "...", "purpose": "insight"},
      {"text": "...", "purpose": "cta"}
    ]
  },
  "keywords": ["keyword1", "keyword2"],
  "hashtags": ["#Hashtag1", "#Hashtag2"]
}

HARD CONSTRAINTS:
- mood: "light" for motivational or growth topics; "dark" for serious, strategic, or crisis topics
- carousel.content_slides: exactly 5 slides
- carousel.cta_slide.body: must mention "BattleRhythmGroup.com" or "DM Charles"
- post.body: 150 to 300 words, platform-ready for LinkedIn, Facebook, and X
- script: total duration under 60 seconds when read at a normal pace; duration_seconds must be 20–60
- quote.quote: single sentence, max 25 words
- story.frames: exactly 3 frames with purposes "hook", "insight", "cta" in that order
- keywords: 5 to 10 relevant SEO keywords without hashtag symbols
- hashtags: 10 to 15 hashtags; must include #BattleRhythm and #Leadership"""

_QUALITY_CHECK_TEMPLATE = """\
Review this BRG social media content for brand voice compliance.

POST BODY:
{{ post_body }}

CAROUSEL HOOK SLIDE:
Title: {{ carousel_hook_title }}
Body: {{ carousel_hook_body }}

Flag FAIL if ANY of these appear:
- Generic clichés: "game changer", "level up", "next level", "crush it", "hustle", "grind", "unleash", "supercharge"
- Vague or abstract language with no actionable takeaway
- Corporate-speak or buzzword soup

Return JSON only: {"passes": true, "reason": "..."}"""


def render_content_prompt(topic: str, context: str, source: str) -> str:
    """Render the content generation user prompt with trend variables."""
    return _env.from_string(_CONTENT_GENERATION_TEMPLATE).render(
        topic=topic, context=context, source=source
    )


def render_quality_prompt(
    post_body: str, carousel_hook_title: str, carousel_hook_body: str
) -> str:
    """Render the voice quality check prompt."""
    return _env.from_string(_QUALITY_CHECK_TEMPLATE).render(
        post_body=post_body,
        carousel_hook_title=carousel_hook_title,
        carousel_hook_body=carousel_hook_body,
    )
