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

PAGE_SIZE = 20

MENU = """
=========================================
       Wiki.js Manager
=========================================
  --- Pages ---
  1. Create Page
  2. Fetch Page
  3. Update Page
  4. Delete Page
  5. List Pages
  6. Search Pages
  7. Browse Pages (tree)

  --- Assets ---
  8. Upload Asset

  --- System ---
  0. Exit
=========================================
"""


def input_with_default(prompt: str, default: str = "") -> str:
    hint = f" [{default}]" if default else ""
    value = input(f"{prompt}{hint}: ").strip()
    return value if value else default


def print_page_table(page_list: list[Page]) -> None:
    if not page_list:
        print("\nNo pages found.")
        return
    print(f"\n{'ID':<6} {'Path':<45} {'Title':<30} {'Published'}")
    print("-" * 95)
    for p in page_list:
        pub = "Yes" if p.isPublished else "No"
        print(f"{p.id:<6} {p.path:<45} {p.title:<30} {pub}")


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


def list_pages(pages: PagesManager) -> None:
    print("Sort by:  1 = Title, 2 = Path, 3 = Created, 4 = Updated")
    choice = input("Choice [1]: ").strip() or "1"
    order_map = {"1": "TITLE", "2": "PATH", "3": "CREATED", "4": "UPDATED"}
    order_by = order_map.get(choice, "TITLE")

    result = pages.list_all(order_by=order_by)
    if not result:
        print("\nNo pages found.")
        return

    total = len(result)
    offset = 0

    while offset < total:
        chunk = result[offset : offset + PAGE_SIZE]
        print_page_table(chunk)
        remaining = total - offset - PAGE_SIZE
        if remaining <= 0:
            break
        print(f"\n  Showing {offset + 1}-{offset + len(chunk)} of {total} "
              f"({remaining} more)")
        cmd = input("  [Enter] next page, [q] quit: ").strip().lower()
        if cmd == "q":
            break
        offset += PAGE_SIZE

    print(f"\nTotal: {total} page(s)")


def search_pages(pages: PagesManager) -> None:
    query = input("Search query: ").strip()
    if not query:
        print("Query is required.")
        return
    locale = input_with_default("Locale (leave blank for all)", "")

    result = pages.search(query, locale=locale) if locale else pages.search(query)

    if not result:
        print("\nNo pages found.")
        return

    print_page_table(result)
    print(f"\nTotal: {len(result)} page(s)")


def browse_tree(pages: PagesManager) -> None:
    result = pages.list_all(order_by="PATH")
    if not result:
        print("\nNo pages found.")
        return

    tree: dict = {}
    for p in result:
        parts = p.path.split("/")
        node = tree
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = p

    def print_tree(d: dict, prefix: str = "", is_last: bool = True) -> None:
        items = sorted(d.items(), key=lambda x: (not isinstance(x[1], dict), x[0]))
        for i, (name, value) in enumerate(items):
            last = i == len(items) - 1
            connector = "└── " if last else "├── "
            if isinstance(value, dict):
                print(f"{prefix}{connector}{name}/")
                extension = "    " if last else "│   "
                print_tree(value, prefix + extension, last)
            else:
                pub = "" if value.isPublished else " [draft]"
                print(f"{prefix}{connector}{name} (id={value.id}){pub}")

    print("\n/ (root)")
    print_tree(tree)

    print("\nEnter page ID to view (or press Enter to go back): ")
    choice = input("ID: ").strip()
    if choice.isdigit():
        page = pages.get_by_id(int(choice))
        print(f"\nID:          {page.id}")
        print(f"Path:        {page.path}")
        print(f"Title:       {page.title}")
        print(f"Description: {page.description}")
        print(f"Tags:        {page.tags}")
        print(f"Published:   {page.isPublished}")
        print(f"Private:     {page.isPrivate}")
        print(f"---")
        print(page.content)


def upload_asset(client: WikiJSClient) -> None:
    file_path = input("Local file path to upload: ").strip()
    if not file_path:
        print("File path is required.")
        return
    folder_id = input_with_default("Destination folder ID", "0")

    base_url = client.url
    parsed = urlparse(base_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    assert client.api_key is not None
    assets = AssetsManager(base_url=base_url, api_key=client.api_key)
    asset = assets.upload(file_path, folder_id=int(folder_id))
    print(f"\nUploaded: {asset.filename} to folder {asset.folder}")


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
        "5": ("List Pages", lambda: list_pages(pages)),
        "6": ("Search Pages", lambda: search_pages(pages)),
        "7": ("Browse Pages (tree)", lambda: browse_tree(pages)),
        "8": ("Upload Asset", lambda: upload_asset(client)),
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
