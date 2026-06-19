import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv

_PROJECT_ROOT = Path(__file__).parent


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

    # Data paths (anchored to project root so cron jobs work regardless of CWD)
    trends_file: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "trends.json"))
    seen_topics_file: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "seen_topics.json"))
    queue_dir: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "queue"))
    posted_dir: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "posted"))
    analytics_dir: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "analytics"))
    errors_dir: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "errors"))
    logs_dir: str = field(default_factory=lambda: str(_PROJECT_ROOT / "data" / "logs"))

    # Distribution
    instagram_account_id: str = field(
        default_factory=lambda: os.getenv("INSTAGRAM_ACCOUNT_ID", "")
    )
    instagram_access_token: str = field(
        default_factory=lambda: os.getenv("INSTAGRAM_ACCESS_TOKEN", "")
    )
    linkedin_person_id: str = field(
        default_factory=lambda: os.getenv("LINKEDIN_PERSON_ID", "")
    )
    linkedin_access_token: str = field(
        default_factory=lambda: os.getenv("LINKEDIN_ACCESS_TOKEN", "")
    )
    image_base_url: str = field(
        default_factory=lambda: os.getenv("IMAGE_BASE_URL", "")
    )
    enabled_platforms: list[str] = field(
        default_factory=lambda: [
            p.strip()
            for p in os.getenv("ENABLED_PLATFORMS", "instagram,linkedin").split(",")
            if p.strip()
        ]
    )


def load_config() -> Config:
    load_dotenv()
    return Config()
