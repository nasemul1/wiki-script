"""Shared helpers for the CLI."""

from __future__ import annotations

from wiki_cli.models import Page, PageHistory

PAGE_SIZE = 20


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
