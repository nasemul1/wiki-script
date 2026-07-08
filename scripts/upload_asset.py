#!/usr/bin/env python3
"""Upload a file to Wiki.js assets.

Usage:
    python upload_asset.py <file_path> [--folder-id 0]
"""

from __future__ import annotations

import argparse
import sys
from urllib.parse import urlparse

from wiki_script.exceptions import WikiJSError
from wiki_script.operations.assets import AssetsManager
from wiki_script.wiki_client import WikiJSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Upload a file to Wiki.js assets")
    parser.add_argument("file", help="Local file path to upload")
    parser.add_argument(
        "--folder-id", type=int, default=0, help="Destination folder ID (0 = root)"
    )

    args = parser.parse_args()

    try:
        client = WikiJSClient()

        # AssetsManager needs the base URL (strip /graphql from the end)
        base_url = client.url
        parsed = urlparse(base_url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"

        assets = AssetsManager(base_url=base_url, api_key=client.api_key)
        asset = assets.upload(args.file, folder_id=args.folder_id)
        print(f"Uploaded: {asset.filename}")
    except WikiJSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
