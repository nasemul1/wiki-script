"""History-related menu handlers."""

from __future__ import annotations

import difflib

from wiki_cli.utils import PAGE_SIZE, input_with_default, print_history_table
from wiki_cli.pages import PagesManager


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
        entries, total = pages.get_history(
            page_id, offset_page=offset_page, offset_size=PAGE_SIZE
        )
        if not entries:
            if offset_page == 0:
                print("\nNo history entries found.")
            return

        print_history_table(entries, total)
        remaining = total - (offset_page + 1) * PAGE_SIZE
        if remaining <= 0:
            break
        print(
            f"\n  Showing {offset_page * PAGE_SIZE + 1}-{offset_page * PAGE_SIZE + len(entries)} of {total} "
            f"({remaining} more)"
        )
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

    print(f"\n{'=' * 60}")
    print(f"Version:   {version.versionId}")
    print(f"Date:      {version.versionDate}")
    print(f"Author:    {version.authorName}")
    print(f"Action:    {version.action}")
    print(f"Path:      {version.path}")
    print(f"Title:     {version.title}")
    print(f"Tags:      {version.tags}")
    print(f"Published: {version.isPublished}")
    print(f"{'=' * 60}")
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

    diff = difflib.unified_diff(
        old_lines, new_lines, fromfile=old_label, tofile=new_label
    )

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
