import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from engines.distribution.publishers.linkedin import LinkedInPublisher


def _mock_resp(json_data: dict = None, headers: dict = None) -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = json_data or {}
    resp.headers = headers or {}
    resp.raise_for_status.return_value = None
    return resp


def test_publish_post_text_only_sends_ugc_post_without_image():
    pub = LinkedInPublisher(
        person_id="abc123",
        access_token="li-tok",
        li_base="https://fake.li.test",
    )
    post_resp = _mock_resp(headers={"x-restli-id": "urn:li:ugcPost:99999"})
    with patch(
        "engines.distribution.publishers.linkedin.requests.post",
        return_value=post_resp,
    ) as mock_post:
        result = pub.publish_post(text="Test post body")
    assert result == "urn:li:ugcPost:99999"
    body = mock_post.call_args[1]["json"]
    content = body["specificContent"]["com.linkedin.ugc.ShareContent"]
    assert content["shareMediaCategory"] == "NONE"
    assert "media" not in content


def test_publish_post_with_image_registers_upload_then_puts_bytes_then_posts(tmp_path):
    pub = LinkedInPublisher(
        person_id="abc123",
        access_token="li-tok",
        li_base="https://fake.li.test",
    )
    image_path = tmp_path / "quote.png"
    image_path.write_bytes(b"PNG_BYTES")

    register_resp = _mock_resp(
        json_data={
            "value": {
                "uploadMechanism": {
                    "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest": {
                        "uploadUrl": "https://fake-upload.li.test/upload"
                    }
                },
                "asset": "urn:li:digitalmediaAsset:abc",
            }
        }
    )
    put_resp = _mock_resp()
    post_resp = _mock_resp(headers={"x-restli-id": "urn:li:ugcPost:12345"})

    with patch(
        "engines.distribution.publishers.linkedin.requests.post",
        side_effect=[register_resp, post_resp],
    ) as mock_post, patch(
        "engines.distribution.publishers.linkedin.requests.put",
        return_value=put_resp,
    ) as mock_put:
        result = pub.publish_post(text="Test body", image_path=image_path)

    assert result == "urn:li:ugcPost:12345"
    assert mock_put.call_count == 1
    assert mock_put.call_args[0][0] == "https://fake-upload.li.test/upload"
    post_body = mock_post.call_args_list[1][1]["json"]
    content = post_body["specificContent"]["com.linkedin.ugc.ShareContent"]
    assert content["shareMediaCategory"] == "IMAGE"
    assert content["media"][0]["media"] == "urn:li:digitalmediaAsset:abc"


def test_publish_post_includes_correct_author_urn():
    pub = LinkedInPublisher(
        person_id="abc123",
        access_token="li-tok",
        li_base="https://fake.li.test",
    )
    post_resp = _mock_resp(headers={"x-restli-id": "urn:li:ugcPost:1"})
    with patch(
        "engines.distribution.publishers.linkedin.requests.post",
        return_value=post_resp,
    ) as mock_post:
        pub.publish_post(text="Hello")
    body = mock_post.call_args[1]["json"]
    assert body["author"] == "urn:li:person:abc123"


def test_raises_on_linkedin_http_error():
    pub = LinkedInPublisher(
        person_id="abc123",
        access_token="li-tok",
        li_base="https://fake.li.test",
    )
    error_resp = MagicMock()
    error_resp.raise_for_status.side_effect = Exception("HTTP 401 Unauthorized")
    with patch(
        "engines.distribution.publishers.linkedin.requests.post",
        return_value=error_resp,
    ):
        try:
            pub.publish_post(text="Hello")
            assert False, "Expected exception"
        except Exception as exc:
            assert "401" in str(exc)
