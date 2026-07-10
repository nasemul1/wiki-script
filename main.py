#!/usr/bin/env python3
"""Interactive terminal menu for Wiki.js operations."""

from __future__ import annotations

import difflib
import os
import sys

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page, PageHistory, PageVersion
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
  8. Move/Rename Page
  9. Clone Page
  10. Export Page to File
  11. Import Page from File

  --- History ---
  12. View Page History
  13. View Specific Revision
  14. Diff Two Revisions
  15. Restore Revision

  --- System ---
  16. Test Connection
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


def print_history_table(entries: list[PageHistory], total: int) -> None:
    if not entries:
        print("\nNo history entries found.")
        return
    print(f"\n{'VerID':<8} {'Date':<22} {'Author':<20} {'Action'}")
    print("-" * 70)
    for h in entries:
        date = h.versionDate[:19] if h.versionDate else ""
        print(f"{h.versionId:<8} {date:<22} {h.authorName:<20} {h.actionType}")


# --- Page Operations ---

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

    filter_tag = input_with_default("Filter by tag (leave blank for all)", "")
    if filter_tag:
        result = [p for p in result if filter_tag.lower() in [t.lower() for t in p.tags]]
        if not result:
            print(f"\nNo pages found with tag '{filter_tag}'.")
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

    filter_tag = input_with_default("Filter by tag (leave blank for all)", "")
    if filter_tag:
        result = [p for p in result if filter_tag.lower() in [t.lower() for t in p.tags]]
        if not result:
            print(f"\nNo pages found with tag '{filter_tag}'.")
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


def move_rename_page(pages: PagesManager) -> None:
    raw = input("Page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    page_id = int(raw)

    existing = pages.get_by_id(page_id)
    print(f"\nCurrent path: {existing.path}")
    print(f"Current title: {existing.title}")

    new_path = input_with_default("New path (leave blank to keep)", existing.path)
    new_title = input_with_default("New title (leave blank to keep)", existing.title)

    if new_path == existing.path and new_title == existing.title:
        print("\nNo changes made.")
        return

    print(f"\nThis will move/rename:")
    print(f"  {existing.path}  →  {new_path}")
    if new_title != existing.title:
        print(f"  Title: {existing.title}  →  {new_title}")
    confirm = input("\nContinue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    existing.path = new_path
    existing.title = new_title
    response = pages.update(existing)
    print(f"\nMoved page {page_id} to: {new_path}")


def clone_page(pages: PagesManager) -> None:
    raw = input("Source page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    source_id = int(raw)

    source = pages.get_by_id(source_id)
    print(f"\nSource: {source.path} — {source.title}")

    new_path = input("New path for clone: ").strip()
    if not new_path:
        print("Path is required.")
        return
    new_title = input_with_default("New title", source.title)

    response = pages.clone_page(source_id, new_path, new_title)
    clone_id = response.page.id if response.page else "?"
    print(f"\nCloned page (id={clone_id}): {new_path}")


def export_page(pages: PagesManager) -> None:
    raw = input("Page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    page = pages.get_by_id(int(raw))

    default_filename = page.path.replace("/", "_") + ".md"
    filename = input_with_default("Export filename", default_filename)

    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"---\n")
        f.write(f"title: {page.title}\n")
        f.write(f"path: {page.path}\n")
        f.write(f"description: {page.description}\n")
        f.write(f"tags: [{', '.join(page.tags)}]\n")
        f.write(f"published: {page.isPublished}\n")
        f.write(f"private: {page.isPrivate}\n")
        f.write(f"locale: {page.locale}\n")
        f.write(f"editor: {page.editor}\n")
        f.write(f"---\n\n")
        f.write(page.content)

    print(f"\nExported page {page.id} to: {filename}")


def import_page(pages: PagesManager) -> None:
    filename = input("Markdown file path: ").strip()
    if not filename:
        print("Filename is required.")
        return
    if not os.path.isfile(filename):
        print(f"File not found: {filename}")
        return

    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()

    has_frontmatter = content.startswith("---")
    meta: dict[str, str] = {}
    if has_frontmatter:
        end = content.find("---", 3)
        if end != -1:
            frontmatter = content[3:end].strip()
            for line in frontmatter.splitlines():
                if ":" in line:
                    key, value = line.split(":", 1)
                    meta[key.strip()] = value.strip()
            content = content[end + 3:].strip()

    path = meta.get("path", "")
    if not path:
        path = input("Page path: ").strip()
    title = meta.get("title", "")
    if not title:
        title = input("Page title: ").strip()
    if not path or not title:
        print("Path and title are required.")
        return

    description = meta.get("description", "")
    tags_str = meta.get("tags", "")
    tags = [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()] if tags_str else []

    page = Page(
        path=path,
        title=title,
        content=content,
        description=description,
        locale=meta.get("locale", "en"),
        isPublished=meta.get("published", "true").lower() == "true",
        isPrivate=meta.get("private", "false").lower() == "true",
        tags=tags,
        editor=meta.get("editor", "markdown"),
    )

    response = pages.create(page)
    page_id = response.page.id if response.page else "?"
    print(f"\nImported page (id={page_id}): {path}")


# --- History Operations ---

def view_page_history(pages: PagesManager) -> None:
    raw = input("Page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    page_id = int(raw)

    page = pages.get_by_id(page_id)
    print(f"\nPage: {page.title} (path: {page.path})")

    offset_page = 0
    while True:
        entries, total = pages.get_history(page_id, offset_page=offset_page, offset_size=PAGE_SIZE)
        if not entries:
            if offset_page == 0:
                print("\nNo history entries found.")
            return

        print_history_table(entries, total)
        remaining = total - (offset_page + 1) * PAGE_SIZE
        if remaining <= 0:
            break
        print(f"\n  Showing {offset_page * PAGE_SIZE + 1}-{offset_page * PAGE_SIZE + len(entries)} of {total} "
              f"({remaining} more)")
        cmd = input("  [Enter] next page, [q] quit: ").strip().lower()
        if cmd == "q":
            break
        offset_page += 1

    print(f"\nTotal: {total} revision(s)")


def view_specific_revision(pages: PagesManager) -> None:
    raw_page = input("Page ID: ").strip()
    if not raw_page.isdigit():
        print("Invalid page ID.")
        return
    raw_ver = input("Version ID: ").strip()
    if not raw_ver.isdigit():
        print("Invalid version ID.")
        return

    version = pages.get_version(int(raw_page), int(raw_ver))

    print(f"\n{'='*60}")
    print(f"Version:   {version.versionId}")
    print(f"Date:      {version.versionDate}")
    print(f"Author:    {version.authorName}")
    print(f"Action:    {version.action}")
    print(f"Path:      {version.path}")
    print(f"Title:     {version.title}")
    print(f"Tags:      {version.tags}")
    print(f"Published: {version.isPublished}")
    print(f"{'='*60}")
    print(version.content)


def diff_two_revisions(pages: PagesManager) -> None:
    raw_page = input("Page ID: ").strip()
    if not raw_page.isdigit():
        print("Invalid page ID.")
        return
    raw_ver1 = input("First version ID (older): ").strip()
    if not raw_ver1.isdigit():
        print("Invalid version ID.")
        return
    raw_ver2 = input("Second version ID (newer): ").strip()
    if not raw_ver2.isdigit():
        print("Invalid version ID.")
        return

    page_id = int(raw_page)
    v1 = pages.get_version(page_id, int(raw_ver1))
    v2 = pages.get_version(page_id, int(raw_ver2))

    old_label = f"v{v1.versionId} ({v1.versionDate[:10] if v1.versionDate else '?'})"
    new_label = f"v{v2.versionId} ({v2.versionDate[:10] if v2.versionDate else '?'})"

    old_lines = v1.content.splitlines(keepends=True)
    new_lines = v2.content.splitlines(keepends=True)

    diff = difflib.unified_diff(old_lines, new_lines, fromfile=old_label, tofile=new_label)

    diff_output = "".join(diff)
    if not diff_output:
        print("\nNo differences found between these versions.")
        return

    print(f"\n--- {old_label}")
    print(f"+++ {new_label}")
    print(diff_output)


def restore_revision(pages: PagesManager) -> None:
    raw_page = input("Page ID: ").strip()
    if not raw_page.isdigit():
        print("Invalid page ID.")
        return
    raw_ver = input("Version ID to restore: ").strip()
    if not raw_ver.isdigit():
        print("Invalid version ID.")
        return

    page_id = int(raw_page)
    version_id = int(raw_ver)

    version = pages.get_version(page_id, version_id)
    print(f"\nThis will restore page to:")
    print(f"  Version: {version.versionId}")
    print(f"  Date:    {version.versionDate}")
    print(f"  Title:   {version.title}")
    print(f"  Author:  {version.authorName}")

    confirm = input("\nAre you sure? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    pages.restore_version(page_id, version_id)
    print(f"\nPage restored to version {version_id}.")


def test_connection(client: WikiJSClient, pages: PagesManager) -> None:
    print("\nTesting connection...")
    print(f"URL: {client.url}")

    try:
        result = pages.list_all(order_by="CREATED")
        print(f"Pages accessible: {len(result)}")

        if result:
            print(f"Most recently created: {result[0].path} — {result[0].title}")
    except WikiJSError as exc:
        print(f"Error: {exc}")
        return

    print("Connection OK.")


# --- Main ---

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
        "8": ("Move/Rename Page", lambda: move_rename_page(pages)),
        "9": ("Clone Page", lambda: clone_page(pages)),
        "10": ("Export Page to File", lambda: export_page(pages)),
        "11": ("Import Page from File", lambda: import_page(pages)),
        "12": ("View Page History", lambda: view_page_history(pages)),
        "13": ("View Specific Revision", lambda: view_specific_revision(pages)),
        "14": ("Diff Two Revisions", lambda: diff_two_revisions(pages)),
        "15": ("Restore Revision", lambda: restore_revision(pages)),
        "16": ("Test Connection", lambda: test_connection(client, pages)),
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
