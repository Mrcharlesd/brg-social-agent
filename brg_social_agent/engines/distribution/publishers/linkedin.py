import logging
from pathlib import Path
from typing import Optional

import requests

log = logging.getLogger(__name__)
_LI_BASE = "https://api.linkedin.com"


class LinkedInPublisher:
    def __init__(
        self,
        person_id: str,
        access_token: str,
        li_base: str = _LI_BASE,
    ):
        self._person_id = person_id
        self._token = access_token
        self._li_base = li_base.rstrip("/")

    @property
    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def _upload_image(self, image_path: Path) -> str:
        register_resp = requests.post(
            f"{self._li_base}/v2/assets",
            params={"action": "registerUpload"},
            headers=self._headers,
            json={
                "registerUploadRequest": {
                    "recipes": ["urn:li:digitalmediaRecipe:feedshare-image"],
                    "owner": f"urn:li:person:{self._person_id}",
                    "serviceRelationships": [
                        {
                            "relationshipType": "OWNER",
                            "identifier": "urn:li:userGeneratedContent",
                        }
                    ],
                }
            },
        )
        register_resp.raise_for_status()
        data = register_resp.json()
        upload_url = data["value"]["uploadMechanism"][
            "com.linkedin.digitalmedia.uploading.MediaUploadHttpRequest"
        ]["uploadUrl"]
        asset_urn = data["value"]["asset"]

        upload_resp = requests.put(
            upload_url,
            headers={
                "Authorization": f"Bearer {self._token}",
                "Content-Type": "image/png",
            },
            data=image_path.read_bytes(),
        )
        upload_resp.raise_for_status()
        return asset_urn

    def publish_post(self, text: str, image_path: Optional[Path] = None) -> str:
        share_content: dict = {"shareCommentary": {"text": text}}
        if image_path is not None:
            asset_urn = self._upload_image(image_path)
            share_content["shareMediaCategory"] = "IMAGE"
            share_content["media"] = [{"status": "READY", "media": asset_urn}]
        else:
            share_content["shareMediaCategory"] = "NONE"

        resp = requests.post(
            f"{self._li_base}/v2/ugcPosts",
            headers=self._headers,
            json={
                "author": f"urn:li:person:{self._person_id}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": share_content
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                },
            },
        )
        resp.raise_for_status()
        return resp.headers.get("x-restli-id", "")
