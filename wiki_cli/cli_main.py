"""Main menu loop."""

from __future__ import annotations

import sys

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.pages import PagesManager

from wiki_cli.cli_pages import (
    browse_tree,
    clone_page,
    create_page,
    delete_page,
    export_page,
    fetch_page,
    import_page,
    list_pages,
    move_rename_page,
    search_pages,
    update_page,
)
from wiki_cli.cli_history import (
    diff_two_revisions,
    restore_revision,
    view_page_history,
    view_specific_revision,
)
from wiki_cli.cli_system import test_connection

MENU = """
========================================
       Wiki.js Manager
========================================
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

  --- AI ---
  17. AI Assistant
  0. Exit
========================================
"""


def _ai_assistant() -> None:
    """Launch the AI assistant (lazy import to avoid requiring openai when unused)."""
    from wiki_cli.ai.cli import ai_mode

    ai_mode()


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
        "17": ("AI Assistant", _ai_assistant),
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
