import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engines.distribution.publishers.instagram import InstagramPublisher


def _mock_resp(json_data: dict, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.raise_for_status.return_value = None
    return resp


def test_image_url_uses_base_url_and_post_id():
    pub = InstagramPublisher(
        account_id="12345",
        access_token="tok",
        image_base_url="https://example.com/queue",
    )
    assert pub._image_url("my-post-abc12345", "carousel_slide_000.png") == (
        "https://example.com/queue/my-post-abc12345/carousel_slide_000.png"
    )


def test_publish_carousel_creates_item_containers_then_carousel_then_publishes():
    pub = InstagramPublisher(
        account_id="12345",
        access_token="tok",
        image_base_url="https://example.com/queue",
        fb_base="https://fake.fb.test/v19.0",
    )
    responses = [
        _mock_resp({"id": "child-1"}),
        _mock_resp({"id": "child-2"}),
        _mock_resp({"id": "carousel-1"}),
        _mock_resp({"id": "media-99"}),
    ]
    with patch(
        "engines.distribution.publishers.instagram.requests.post",
        side_effect=responses,
    ) as mock_post:
        result = pub.publish_carousel(
            post_id="my-post-abc12345",
            slide_filenames=["carousel_slide_000.png", "carousel_slide_001.png"],
            caption="Test caption",
        )
    assert result == "media-99"
    assert mock_post.call_count == 4
    carousel_data = mock_post.call_args_list[2][1]["data"]
    assert carousel_data["media_type"] == "CAROUSEL"
    assert "child-1" in carousel_data["children"]
    assert "child-2" in carousel_data["children"]


def test_publish_image_creates_container_then_publishes():
    pub = InstagramPublisher(
        account_id="12345",
        access_token="tok",
        image_base_url="https://example.com/queue",
        fb_base="https://fake.fb.test/v19.0",
    )
    responses = [
        _mock_resp({"id": "container-1"}),
        _mock_resp({"id": "media-50"}),
    ]
    with patch(
        "engines.distribution.publishers.instagram.requests.post",
        side_effect=responses,
    ) as mock_post:
        result = pub.publish_image("my-post-abc12345", "quote.png", "Test caption")
    assert result == "media-50"
    assert mock_post.call_count == 2


def test_publish_story_sends_stories_media_type():
    pub = InstagramPublisher(
        account_id="12345",
        access_token="tok",
        image_base_url="https://example.com/queue",
        fb_base="https://fake.fb.test/v19.0",
    )
    responses = [
        _mock_resp({"id": "story-container-1"}),
        _mock_resp({"id": "story-media-1"}),
    ]
    with patch(
        "engines.distribution.publishers.instagram.requests.post",
        side_effect=responses,
    ) as mock_post:
        result = pub.publish_story("my-post-abc12345", "story_frame_000.png")
    assert result == "story-media-1"
    container_data = mock_post.call_args_list[0][1]["data"]
    assert container_data["media_type"] == "STORIES"


def test_raises_on_http_error_from_instagram():
    pub = InstagramPublisher(
        account_id="12345",
        access_token="tok",
        image_base_url="https://example.com/queue",
        fb_base="https://fake.fb.test/v19.0",
    )
    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = Exception("HTTP 400 Bad Request")
    with patch(
        "engines.distribution.publishers.instagram.requests.post",
        return_value=error_resp,
    ):
        try:
            pub.publish_image("my-post-abc12345", "quote.png", "caption")
            assert False, "Expected exception"
        except Exception as exc:
            assert "HTTP 400" in str(exc)
