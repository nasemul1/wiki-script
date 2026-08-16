"""Wiki management submenu for the main CLI.

Provides manage_wikis_menu() — invoked from main menu option 18.
Covers switch / add / list / remove with explicit confirmation on remove.
"""

from __future__ import annotations

from wiki_cli.client import WikiJSClient
from wiki_cli.wikis import (
    get_active_wiki_name,
    list_wikis,
    remove_wiki,
    set_active_wiki,
    switch_wiki_flow,
)

# ── ANSI ─────────────────────────────────────────────────────────────

R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
C = "\033[36m"
G = "\033[32m"
Y = "\033[33m"

SUBMENU = """
  --- Manage Wikis ---
  1. Switch active wiki
  2. Add new wiki profile
  3. List saved wikis
  4. Remove a wiki profile
  0. Back to main menu
"""


def _list_profiles() -> None:
    """Print all profiles with * marker on active."""
    data = list_wikis()
    active = get_active_wiki_name()
    if not data:
        print(f"  {D}no saved wikis{R}")
        return
    print(f"  {D}saved wikis:{R}")
    for name in sorted(data):
        marker = f" {G}*{R}" if name == active else "  "
        print(f"  {marker} {B}{name}{R}  {data[name]['url']}")
    print()


def _confirm(prompt: str) -> bool:
    """Return True if user types y/yes (case-insensitive). Empty = no."""
    ans = input(prompt).strip().lower()
    return ans in ("y", "yes")


def _remove_wiki_flow(current_client: WikiJSClient) -> WikiJSClient:
    """Picker + confirm + remove. Rebuild via switch flow if active removed."""
    data = list_wikis()
    if not data:
        print(f"  {D}no saved wikis to remove{R}")
        return current_client

    names = sorted(data.keys())

    print(f"  {D}select wiki to remove:{R}")
    for i, n in enumerate(names, 1):
        print(f"    {C}{i}{R}    {n}  {D}{data[n]['url']}{R}")
    cancel_idx = len(names) + 1
    print(f"    {C}{cancel_idx}{R}    cancel")
    print()

    while True:
        choice = input("  > ").strip() or str(cancel_idx)
        if not choice.isdigit():
            print(f"  {Y}invalid choice{R}\n")
            return current_client
        idx = int(choice)
        if idx == cancel_idx:
            print(f"  {D}cancelled{R}\n")
            return current_client
        if 1 <= idx <= len(names):
            target = names[idx - 1]
            break
        print(f"  {Y}invalid choice{R}\n")
        return current_client

    entry = data[target]
    if not _confirm(f"  remove '{target}' ({entry['url']})? [y/n]: "):
        print(f"  {D}cancelled{R}\n")
        return current_client

    was_active = get_active_wiki_name() == target
    remove_wiki(target)
    print(f"  {G}removed → {target}{R}")

    if was_active:
        set_active_wiki(None)
        remaining = list_wikis()
        if remaining:
            print()
            return switch_wiki_flow()
        print(f"  {Y}no saved wikis. /switch-wiki to add one.{R}\n")

    return current_client


def manage_wikis_menu(current_client: WikiJSClient) -> WikiJSClient:
    """Run Manage Wikis submenu. Returns WikiJSClient (possibly rebuilt)."""
    print(SUBMENU)

    while True:
        choice = input("  > ").strip() or "0"

        if choice == "0":
            return current_client

        if choice == "1":
            return switch_wiki_flow()

        if choice == "2":
            return switch_wiki_flow("--new")

        if choice == "3":
            _list_profiles()
            continue

        if choice == "4":
            current_client = _remove_wiki_flow(current_client)
            print(SUBMENU)
            continue

        print(f"  {Y}invalid choice{R}")
