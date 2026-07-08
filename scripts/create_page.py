#!/usr/bin/env python3
"""Create a new Wiki.js page.

Usage:
    python create_page.py <path> <title> <content> [--description DESC] [--tags tag1,tag2]
"""

from __future__ import annotations

import argparse
import sys

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page
from wiki_script.operations.assets import AssetsManager
from wiki_script.operations.pages import PagesManager
from wiki_script.wiki_client import WikiJSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a new Wiki.js page")
    parser.add_argument("path", help="Page path (e.g. 'projects/alpha/overview')")
    parser.add_argument("title", help="Page title")
    parser.add_argument("content", help="Page content (markdown)")
    parser.add_argument("--description", default="", help="Page description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--locale", default="en", help="Locale (default: en)")
    parser.add_argument("--private", action="store_true", help="Mark as private")
    parser.add_argument("--unpublished", action="store_true", help="Do not publish")

    args = parser.parse_args()

    try:
        client = WikiJSClient()
        pages = PagesManager(client)

        page = Page(
            path=args.path,
            title=args.title,
            content=args.content,
            description=args.description,
            locale=args.locale,
            isPrivate=args.private,
            isPublished=not args.unpublished,
            tags=[t.strip() for t in args.tags.split(",") if t.strip()],
        )

        response = pages.create(page)
        page_id = response.page.id if response.page else "?"
        print(f"Created page (id={page_id}): {response.message}")
    except WikiJSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
