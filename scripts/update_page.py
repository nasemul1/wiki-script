#!/usr/bin/env python3
"""Update an existing Wiki.js page.

Usage:
    python update_page.py --id 15 --content "# New Content" --title "New Title"
    python update_page.py --id 15 --append-content "\n\n## Appended Section"
"""

from __future__ import annotations

import argparse
import sys

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page
from wiki_script.operations.pages import PagesManager
from wiki_script.wiki_client import WikiJSClient


def main() -> None:
    parser = argparse.ArgumentParser(description="Update a Wiki.js page")
    parser.add_argument("--id", type=int, required=True, help="Page ID")
    parser.add_argument("--title", help="New title")
    parser.add_argument("--content", help="Replace page content entirely")
    parser.add_argument("--append-content", help="Append text to existing content")
    parser.add_argument("--description", help="New description")
    parser.add_argument("--tags", help="Comma-separated tags (replaces existing)")
    parser.add_argument("--published", action=argparse.BooleanOptionalAction, help="Set published status")

    args = parser.parse_args()

    try:
        client = WikiJSClient()
        pages = PagesManager(client)

        existing = pages.get_by_id(args.id)

        if args.title:
            existing.title = args.title
        if args.content is not None:
            existing.content = args.content
        elif args.append_content:
            existing.content += args.append_content
        if args.description is not None:
            existing.description = args.description
        if args.tags is not None:
            existing.tags = [t.strip() for t in args.tags.split(",") if t.strip()]
        if args.published is not None:
            existing.isPublished = args.published

        response = pages.update(existing)
        print(f"Updated page {args.id}: {response.message}")
    except WikiJSError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
