import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


def _require(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(f"Required environment variable {key!r} is not set")
    return val


@dataclass
class Config:
    # Credentials
    anthropic_api_key: str = field(default_factory=lambda: _require("ANTHROPIC_API_KEY"))
    reddit_client_id: str = field(default_factory=lambda: _require("REDDIT_CLIENT_ID"))
    reddit_client_secret: str = field(default_factory=lambda: _require("REDDIT_CLIENT_SECRET"))
    reddit_user_agent: str = "BRGSocialAgent/1.0"

    # Brand
    brand_primary_color: str = field(default_factory=lambda: os.getenv("BRAND_PRIMARY_COLOR", "#1A1A2E"))
    brand_accent_color: str = field(default_factory=lambda: os.getenv("BRAND_ACCENT_COLOR", "#E94560"))
    brand_font_family: str = field(default_factory=lambda: os.getenv("BRAND_FONT_FAMILY", "Inter"))
    logo_path: str = field(default_factory=lambda: os.getenv("LOGO_PATH", "assets/brg_logo.svg"))
    headshot_path: str = field(default_factory=lambda: os.getenv("HEADSHOT_PATH", "assets/charles_headshot.jpg"))

    # Data paths
    trends_file: str = "data/trends.json"
    seen_topics_file: str = "data/seen_topics.json"
    queue_dir: str = "data/queue"
    posted_dir: str = "data/posted"
    analytics_dir: str = "data/analytics"
    errors_dir: str = "data/errors"
    logs_dir: str = "data/logs"


def load_config() -> Config:
    return Config()
