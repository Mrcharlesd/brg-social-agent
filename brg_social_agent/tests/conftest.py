import sys
from pathlib import Path
from typing import Optional

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
