import json
from unittest.mock import patch, MagicMock

from engines.generation.models import (
    CarouselContent, CarouselSlide, ContentPackage,
    PostContent, QuoteContent, ScriptContent,
    StoryContent, StoryFrame,
)
from config import Config


def _make_config() -> Config:
    config = Config.__new__(Config)
    config.anthropic_api_key = "test-key"
    return config


def _slide() -> CarouselSlide:
    return CarouselSlide(title="The Truth About Leadership", body="Most leaders talk.", speaker_note="N")


def _make_package() -> ContentPackage:
    return ContentPackage(
        post_id="test-id",
        trend_title="Test",
        trend_url="https://example.com",
        mood="dark",
        carousel=CarouselContent(
            hook_slide=_slide(),
            content_slides=[_slide(), _slide(), _slide()],
            cta_slide=_slide(),
        ),
        post=PostContent(body="Leadership is a discipline. " * 10),
        script=ScriptContent(hook="H", body="B", cta="C", duration_seconds=30),
        quote=QuoteContent(quote="Quote.", attribution="— CB"),
        story=StoryContent(
            frames=[
                StoryFrame(text="a", purpose="hook"),
                StoryFrame(text="b", purpose="insight"),
                StoryFrame(text="c", purpose="cta"),
            ]
        ),
        generated_at="2026-01-01T00:00:00+00:00",
    )


def _mock_quality_client(passes: bool, reason: str = "ok") -> MagicMock:
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps({"passes": passes, "reason": reason}))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_voice_check_returns_true_when_passes():
    from engines.generation.quality import voice_check
    with patch("engines.generation.quality.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _mock_quality_client(True)
        assert voice_check(_make_package(), _make_config()) is True


def test_voice_check_returns_false_when_fails():
    from engines.generation.quality import voice_check
    with patch("engines.generation.quality.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _mock_quality_client(False, "uses clichés")
        assert voice_check(_make_package(), _make_config()) is False


def test_voice_check_returns_false_on_non_json_response():
    from engines.generation.quality import voice_check
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="yes it passes")]
    )
    with patch("engines.generation.quality.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = mock_client
        assert voice_check(_make_package(), _make_config()) is False


def test_voice_check_uses_correct_model_and_max_tokens():
    from engines.generation.quality import voice_check
    with patch("engines.generation.quality.anthropic.Anthropic") as mock_cls:
        mock_client = _mock_quality_client(True)
        mock_cls.return_value = mock_client
        voice_check(_make_package(), _make_config())
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == 256


def test_voice_check_passes_post_body_in_prompt():
    from engines.generation.quality import voice_check
    pkg = _make_package()
    with patch("engines.generation.quality.anthropic.Anthropic") as mock_cls:
        mock_client = _mock_quality_client(True)
        mock_cls.return_value = mock_client
        voice_check(pkg, _make_config())
    call_msgs = mock_client.messages.create.call_args.kwargs["messages"]
    assert pkg.post.body in call_msgs[0]["content"]
