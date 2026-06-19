import sys
from pathlib import Path
from typing import Optional

import pytest

# Add the project root to sys.path so test modules can import top-level packages.
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config


def make_test_config(tmp_path: Optional[Path] = None, **overrides) -> Config:
    """Create a Config instance suitable for tests, bypassing env-var validation."""
    config = Config.__new__(Config)
    config.anthropic_api_key = "test-key"
    config.reddit_client_id = "test-reddit-id"
    config.reddit_client_secret = "test-reddit-secret"
    config.reddit_user_agent = "BRGSocialAgent/test"
    config.brand_primary_color = "#1A1A2E"
    config.brand_accent_color = "#E94560"
    config.brand_font_family = "Inter"
    config.logo_path = "assets/brg_logo.svg"
    config.headshot_path = "assets/charles_headshot.jpg"
    config.instagram_account_id = ""
    config.instagram_access_token = ""
    config.linkedin_person_id = ""
    config.linkedin_access_token = ""
    config.image_base_url = ""
    config.enabled_platforms = ["instagram", "linkedin"]
    if tmp_path is not None:
        config.trends_file = str(tmp_path / "trends.json")
        config.seen_topics_file = str(tmp_path / "seen_topics.json")
        config.queue_dir = str(tmp_path / "queue")
        config.posted_dir = str(tmp_path / "posted")
        config.analytics_dir = str(tmp_path / "analytics")
        config.errors_dir = str(tmp_path / "errors")
        config.logs_dir = str(tmp_path / "logs")
    else:
        from pathlib import Path as _Path
        _root = _Path(__file__).parent.parent
        config.trends_file = str(_root / "data" / "trends.json")
        config.seen_topics_file = str(_root / "data" / "seen_topics.json")
        config.queue_dir = str(_root / "data" / "queue")
        config.posted_dir = str(_root / "data" / "posted")
        config.analytics_dir = str(_root / "data" / "analytics")
        config.errors_dir = str(_root / "data" / "errors")
        config.logs_dir = str(_root / "data" / "logs")
    for k, v in overrides.items():
        setattr(config, k, v)
    return config


@pytest.fixture
def sample_brand():
    """BrandContext with test values for use in visual tests."""
    from engines.visual.brand import BrandContext
    return BrandContext(
        primary_color="#1A1A2E",
        accent_color="#E94560",
        font_family="Inter",
        logo_svg="<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 40'><rect width='40' height='40' fill='#E94560'/></svg>",
        headshot_path=None,
    )


@pytest.fixture
def sample_content_package_dict():
    """Valid ContentPackage dict (serializable to JSON) for pipeline tests."""
    return {
        "post_id": "discipline-over-motivation-ab12cd34",
        "trend_title": "Discipline Over Motivation",
        "trend_url": "https://example.com/trend",
        "mood": "dark",
        "carousel": {
            "hook_slide": {
                "title": "Discipline Wins Every Time",
                "body": "Motivation is a feeling. Discipline is a decision.",
                "speaker_note": "Open strong — pause after second sentence.",
            },
            "content_slides": [
                {
                    "title": "Motivation Is Unreliable",
                    "body": "You will not feel motivated every day. Top performers don't wait for it.",
                    "speaker_note": "",
                },
                {
                    "title": "Discipline Builds Identity",
                    "body": "Every rep you complete when you don't want to is a vote for who you're becoming.",
                    "speaker_note": "",
                },
                {
                    "title": "Create Your Battle Rhythm",
                    "body": "A system of non-negotiable daily actions removes the need for motivation.",
                    "speaker_note": "",
                },
            ],
            "cta_slide": {
                "title": "Build Your Battle Rhythm",
                "body": "Follow Battle Rhythm Group for daily leadership frameworks that work.",
                "speaker_note": "",
            },
        },
        "post": {
            "body": (
                "Discipline is the real differentiator. High performers don't wake up motivated "
                "every day — they wake up committed. They have a battle rhythm: a set of "
                "non-negotiable actions that move them forward regardless of how they feel. "
                "Build yours."
            )
        },
        "script": {
            "hook": "What separates leaders who achieve from those who don't?",
            "body": (
                "It's not motivation. Motivation is a feeling that comes and goes. "
                "The leaders who win are the ones who show up when motivation is gone. "
                "That's discipline. And discipline is a skill you build deliberately."
            ),
            "cta": "Follow Battle Rhythm Group for daily leadership tools that actually work.",
            "duration_seconds": 45,
        },
        "quote": {
            "quote": "Discipline is the bridge between goals and accomplishment.",
            "attribution": "Charles Butler — Battle Rhythm Group",
        },
        "story": {
            "frames": [
                {"text": "Most leaders wait for motivation.", "purpose": "hook"},
                {"text": "The best leaders act with discipline — every day, no matter what.", "purpose": "insight"},
                {"text": "Build your battle rhythm. Follow BRG.", "purpose": "cta"},
            ]
        },
        "keywords": ["leadership", "discipline", "motivation", "battle rhythm"],
        "hashtags": [
            "#Leadership", "#BattleRhythm", "#BRG", "#ExecutiveCoach",
            "#Accountability", "#Discipline", "#Mindset", "#BusinessCoach",
            "#Entrepreneur", "#Faith",
        ],
        "location_signals": [
            "Chicago, IL",
            "Dallas, TX",
            "Houston, TX",
            "Atlanta, GA",
            "New York, NY",
        ],
        "generated_at": "2026-06-19T12:00:00+00:00",
    }
