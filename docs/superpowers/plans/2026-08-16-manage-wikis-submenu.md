# Manage Wikis Submenu + Remove Confirmation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Main menu option 18 becomes a "Manage Wikis" submenu (switch / add / list / remove) with explicit confirmation before removing a wiki profile. AI assistant `/remove-wiki` also confirms and reports unknown names.

**Architecture:** New `wiki_cli/cli_wikis.py` owns the submenu UI. `cli_main.py` delegates option 18 to it. `ai/cli.py` `_cmd_remove_wiki` gains confirmation + unknown-name error. Storage layer (`wikis.py`) unchanged.

**Tech Stack:** Python 3.10+, `pathlib`, `input()` for prompts (paste-safe per recent fix).

## Global Constraints

- Confirm input: accept `y`, `Y`, `yes` (case-insensitive). Anything else cancels.
- Empty confirm input cancels.
- Option 18 menu label: `18. Manage Wikis` (replaces `18. Switch Wiki`).
- `remove_wiki()` storage primitive stays as no-op-on-missing. UI layer validates.
- After removing the active profile: clear `active_wiki.txt`; if other profiles remain, auto-prompt `switch_wiki_flow()`; if none, print "no saved wikis" hint.
- All wiki storage tests use `tmp_wiki_config` fixture (`wiki_cli.wikis.WIKIS_FILE` and `ACTIVE_FILE` redirected to `tmp_path`).
- Submenu option 4 (remove) skipped when `list_wikis()` is empty.
- Tests use `MagicMock(spec=WikiJSClient)` for client construction in fixtures.
- ANSI color codes: `R = "\033[0m"` reset, `D = "\033[2m"` dim, `Y = "\033[33m"` yellow (warn), `G = "\033[32m"` green (success), `B = "\033[1m"` bold, `C = "\033[36m"` cyan.

---

## Task 1: `manage_wikis_menu` + `_remove_wiki_flow`

**Files:**
- Create: `wiki_cli/cli_wikis.py`
- Create: `tests/cli_wikis/__init__.py`
- Create: `tests/cli_wikis/success.py`
- Create: `tests/test_cli_wikis.py`

**Interfaces this task produces:**
```python
# wiki_cli/cli_wikis.py
def manage_wikis_menu(current_client: WikiJSClient) -> WikiJSClient
def _remove_wiki_flow(current_client: WikiJSClient) -> WikiJSClient
```

- [ ] **Step 1.1: Write failing tests**

Create `tests/cli_wikis/__init__.py` (empty).

Create `tests/cli_wikis/success.py`:

```python
"""Tests for wiki_cli.cli_wikis module."""

from unittest.mock import MagicMock, patch

from wiki_cli.client import WikiJSClient
from wiki_cli import wikis
from wiki_cli.cli_wikis import manage_wikis_menu, _remove_wiki_flow

INPUT_PATCH = "builtins.input"


def _client(url="https://w.com/graphql"):
    c = MagicMock(spec=WikiJSClient)
    c.url = url
    return c


def test_manage_wikis_menu_back_returns_current(tmp_wiki_config, capsys):
    """Option 0 returns current client without changes."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    client = _client()
    with patch(INPUT_PATCH, side_effect=iter(["0"])):
        result = manage_wikis_menu(client)
    assert result is client
    out = capsys.readouterr().out
    assert "Manage Wikis" in out


def test_manage_wikis_menu_list_shows_active_marker(tmp_wiki_config, capsys):
    """Option 3 lists profiles with * marker on active."""
    wikis.save_wiki("work", "https://w.com/graphql", "k")
    wikis.save_wiki("home", "https://h.com/graphql", "k2")
    wikis.set_active_wiki("work")
    with patch(INPUT_PATCH, side_effect=iter(["3", "0"])):
        manage_wikis_menu(_client())
    out = capsys.readouterr().out
    assert "work" in out
    assert "home" in out


def test_manage_wikis_menu_remove_cancels_on_n(tmp_wiki_config, capsys):
    """Option 4 + 'n' confirm keeps profile."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    client = _client()
    inputs = iter(["4", "1", "n", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_manage_wikis_menu_remove_succeeds_on_y(tmp_wiki_config, capsys):
    """Option 4 + 'y' removes non-active profile."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    client = _client()
    # 4 = remove, 2 = pick profile "b", y = confirm, 0 = back
    inputs = iter(["4", "2", "y", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert wikis.get_wiki("b") is None
    assert wikis.get_active_wiki_name() == "a"
    assert result is client


def test_manage_wikis_menu_remove_active_rebuilds_via_switch(tmp_wiki_config, capsys):
    """Removing active profile triggers switch flow for remaining profiles."""
    wikis.save_wiki("work", "https://w.com/graphql", "k")
    wikis.save_wiki("home", "https://h.com/graphql", "k2")
    wikis.set_active_wiki("work")
    client = _client()
    new_client = _client("https://h.com/graphql")
    # 4 = remove, 1 = pick profile "work", y = confirm,
    # then switch flow: 1 = pick "home" from remaining, 0 = back
    inputs = iter(["4", "1", "y", "1", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_wikis.switch_wiki_flow", return_value=new_client):
            result = manage_wikis_menu(client)
    assert wikis.get_wiki("work") is None
    assert result is new_client


def test_manage_wikis_menu_remove_active_no_remaining(tmp_wiki_config, capsys):
    """Removing last profile clears active, returns current client."""
    wikis.save_wiki("only", "https://o.com/graphql", "k")
    wikis.set_active_wiki("only")
    client = _client()
    inputs = iter(["4", "1", "y", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert wikis.get_wiki("only") is None
    assert wikis.get_active_wiki_name() is None
    assert result is client


def test_remove_wiki_flow_unknown_name(tmp_wiki_config, capsys):
    """Pick index out of range prints error, no change."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    inputs = iter(["99", "0"])  # invalid picker index, then back
    with patch(INPUT_PATCH, side_effect=inputs):
        client = _client()
        result = _remove_wiki_flow(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "invalid" in out.lower() or "not found" in out.lower()


def test_remove_wiki_flow_cancel_option(tmp_wiki_config, capsys):
    """Picker option 'cancel' (last index) returns current client."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    inputs = iter(["2", "0"])  # 2 = cancel (1 profile + 1 cancel)
    with patch(INPUT_PATCH, side_effect=inputs):
        client = _client()
        result = _remove_wiki_flow(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
```

Create `tests/test_cli_wikis.py`:

```python
from cli_wikis.success import (
    test_manage_wikis_menu_back_returns_current as _back,
)
from cli_wikis.success import (
    test_manage_wikis_menu_list_shows_active_marker as _list,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_cancels_on_n as _cancel,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_succeeds_on_y as _ok,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_active_rebuilds_via_switch as _rebuild,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_active_no_remaining as _no_remaining,
)
from cli_wikis.success import (
    test_remove_wiki_flow_unknown_name as _unknown,
)
from cli_wikis.success import (
    test_remove_wiki_flow_cancel_option as _cancel_opt,
)


def test_back(capsys, tmp_wiki_config):
    _back(capsys)


def test_list(capsys, tmp_wiki_config):
    _list(capsys)


def test_cancel(capsys, tmp_wiki_config):
    _cancel(capsys)


def test_ok(capsys, tmp_wiki_config):
    _ok(capsys)


def test_rebuild(capsys, tmp_wiki_config):
    _rebuild(capsys)


def test_no_remaining(capsys, tmp_wiki_config):
    _no_remaining(capsys)


def test_unknown(capsys, tmp_wiki_config):
    _unknown(capsys)


def test_cancel_opt(capsys, tmp_wiki_config):
    _cancel_opt(capsys)
```

- [ ] **Step 1.2: Run tests — verify failure**

Run: `uv run pytest tests/test_cli_wikis.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'wiki_cli.cli_wikis'`.

- [ ] **Step 1.3: Implement `wiki_cli/cli_wikis.py`**

```python
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
            print(f"  {Y}invalid choice{R}")
            continue
        idx = int(choice)
        if idx == cancel_idx:
            print(f"  {D}cancelled{R}\n")
            return current_client
        if 1 <= idx <= len(names):
            target = names[idx - 1]
            break
        print(f"  {Y}invalid choice{R}")

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
```

- [ ] **Step 1.4: Run tests — verify pass**

Run: `uv run pytest tests/test_cli_wikis.py -v`
Expected: all pass.

- [ ] **Step 1.5: Commit**

```bash
git add wiki_cli/cli_wikis.py tests/cli_wikis/ tests/test_cli_wikis.py
git commit -m "feat(cli): manage wikis submenu with remove confirmation"
```

---

## Task 2: `cli_main` option 18 relabel + delegate

**Files:**
- Modify: `wiki_cli/cli_main.py:57` (menu label)
- Modify: `wiki_cli/cli_main.py:89-92, 112` (handler + dispatch)
- Modify: `tests/main_menu/success.py` (rename test, update mocks)

- [ ] **Step 2.1: Update existing main-menu test mocks**

In `tests/main_menu/success.py`, replace the entire file:

```python
from unittest.mock import patch, MagicMock

from wiki_cli.cli_main import main
from wiki_cli import WikiJSError
from wiki_cli.client import WikiJSClient

INPUT_PATCH = "builtins.input"


def _client():
    c = MagicMock(spec=WikiJSClient)
    c.url = "https://w.com/graphql"
    return c


def test_menu_exit(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()
    output = capsys.readouterr().out
    assert "Goodbye!" in output
    print(f"\n  [MENU] Exit")


def test_menu_invalid_option(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["99", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()
    output = capsys.readouterr().out
    assert "Invalid option. Try again." in output
    print(f"\n  [MENU] Invalid option handled")


def test_menu_dispatches_handler(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["1", "", "", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                with patch("wiki_cli.cli_main.create_page") as mock_create:
                    main()
    mock_create.assert_called_once()
    print(f"\n  [MENU] Handler dispatched")


def test_menu_handles_error(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["16", "", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                with patch(
                    "wiki_cli.cli_main.test_connection",
                    side_effect=WikiJSError("Conn failed"),
                ):
                    main()
    output = capsys.readouterr().err
    assert "Error: Conn failed" in output
    print(f"\n  [MENU] WikiJSError handled gracefully")


def test_menu_option_18_label(capsys, tmp_wiki_config):
    """Verify the menu displays 'Manage Wikis' for option 18."""
    with patch(INPUT_PATCH, side_effect=iter(["0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()
    output = capsys.readouterr().out
    assert "Manage Wikis" in output
    assert "Switch Wiki" not in output
    print(f"\n  [MENU] Option 18 labeled 'Manage Wikis'")


def test_menu_manage_wikis_rebuilds(capsys, tmp_wiki_config):
    """Option 18 delegates to manage_wikis_menu and rebuilds client."""
    new_client = MagicMock(spec=WikiJSClient)
    new_client.url = "https://new.com/graphql"
    with patch(INPUT_PATCH, side_effect=iter(["18", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager") as mock_pm:
                with patch(
                    "wiki_cli.cli_main.manage_wikis_menu",
                    return_value=new_client,
                ) as mock_manage:
                    main()
    mock_manage.assert_called_once()
    assert mock_pm.call_count == 2
    output = capsys.readouterr().out
    assert "Manage Wikis" in output
    print(f"\n  [MENU] Option 18 delegates to manage_wikis_menu")
```

Also update `tests/test_main_menu.py` to add wrappers for the two new tests:

```python
from main_menu.success import test_menu_exit as _exit
from main_menu.success import test_menu_invalid_option as _invalid
from main_menu.success import test_menu_dispatches_handler as _dispatch
from main_menu.success import test_menu_handles_error as _error
from main_menu.success import test_menu_option_18_label as _label
from main_menu.success import test_menu_manage_wikis_rebuilds as _manage


def test_menu_exit(capsys, tmp_wiki_config):
    _exit(capsys, tmp_wiki_config)


def test_menu_invalid_option(capsys, tmp_wiki_config):
    _invalid(capsys, tmp_wiki_config)


def test_menu_dispatches_handler(capsys, tmp_wiki_config):
    _dispatch(capsys, tmp_wiki_config)


def test_menu_handles_error(capsys, tmp_wiki_config):
    _error(capsys, tmp_wiki_config)


def test_menu_option_18_label(capsys, tmp_wiki_config):
    _label(capsys, tmp_wiki_config)


def test_menu_manage_wikis_rebuilds(capsys, tmp_wiki_config):
    _manage(capsys, tmp_wiki_config)
```

- [ ] **Step 2.2: Update `wiki_cli/cli_main.py`**

Three edits:

**Edit 1** — replace import line `from wiki_cli.wikis import get_active_client, switch_wiki_flow`:

```python
from wiki_cli.wikis import get_active_client, switch_wiki_flow
```

becomes:

```python
from wiki_cli.cli_wikis import manage_wikis_menu
from wiki_cli.wikis import get_active_client, switch_wiki_flow
```

**Edit 2** — menu label. Replace line `  18. Switch Wiki` with:

```
  18. Manage Wikis
```

**Edit 3** — handler + dispatch. Replace `_switch_wiki()` definition and the `"18"` entry:

```python
    def _manage_wikis() -> None:
        nonlocal client, pages
        client = manage_wikis_menu(client)
        pages = PagesManager(client)

    handlers = {
        ...
        "18": ("Manage Wikis", _manage_wikis),
    }
```

The full handler dict remains the same except `"18"`.

- [ ] **Step 2.3: Run focused test**

Run: `uv run pytest tests/test_main_menu.py tests/main_menu/ tests/test_cli_wikis.py -v`
Expected: all pass.

- [ ] **Step 2.4: Run full suite**

Run: `uv run pytest tests/ --tb=short -q 2>&1 | tail -10`
Expected: all green (98+ tests, 0 failed).

- [ ] **Step 2.5: Commit**

```bash
git add wiki_cli/cli_main.py tests/main_menu/success.py tests/test_main_menu.py
git commit -m "feat(cli): rename option 18 to Manage Wikis and delegate"
```

---

## Task 3: AI assistant `_cmd_remove_wiki` confirm + unknown error

**Files:**
- Modify: `wiki_cli/ai/cli.py` (`_cmd_remove_wiki` body + help text)
- Create: `tests/test_ai_cli.py` (new tests)
- Create: `tests/ai_cli/__init__.py` (empty)
- Create: `tests/ai_cli/success.py` (test bodies)

- [ ] **Step 3.1: Write failing tests**

Create `tests/ai_cli/__init__.py` (empty).

Create `tests/ai_cli/success.py`:

```python
"""Tests for AI assistant slash command handlers."""

from unittest.mock import patch, MagicMock

from wiki_cli import wikis
from wiki_cli.ai.cli import _cmd_remove_wiki
from wiki_cli.pages import PagesManager

INPUT_PATCH = "builtins.input"


def _agent():
    a = MagicMock()
    a.wiki_client = MagicMock()
    a.wiki_client.url = "https://w.com/graphql"
    a.pages = MagicMock(spec=PagesManager)
    return a


def test_ai_remove_wiki_unknown_name_no_change(capsys, tmp_wiki_config):
    """Unknown name prints error, no state change."""
    wikis.save_wiki("real", "https://r.com/graphql", "k")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["ghost"])):
        _cmd_remove_wiki(agent, "ghost")
    assert wikis.get_wiki("real") is not None
    assert wikis.get_wiki("ghost") is None
    out = capsys.readouterr().out
    assert "not found" in out.lower()


def test_ai_remove_wiki_cancels_on_n(capsys, tmp_wiki_config):
    """User types 'n' to confirm — no removal."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["n"])):
        _cmd_remove_wiki(agent, "a")
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_ai_remove_wiki_succeeds_on_y(capsys, tmp_wiki_config):
    """User types 'y' — non-active profile removed."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["y"])):
        _cmd_remove_wiki(agent, "b")
    assert wikis.get_wiki("b") is None
    assert wikis.get_active_wiki_name() == "a"
    out = capsys.readouterr().out
    assert "removed" in out.lower()


def test_ai_remove_wiki_default_target_is_active(capsys, tmp_wiki_config):
    """Empty arg defaults to active wiki."""
    wikis.save_wiki("active", "https://a.com/graphql", "k")
    wikis.set_active_wiki("active")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["n"])):
        _cmd_remove_wiki(agent, "")
    assert wikis.get_wiki("active") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_ai_remove_wiki_accepts_yes(capsys, tmp_wiki_config):
    """User types 'yes' (full word) — confirm succeeds."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["yes"])):
        _cmd_remove_wiki(agent, "b")
    assert wikis.get_wiki("b") is None
```

Create `tests/test_ai_cli.py`:

```python
from ai_cli.success import (
    test_ai_remove_wiki_unknown_name_no_change as _unknown,
)
from ai_cli.success import (
    test_ai_remove_wiki_cancels_on_n as _cancel,
)
from ai_cli.success import (
    test_ai_remove_wiki_succeeds_on_y as _ok,
)
from ai_cli.success import (
    test_ai_remove_wiki_default_target_is_active as _default,
)
from ai_cli.success import (
    test_ai_remove_wiki_accepts_yes as _yes,
)


def test_unknown(capsys, tmp_wiki_config):
    _unknown(capsys, tmp_wiki_config)


def test_cancel(capsys, tmp_wiki_config):
    _cancel(capsys, tmp_wiki_config)


def test_ok(capsys, tmp_wiki_config):
    _ok(capsys, tmp_wiki_config)


def test_default(capsys, tmp_wiki_config):
    _default(capsys, tmp_wiki_config)


def test_yes(capsys, tmp_wiki_config):
    _yes(capsys, tmp_wiki_config)
```

- [ ] **Step 3.2: Run tests — verify failure**

Run: `uv run pytest tests/test_ai_cli.py -v`
Expected: FAIL (existing `_cmd_remove_wiki` silently succeeds on unknown name).

- [ ] **Step 3.3: Update `_cmd_remove_wiki` in `wiki_cli/ai/cli.py`**

Find the existing `_cmd_remove_wiki` function (around line 360). Replace its body with:

```python
def _cmd_remove_wiki(agent: WikiAgent, arg: str) -> None:
    from wiki_cli.wikis import get_active_wiki_name, set_active_wiki

    target = arg.strip() or get_active_wiki_name()
    if not target:
        print(f"  {Y}no wiki specified and no active wiki{R}\n")
        return

    entry = wikis.get_wiki(target)
    if not entry:
        print(f"  {Y}wiki '{target}' not found{R}\n")
        return

    ans = input(f"  remove '{target}' ({entry['url']})? [y/n]: ").strip().lower()
    if ans not in ("y", "yes"):
        print(f"  {D}cancelled{R}\n")
        return

    wikis.remove_wiki(target)

    if get_active_wiki_name() == target:
        set_active_wiki(None)
        agent.wiki_client = None
        agent.pages = None
        remaining = wikis.list_wikis()
        if remaining:
            new_client = switch_wiki_flow()
            agent.wiki_client = new_client
            agent.pages = PagesManager(new_client)
        else:
            print(f"  {Y}no saved wikis. /switch-wiki to add one.{R}\n")

    print(f"  {G}removed → {target}{R}\n")
```

Note: the existing top-level import block already imports `get_active_client`, `list_wikis`, `remove_wiki`, `switch_wiki_flow`. Add `get_wiki`, `get_active_wiki_name`, `set_active_wiki` if not present. Check the existing import block (around line 31 in `wiki_cli/ai/cli.py`) and add missing names from `wiki_cli.wikis`.

Also update the `_cmd_help` body to add the confirm hint to the `/remove-wiki` line:

Replace the `/remove-wiki` line in `_cmd_help`:

```python
    {C}/remove-wiki{R}    remove a wiki profile (/remove-wiki [name])
```

with:

```python
    {C}/remove-wiki{R}    remove a wiki profile (asks to confirm)
```

- [ ] **Step 3.4: Run tests — verify pass**

Run: `uv run pytest tests/test_ai_cli.py -v`
Expected: all pass.

- [ ] **Step 3.5: Run full suite**

Run: `uv run pytest tests/ --tb=short -q 2>&1 | tail -10`
Expected: all green.

- [ ] **Step 3.6: Commit**

```bash
git add wiki_cli/ai/cli.py tests/ai_cli/ tests/test_ai_cli.py
git commit -m "feat(ai): /remove-wiki confirms and errors on unknown name"
```

---

## Task 4: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 4.1: Update README — Configuration section**

In `README.md`, find the Configuration section. Update the "Switching wikis" bullet list to reflect new submenu shape. The current bullets read:

```
**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create)
- From the main menu: option `18. Switch Wiki`
- List profiles: `/wikis`
- Remove a profile: `/remove-wiki [name]`
```

Replace with:

```
**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create)
- From the main menu: option `18. Manage Wikis` (submenu with switch / add / list / remove)
- List profiles: `/wikis` or main menu option `18 → 3`
- Remove a profile: `/remove-wiki [name]` or main menu option `18 → 4` (both ask to confirm)
```

- [ ] **Step 4.2: Update AI Commands table**

The existing table has:

```
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (`/remove-wiki [name]`) |
```

Update the `/remove-wiki` row description:

```
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
```

- [ ] **Step 4.3: Verify no broken references**

Run: `uv run pytest tests/ --tb=short -q 2>&1 | tail -5`
Expected: still green.

- [ ] **Step 4.4: Commit**

```bash
git add README.md
git commit -m "docs: update README for Manage Wikis submenu + remove confirm"
```

---

## Self-Review

**Spec coverage:**
- Submenu under option 18 → Task 1 (`manage_wikis_menu`)
- Option 18 relabel → Task 2
- Confirm before delete → Tasks 1, 3
- Fix silent-success bug → Task 3 (unknown name → error)
- Remove active profile → Tasks 1, 3 (clear active + rebuild via switch flow)
- New `wiki_cli/cli_wikis.py` → Task 1
- `_cmd_remove_wiki` updates → Task 3
- README updates → Task 4
- Tests: `tests/cli_wikis/` (Task 1), `tests/test_cli_wikis.py` (Task 1), main menu tests updated (Task 2), `tests/ai_cli/` + `tests/test_ai_cli.py` (Task 3)

**Placeholder scan:** No TBDs. Every step has actual code.

**Type consistency:**
- `manage_wikis_menu(current_client) -> WikiJSClient` defined Task 1, consumed Task 2.
- `_remove_wiki_flow(current_client) -> WikiJSClient` defined Task 1, used internally only.
- `_cmd_remove_wiki(agent, arg)` signature unchanged in Task 3.
- `switch_wiki_flow()` and `wikis.get_wiki/get_active_wiki_name/set_active_wiki/list_wikis/remove_wiki` used consistently.
- ANSI color codes consistent with existing `wiki_cli/ai/cli.py` style.
