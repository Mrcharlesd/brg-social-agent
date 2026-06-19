import logging

import requests

log = logging.getLogger(__name__)
_FB_BASE = "https://graph.facebook.com/v19.0"


class InstagramPublisher:
    def __init__(
        self,
        account_id: str,
        access_token: str,
        image_base_url: str,
        fb_base: str = _FB_BASE,
    ):
        self._account_id = account_id
        self._token = access_token
        self._image_base_url = image_base_url.rstrip("/")
        self._fb_base = fb_base.rstrip("/")

    def _image_url(self, post_id: str, filename: str) -> str:
        return f"{self._image_base_url}/{post_id}/{filename}"

    def _create_container(self, **params: str) -> str:
        url = f"{self._fb_base}/{self._account_id}/media"
        resp = requests.post(url, data={**params, "access_token": self._token})
        resp.raise_for_status()
        return resp.json()["id"]

    def _publish(self, container_id: str) -> str:
        url = f"{self._fb_base}/{self._account_id}/media_publish"
        resp = requests.post(
            url, data={"creation_id": container_id, "access_token": self._token}
        )
        resp.raise_for_status()
        return resp.json()["id"]

    def publish_carousel(
        self, post_id: str, slide_filenames: list[str], caption: str
    ) -> str:
        child_ids = [
            self._create_container(
                image_url=self._image_url(post_id, fn),
                is_carousel_item="true",
            )
            for fn in slide_filenames
        ]
        carousel_id = self._create_container(
            media_type="CAROUSEL",
            children=",".join(child_ids),
            caption=caption,
        )
        return self._publish(carousel_id)

    def publish_image(self, post_id: str, filename: str, caption: str) -> str:
        container_id = self._create_container(
            image_url=self._image_url(post_id, filename),
            caption=caption,
        )
        return self._publish(container_id)

    def publish_story(self, post_id: str, filename: str) -> str:
        container_id = self._create_container(
            image_url=self._image_url(post_id, filename),
            media_type="STORIES",
        )
        return self._publish(container_id)
