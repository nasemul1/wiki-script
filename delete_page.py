#!/usr/bin/env python3
"""Delete a Wiki.js page by ID.

Usage:
    python delete_page.py 15
"""

from __future__ import annotations

import argparse
import sys

from wiki_script.exceptions import WikiJSError
from wiki_script.operations.pages import PagesManager
from wiki_script.wiki_client import WikiJSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete a Wiki.js page")
    parser.add_argument("id", type=int, help="Page ID to delete")

    args = parser.parse_args()

    try:
        client = WikiJSClient()
        pages = PagesManager(client)
        pages.delete(args.id)
        print(f"Deleted page {args.id}.")
    except WikiJSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
