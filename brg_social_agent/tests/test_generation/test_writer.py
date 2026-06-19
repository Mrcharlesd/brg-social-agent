import json
import pytest
from unittest.mock import patch, MagicMock

from engines.generation.models import ContentPackage, make_post_id
from config import Config

# A minimal valid JSON response that Claude would return
_SAMPLE_RESPONSE = {
    "mood": "dark",
    "carousel": {
        "hook_slide": {
            "title": "The Truth About Leadership",
            "body": "Most leaders talk. Few execute.",
            "speaker_note": "Pause after first sentence.",
        },
        "content_slides": [
            {
                "title": f"Principle {i}",
                "body": f"Leaders who execute principle {i} outperform their peers.",
                "speaker_note": f"Hold on slide {i} for emphasis.",
            }
            for i in range(1, 6)
        ],
        "cta_slide": {
            "title": "Your Next Move",
            "body": "Start your battle rhythm at BattleRhythmGroup.com",
            "speaker_note": "End with energy.",
        },
    },
    "post": {
        "body": (
            "Leadership is not a title. It is a discipline. "
            "Every leader I have coached who struggled did so because they confused "
            "position with performance. They managed activity instead of driving outcomes. "
            "The best leaders I know share one trait: they execute relentlessly. "
            "They do not wait for perfect conditions. They build battle rhythm. "
            "They hold their teams accountable because they hold themselves accountable first. "
            "If you want to lead at a higher level, start with your own execution. "
            "Your team mirrors your standard. Raise it."
        )
    },
    "script": {
        "hook": "Most leaders never figure out why their team won't execute.",
        "body": (
            "Here is the truth — your team executes at the level you model. "
            "If you are inconsistent, they will be inconsistent. "
            "If you avoid hard conversations, they will too. "
            "Execution is not a team problem. It is a leadership problem."
        ),
        "cta": "Follow for more on building a battle rhythm that actually works.",
        "duration_seconds": 45,
    },
    "quote": {
        "quote": "Execution is not a strategy — it is the standard.",
        "attribution": "— Charles Butler, Battle Rhythm Group",
    },
    "story": {
        "frames": [
            {"text": "Are you leading or just managing?", "purpose": "hook"},
            {"text": "Leaders execute. Managers plan.", "purpose": "insight"},
            {"text": "DM Charles to build your battle rhythm.", "purpose": "cta"},
        ]
    },
    "keywords": ["leadership", "execution", "accountability", "business coaching", "battle rhythm"],
    "hashtags": [
        "#Leadership", "#BattleRhythm", "#BRG", "#ExecutiveCoach",
        "#Accountability", "#Discipline", "#Mindset", "#BusinessCoach",
        "#Entrepreneur", "#Faith", "#ExecutivePresence", "#HighPerformance",
    ],
}

_SAMPLE_ITEM = {
    "title": "Leadership Under Pressure",
    "body": "How top executives stay calm and decisive in a crisis.",
    "source": "Harvard Business Review",
    "url": "https://hbr.org/leadership-under-pressure",
    "timestamp": "2026-06-18T12:00:00+00:00",
    "likes": 150,
    "shares": 40,
    "comments": 25,
    "score": 0.82,
}


def _make_config() -> Config:
    config = Config.__new__(Config)
    config.anthropic_api_key = "test-key"
    return config


def _mock_client(response_dict: dict) -> MagicMock:
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=json.dumps(response_dict))]
    mock_client = MagicMock()
    mock_client.messages.create.return_value = mock_msg
    return mock_client


def test_generate_content_package_returns_content_package():
    from engines.generation.writer import generate_content_package
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _mock_client(_SAMPLE_RESPONSE)
        result = generate_content_package(_SAMPLE_ITEM, _make_config())
    assert isinstance(result, ContentPackage)


def test_generate_content_package_post_id_matches_title():
    from engines.generation.writer import generate_content_package
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _mock_client(_SAMPLE_RESPONSE)
        result = generate_content_package(_SAMPLE_ITEM, _make_config())
    assert result.post_id == make_post_id(_SAMPLE_ITEM["title"])


def test_generate_content_package_uses_correct_model_and_tokens():
    from engines.generation.writer import generate_content_package
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_client = _mock_client(_SAMPLE_RESPONSE)
        mock_cls.return_value = mock_client
        generate_content_package(_SAMPLE_ITEM, _make_config())
    kwargs = mock_client.messages.create.call_args.kwargs
    assert kwargs["model"] == "claude-sonnet-4-6"
    assert kwargs["max_tokens"] == 4096


def test_generate_content_package_raises_on_non_json():
    from engines.generation.writer import generate_content_package
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Here is your content: sorry, not JSON.")]
    )
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = mock_client
        with pytest.raises(ValueError, match="non-JSON"):
            generate_content_package(_SAMPLE_ITEM, _make_config())


def test_generate_content_package_passes_topic_to_prompt():
    from engines.generation.writer import generate_content_package
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_client = _mock_client(_SAMPLE_RESPONSE)
        mock_cls.return_value = mock_client
        generate_content_package(_SAMPLE_ITEM, _make_config())
    call_msgs = mock_client.messages.create.call_args.kwargs["messages"]
    assert _SAMPLE_ITEM["title"] in call_msgs[0]["content"]


def test_generate_content_package_sets_trend_url():
    from engines.generation.writer import generate_content_package
    with patch("engines.generation.writer.anthropic.Anthropic") as mock_cls:
        mock_cls.return_value = _mock_client(_SAMPLE_RESPONSE)
        result = generate_content_package(_SAMPLE_ITEM, _make_config())
    assert result.trend_url == _SAMPLE_ITEM["url"]
