#!/usr/bin/env python3
"""Interactive terminal menu for Wiki.js operations."""

from __future__ import annotations

import sys
from urllib.parse import urlparse

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page
from wiki_script.operations.assets import AssetsManager
from wiki_script.operations.pages import PagesManager
from wiki_script.wiki_client import WikiJSClient

MENU = """
=========================================
       Wiki.js Manager
=========================================
  1. Create Page
  2. Fetch Page
  3. Update Page
  4. Delete Page
  5. Upload Asset
  6. List All Pages
  0. Exit
=========================================
"""


def input_with_default(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{prompt}{hint}: ").strip()
    return value if value else default


def create_page(pages: PagesManager) -> None:
    path = input("Page path (e.g. projects/alpha/overview): ").strip()
    if not path:
        print("Path is required.")
        return
    title = input("Page title: ").strip()
    if not title:
        print("Title is required.")
        return
    content = input("Page content (markdown): ").strip()
    description = input_with_default("Description", "")
    tags_raw = input_with_default("Tags (comma-separated)", "")
    locale = input_with_default("Locale", "en")
    private = input_with_default("Private? (y/n)", "n").lower() == "y"
    published = input_with_default("Published? (y/n)", "y").lower() != "n"

    page = Page(
        path=path,
        title=title,
        content=content,
        description=description,
        locale=locale,
        isPrivate=private,
        isPublished=published,
        tags=[t.strip() for t in tags_raw.split(",") if t.strip()],
    )

    response = pages.create(page)
    page_id = response.page.id if response.page else "?"
    print(f"\nCreated page (id={page_id}): {response.message}")


def fetch_page(pages: PagesManager) -> None:
    print("Fetch by:  1 = ID, 2 = Path")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "1":
        raw = input("Page ID: ").strip()
        if not raw.isdigit():
            print("Invalid ID.")
            return
        page = pages.get_by_id(int(raw))
    else:
        path = input("Page path: ").strip()
        if not path:
            print("Path is required.")
            return
        locale = input_with_default("Locale", "en")
        page = pages.get_by_path(path, locale=locale)

    print(f"\nID:          {page.id}")
    print(f"Path:        {page.path}")
    print(f"Title:       {page.title}")
    print(f"Description: {page.description}")
    print(f"Tags:        {page.tags}")
    print(f"Published:   {page.isPublished}")
    print(f"Private:     {page.isPrivate}")
    print(f"---")
    print(page.content)


def update_page(pages: PagesManager) -> None:
    raw = input("Page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    page_id = int(raw)

    existing = pages.get_by_id(page_id)
    print(f"Current title: {existing.title}")

    title = input_with_default("New title (leave blank to keep)", existing.title)
    description = input_with_default("New description (leave blank to keep)", existing.description)
    print("Content options:  1 = Replace entirely, 2 = Append, 3 = Keep unchanged")
    content_choice = input("Choice [3]: ").strip() or "3"

    content = existing.content
    if content_choice == "1":
        content = input("New content (markdown): ").strip()
    elif content_choice == "2":
        append_text = input("Text to append: ").strip()
        content = existing.content + append_text

    tags_raw = input_with_default(
        "Tags (comma-separated, leave blank to keep)",
        ",".join(existing.tags),
    )
    pub_raw = input_with_default("Published? (y/n)", "y" if existing.isPublished else "n")
    is_published = pub_raw.lower() != "n"

    existing.title = title
    existing.description = description
    existing.content = content
    existing.tags = [t.strip() for t in tags_raw.split(",") if t.strip()]
    existing.isPublished = is_published

    response = pages.update(existing)
    print(f"\nUpdated page {page_id}: {response.message}")


def delete_page(pages: PagesManager) -> None:
    raw = input("Page ID to delete: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    confirm = input(f"Are you sure you want to delete page {raw}? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return
    pages.delete(int(raw))
    print(f"\nDeleted page {raw}.")


def upload_asset(client: WikiJSClient) -> None:
    file_path = input("Local file path to upload: ").strip()
    if not file_path:
        print("File path is required.")
        return
    folder_id = input_with_default("Destination folder ID", "0")

    base_url = client.url
    parsed = urlparse(base_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    assets = AssetsManager(base_url=base_url, api_key=client.api_key)
    asset = assets.upload(file_path, folder_id=int(folder_id))
    print(f"\nUploaded: {asset.filename} to folder {asset.folder}")


def list_pages(pages: PagesManager) -> None:
    print("Sort by:  1 = Title, 2 = Path, 3 = Created, 4 = Updated")
    choice = input("Choice [1]: ").strip() or "1"
    order_map = {"1": "TITLE", "2": "PATH", "3": "CREATED", "4": "UPDATED"}
    order_by = order_map.get(choice, "TITLE")

    result = pages.list_all(order_by=order_by)

    if not result:
        print("\nNo pages found.")
        return

    print(f"\n{'ID':<6} {'Path':<40} {'Title':<30} {'Published'}")
    print("-" * 90)
    for p in result:
        pub = "Yes" if p.isPublished else "No"
        print(f"{p.id:<6} {p.path:<40} {p.title:<30} {pub}")

    print(f"\nTotal: {len(result)} page(s)")


def main() -> None:
    try:
        client = WikiJSClient()
        pages = PagesManager(client)
    except WikiJSError as exc:
        print(f"Error initializing client: {exc}", file=sys.stderr)
        sys.exit(1)

    handlers = {
        "1": ("Create Page", lambda: create_page(pages)),
        "2": ("Fetch Page", lambda: fetch_page(pages)),
        "3": ("Update Page", lambda: update_page(pages)),
        "4": ("Delete Page", lambda: delete_page(pages)),
        "5": ("Upload Asset", lambda: upload_asset(client)),
        "6": ("List All Pages", lambda: list_pages(pages)),
    }

    while True:
        print(MENU)
        choice = input("Select an option: ").strip()

        if choice == "0":
            print("Goodbye!")
            break

        if choice not in handlers:
            print("Invalid option. Try again.")
            continue

        label, handler = handlers[choice]
        print(f"\n--- {label} ---")
        try:
            handler()
        except WikiJSError as exc:
            print(f"Error: {exc}", file=sys.stderr)

        input("\nPress Enter to continue...")


if __name__ == "__main__":
    main()
