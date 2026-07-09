"""Asset operations for Wiki.js (upload, list, download, delete, folders)."""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

import requests

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Asset, AssetFolder

# --- GraphQL Queries & Mutations ---

_LIST_ASSETS = """
query ListAssets($folderId: Int!, $kind: AssetKind!) {
  assets {
    list(folderId: $folderId, kind: $kind) {
      id
      filename
      ext
      kind
      mime
      fileSize
      createdAt
      updatedAt
      folder {
        id
        slug
      }
    }
  }
}
"""

_LIST_FOLDERS = """
query ListFolders($parentFolderId: Int!) {
  assets {
    folders(parentFolderId: $parentFolderId) {
      id
      slug
      name
    }
  }
}
"""

_CREATE_FOLDER = """
mutation CreateFolder($parentFolderId: Int!, $slug: String!, $name: String) {
  assets {
    createFolder(parentFolderId: $parentFolderId, slug: $slug, name: $name) {
      responseResult {
        succeeded
        message
      }
    }
  }
}
"""

_DELETE_ASSET = """
mutation DeleteAsset($id: Int!) {
  assets {
    deleteAsset(id: $id) {
      responseResult {
        succeeded
        message
      }
    }
  }
}
"""


class AssetsManager:
    """Handles asset operations against the Wiki.js API.

    Uses GraphQL for list/delete/folder operations and REST for upload/download.

    Attributes:
        base_url: The base URL of the Wiki.js instance.
        api_key: Bearer token for authentication.
    """

    def __init__(self, base_url: str, api_key: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key

    def _gql_execute(self, query: str, variables: dict | None = None) -> dict:
        """Execute a GraphQL query using raw requests (avoids gql library dependency for assets)."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload: dict = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            response = requests.post(
                f"{self.base_url}/graphql",
                headers=headers,
                json=payload,
                timeout=30,
            )
        except requests.RequestException as exc:
            raise WikiJSError(f"GraphQL request failed: {exc}") from exc

        if response.status_code != 200:
            raise WikiJSError(
                f"GraphQL request failed with status {response.status_code}: {response.text}"
            )

        data = response.json()
        if "errors" in data:
            messages = "; ".join(e.get("message", "Unknown") for e in data["errors"])
            raise WikiJSError(f"GraphQL errors: {messages}")

        return data.get("data", {})

    def list_assets(self, folder_id: int = 0, kind: str = "ALL") -> list[Asset]:
        """List assets in a folder.

        Args:
            folder_id: Folder ID to list (0 = root).
            kind: Filter by kind - IMAGE, BINARY, or ALL.

        Returns:
            List of Asset objects.
        """
        result = self._gql_execute(_LIST_ASSETS, {"folderId": folder_id, "kind": kind})
        raw_assets = result.get("assets", {}).get("list", [])
        return [
            Asset(
                id=a["id"],
                filename=a["filename"],
                ext=a.get("ext", ""),
                kind=a.get("kind", ""),
                mime=a.get("mime", ""),
                fileSize=a.get("fileSize", 0),
                folderId=a.get("folder", {}).get("id") if a.get("folder") else None,
                folderSlug=a.get("folder", {}).get("slug", "") if a.get("folder") else "",
                createdAt=a.get("createdAt", ""),
                updatedAt=a.get("updatedAt", ""),
            )
            for a in raw_assets
        ]

    def list_folders(self, parent_folder_id: int = 0) -> list[AssetFolder]:
        """List subfolders in a folder.

        Args:
            parent_folder_id: Parent folder ID (0 = root).

        Returns:
            List of AssetFolder objects.
        """
        result = self._gql_execute(_LIST_FOLDERS, {"parentFolderId": parent_folder_id})
        raw_folders = result.get("assets", {}).get("folders", [])
        return [
            AssetFolder(id=f["id"], slug=f["slug"], name=f.get("name", f["slug"]))
            for f in raw_folders
        ]

    def create_folder(self, parent_folder_id: int, slug: str, name: str = "") -> bool:
        """Create a new asset folder.

        Args:
            parent_folder_id: Parent folder ID (0 = root).
            slug: Folder slug (URL-safe name).
            name: Display name (defaults to slug).

        Returns:
            True on success.

        Raises:
            WikiJSError: If creation fails.
        """
        result = self._gql_execute(_CREATE_FOLDER, {
            "parentFolderId": parent_folder_id,
            "slug": slug,
            "name": name or slug,
        })
        response = result.get("assets", {}).get("createFolder", {}).get("responseResult", {})
        if not response.get("succeeded"):
            raise WikiJSError(f"Failed to create folder: {response.get('message', 'Unknown error')}")
        return True

    def delete_asset(self, asset_id: int) -> bool:
        """Delete an asset by ID.

        Args:
            asset_id: The numeric ID of the asset to delete.

        Returns:
            True on success.

        Raises:
            WikiJSError: If deletion fails.
        """
        result = self._gql_execute(_DELETE_ASSET, {"id": asset_id})
        response = result.get("assets", {}).get("deleteAsset", {}).get("responseResult", {})
        if not response.get("succeeded"):
            raise WikiJSError(f"Failed to delete asset: {response.get('message', 'Unknown error')}")
        return True

    def download(self, asset_id: int, filename: str, save_path: str | Path) -> Path:
        """Download an asset to a local file.

        Args:
            asset_id: The numeric ID of the asset.
            filename: The original filename (used in the URL).
            save_path: Local path to save the file.

        Returns:
            Path to the saved file.

        Raises:
            WikiJSError: If the download fails.
        """
        save = Path(save_path)
        download_url = f"{self.base_url}/assets/{asset_id}/{filename}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(download_url, headers=headers, timeout=120, stream=True)
        except requests.RequestException as exc:
            raise WikiJSError(f"Download request failed: {exc}") from exc

        if response.status_code != 200:
            raise WikiJSError(
                f"Download failed with status {response.status_code}: {response.text}"
            )

        with open(save, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return save

    def upload(self, file_path: str | Path, folder_id: int = 0) -> Asset:
        """Upload a file to Wiki.js via the REST /u endpoint.

        Args:
            file_path: Local path to the file to upload.
            folder_id: Numeric ID of the destination asset folder (0 = root).

        Returns:
            Asset with metadata.

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
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

        with open(path, "rb") as f:
            files = {
                "mediaUpload": (path.name, f, mime_type),
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

        resp_data = response.json() if response.text else {}
        return Asset(
            id=resp_data.get("id"),
            filename=path.name,
            ext=path.suffix.lstrip("."),
            mime=mime_type,
            fileSize=path.stat().st_size,
            folderId=folder_id if folder_id else None,
        )
