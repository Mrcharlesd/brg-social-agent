import json
import os
from unittest.mock import patch
from datetime import datetime, timezone

from config import Config
from engines.intelligence import run_intelligence_pipeline
from engines.intelligence.scraper import ContentItem


def _make_config(tmp_path) -> Config:
    config = Config.__new__(Config)
    config.anthropic_api_key = "test"
    config.reddit_client_id = "test"
    config.reddit_client_secret = "test"
    config.reddit_user_agent = "test"
    config.brand_primary_color = "#1A1A2E"
    config.brand_accent_color = "#E94560"
    config.brand_font_family = "Inter"
    config.logo_path = "assets/logo.svg"
    config.headshot_path = "assets/headshot.jpg"
    config.trends_file = str(tmp_path / "trends.json")
    config.seen_topics_file = str(tmp_path / "seen_topics.json")
    config.queue_dir = str(tmp_path / "queue")
    config.posted_dir = str(tmp_path / "posted")
    config.analytics_dir = str(tmp_path / "analytics")
    config.errors_dir = str(tmp_path / "errors")
    config.logs_dir = str(tmp_path / "logs")
    return config


def _make_items(n: int) -> list[ContentItem]:
    return [
        ContentItem(
            title=f"Leadership growth strategy {i}",
            body="mindset accountability coaching business",
            url=f"https://example.com/{i}",
            source="Test",
            timestamp=datetime.now(timezone.utc),
            likes=100 + i,
            comments=20,
        )
        for i in range(n)
    ]


def test_pipeline_writes_trends_json(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(5)):
        result = run_intelligence_pipeline(config)
    assert os.path.exists(config.trends_file)
    with open(config.trends_file) as f:
        data = json.load(f)
    assert "generated_at" in data
    assert "items" in data
    assert len(data["items"]) == 5


def test_pipeline_returns_list_of_dicts(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(3)):
        result = run_intelligence_pipeline(config)
    assert isinstance(result, list)
    assert all(isinstance(item, dict) for item in result)
    assert result[0]["title"].startswith("Leadership")


def test_pipeline_caps_output_at_20_items(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(30)):
        result = run_intelligence_pipeline(config)
    assert len(result) <= 20


def test_pipeline_marks_topics_seen(tmp_path):
    config = _make_config(tmp_path)
    with patch("engines.intelligence.scrape_all", return_value=_make_items(3)):
        run_intelligence_pipeline(config)
    assert os.path.exists(config.seen_topics_file)
    with open(config.seen_topics_file) as f:
        seen = json.load(f)
    assert len(seen) == 3
