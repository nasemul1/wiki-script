"""Page-related menu handlers."""

from __future__ import annotations

import os

from wiki_cli.utils import PAGE_SIZE, input_with_default, print_page_table
from wiki_cli.models import Page
from wiki_cli.pages import PagesManager


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
    description = input_with_default(
        "New description (leave blank to keep)", existing.description
    )
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
    pub_raw = input_with_default(
        "Published? (y/n)", "y" if existing.isPublished else "n"
    )
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
    confirm = (
        input(f"Are you sure you want to delete page {raw}? (yes/no): ")
        .strip()
        .lower()
    )
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
        result = [
            p for p in result if filter_tag.lower() in [t.lower() for t in p.tags]
        ]
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
        print(
            f"\n  Showing {offset + 1}-{offset + len(chunk)} of {total} "
            f"({remaining} more)"
        )
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
        result = [
            p for p in result if filter_tag.lower() in [t.lower() for t in p.tags]
        ]
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
            child = node.get(part)
            if child is None:
                node[part] = {}
                node = node[part]
            elif isinstance(child, dict):
                node = child
            else:
                node[part] = {}
                node = node[part]
        node[parts[-1]] = p

    def _print_tree(d: dict, prefix: str = "", is_last: bool = True) -> None:
        items = sorted(d.items(), key=lambda x: (not isinstance(x[1], dict), x[0]))
        for i, (name, value) in enumerate(items):
            last = i == len(items) - 1
            connector = "└── " if last else "├── "
            if isinstance(value, dict):
                print(f"{prefix}{connector}{name}/")
                extension = "    " if last else "│   "
                _print_tree(value, prefix + extension, last)
            else:
                pub = "" if value.isPublished else " [draft]"
                print(f"{prefix}{connector}{name} (id={value.id}){pub}")

    print("\n/ (root)")
    _print_tree(tree)

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
    print(f"  {existing.path}  ->  {new_path}")
    if new_title != existing.title:
        print(f"  Title: {existing.title}  ->  {new_title}")
    confirm = input("\nContinue? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Cancelled.")
        return

    existing.path = new_path
    existing.title = new_title
    pages.update(existing)
    print(f"\nMoved page {page_id} to: {new_path}")


def clone_page(pages: PagesManager) -> None:
    raw = input("Source page ID: ").strip()
    if not raw.isdigit():
        print("Invalid ID.")
        return
    source_id = int(raw)

    source = pages.get_by_id(source_id)
    print(f"\nSource: {source.path} -- {source.title}")

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
        f.write("---\n")
        f.write(f"title: {page.title}\n")
        f.write(f"path: {page.path}\n")
        f.write(f"description: {page.description}\n")
        f.write(f"tags: [{', '.join(page.tags)}]\n")
        f.write(f"published: {page.isPublished}\n")
        f.write(f"private: {page.isPrivate}\n")
        f.write(f"locale: {page.locale}\n")
        f.write(f"editor: {page.editor}\n")
        f.write("---\n\n")
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
            content = content[end + 3 :].strip()

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
    tags = (
        [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
        if tags_str
        else []
    )

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
