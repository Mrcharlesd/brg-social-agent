import pytest
from unittest.mock import patch
from config import load_config


def test_load_config_raises_on_missing_anthropic_key(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    with patch("config.load_dotenv"):
        with pytest.raises(EnvironmentError, match="ANTHROPIC_API_KEY"):
            load_config()


def test_load_config_reddit_optional(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    config = load_config()
    assert config.reddit_client_id == ""
    assert config.reddit_client_secret == ""


def test_load_config_success(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.delenv("REDDIT_CLIENT_ID", raising=False)
    monkeypatch.delenv("REDDIT_CLIENT_SECRET", raising=False)
    config = load_config()
    assert config.anthropic_api_key == "test-key"
    assert config.trends_file.endswith("data/trends.json")
    assert config.brand_primary_color == "#1A1A2E"
