"""Asset upload operations for Wiki.js using the REST /u endpoint."""

from __future__ import annotations

import json
from pathlib import Path

import requests

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Asset


class AssetsManager:
    """Handles file upload operations against the Wiki.js REST upload endpoint.

    Wiki.js does not expose a GraphQL mutation for asset uploads. Instead,
    files are uploaded via POST to the /u endpoint with multipart form data.

    Attributes:
        base_url: The base URL of the Wiki.js instance (e.g. 'https://wiki.example.com').
        api_key: Bearer token for authentication.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        """Initialize the AssetsManager.

        Args:
            base_url: Base URL of the Wiki.js instance (no trailing /graphql).
            api_key: Bearer token for authentication.
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def upload(self, file_path: str | Path, folder_id: int = 0) -> Asset:
        """Upload a file to Wiki.js via the REST /u endpoint.

        The endpoint expects a multipart/form-data POST with:
          - 'mediaUpload' field: the file binary
          - 'mediaUpload' field: JSON metadata with folderId

        Args:
            file_path: Local path to the file to upload.
            folder_id: Numeric ID of the destination asset folder (0 = root).

        Returns:
            Asset with filename and folder metadata.

        Raises:
            WikiJSError: If the file does not exist or the upload fails.
        """
        path = Path(file_path)

        if not path.exists():
            raise WikiJSError(f"File not found: {path}")
        if not path.is_file():
            raise WikiJSError(f"Path is not a file: {path}")

        upload_url = f"{self.base_url}/u"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        metadata = json.dumps({"folderId": folder_id})

        with open(path, "rb") as f:
            files = {
                "mediaUpload": (
                    path.name,
                    f,
                    "application/octet-stream",
                ),
            }
            data = {"mediaUpload": metadata}

            try:
                response = requests.post(
                    upload_url,
                    headers=headers,
                    files=files,
                    data=data,
                    timeout=60,
                )
            except requests.RequestException as exc:
                raise WikiJSError(f"Upload request failed: {exc}") from exc

        if response.status_code != 200:
            raise WikiJSError(
                f"Upload failed with status {response.status_code}: {response.text}"
            )

        return Asset(
            filename=path.name,
            folder=f"/{folder_id}" if folder_id else "/",
        )
