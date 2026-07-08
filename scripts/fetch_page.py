#!/usr/bin/env python3
"""Fetch a Wiki.js page by ID or path.

Usage:
    python fetch_page.py --id 15
    python fetch_page.py --path projects/alpha/overview
"""

from __future__ import annotations

import argparse
import sys

from wiki_script.exceptions import WikiJSError
from wiki_script.operations.pages import PagesManager
from wiki_script.wiki_client import WikiJSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch a Wiki.js page")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--id", type=int, help="Page ID")
    group.add_argument("--path", help="Page path (e.g. 'projects/alpha/overview')")
    parser.add_argument("--locale", default="en", help="Locale (default: en)")

    args = parser.parse_args()

    try:
        client = WikiJSClient()
        pages = PagesManager(client)

        if args.id is not None:
            page = pages.get_by_id(args.id)
        else:
            page = pages.get_by_path(args.path, locale=args.locale)

        print(f"ID:          {page.id}")
        print(f"Path:        {page.path}")
        print(f"Title:       {page.title}")
        print(f"Description: {page.description}")
        print(f"Tags:        {page.tags}")
        print(f"Published:   {page.isPublished}")
        print(f"Private:     {page.isPrivate}")
        print(f"---")
        print(page.content)
    except WikiJSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
