# Multi-Wiki Profile Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace single-wiki env-var config with named profiles. Users can store multiple Wiki.js instances at `~/.config/wiki-cli/wikis.json` and switch from the main menu (option 18) or the AI assistant (`/switch-wiki`).

**Architecture:** New `wiki_cli/wikis.py` owns profile storage + active-client resolution. `WikiJSClient` becomes a pure transport (requires `url` + `api_key` as args). `WikiAgent` accepts an injected client. Both CLI entry points (`cli_main.main`, `ai/cli.ai_mode`) resolve an active client at startup and rebuild it on switch.

**Tech Stack:** Python 3.10+, `pathlib`, `getpass`, `json`, existing `WikiJSClient`/`PagesManager`/`WikiAgent`.

## Global Constraints

- Storage paths: `~/.config/wiki-cli/wikis.json` and `~/.config/wiki-cli/active_wiki.txt`, both `chmod 0600`.
- Profile name: non-empty after strip, no whitespace inside, case-insensitive uniqueness.
- URL: non-empty, must start with `http://` or `https://`, exact-match uniqueness.
- API key: non-empty after strip, captured via `getpass.getpass` (no echo).
- `.env` / `.env.example` no longer carry `WIKIJS_URL` / `WIKIJS_API_KEY`.
- `WikiJSClient.__init__` signature: `(self, url: str, api_key: str)` — both required, no env fallback.
- Tests use `tmp_path` + `monkeypatch` to redirect storage paths; never touch real `~/.config/wiki-cli`.

---

## Task 1: Profile storage layer

**Files:**
- Create: `wiki_cli/wikis.py`
- Test: `tests/test_wikis.py`

**Interfaces this task produces** (consumed by later tasks):
```python
def list_wikis() -> dict[str, dict[str, str]]      # name -> {url, api_key}
def get_wiki(name: str) -> dict[str, str] | None
def save_wiki(name: str, url: str, api_key: str) -> None
def remove_wiki(name: str) -> None
def get_active_wiki_name() -> str | None
def set_active_wiki(name: str | None) -> None
```

Paths exposed as module-level variables that tests can monkeypatch:
```python
WIKIS_FILE: Path
ACTIVE_FILE: Path
```

- [ ] **Step 1.1: Write failing tests**

Create `tests/test_wikis.py`:

```python
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wiki_cli import wikis
from wiki_cli.exceptions import WikiJSError


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    f1 = tmp_path / "wikis.json"
    f2 = tmp_path / "active_wiki.txt"
    monkeypatch.setattr(wikis, "WIKIS_FILE", f1)
    monkeypatch.setattr(wikis, "ACTIVE_FILE", f2)
    return f1, f2


def test_list_wikis_empty(tmp_config):
    assert wikis.list_wikis() == {}


def test_save_and_get_wiki(tmp_config):
    wikis.save_wiki("work", "https://w.work.com/graphql", "secret1")
    assert wikis.get_wiki("work") == {
        "url": "https://w.work.com/graphql",
        "api_key": "secret1",
    }
    assert "work" in wikis.list_wikis()


def test_save_wiki_creates_file_with_mode_0600(tmp_config):
    f1, _ = tmp_config
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    assert f1.exists()
    assert oct(f1.stat().st_mode & 0o777) == "0o600"


def test_save_wiki_rejects_duplicate_name_case_insensitive(tmp_config):
    wikis.save_wiki("Work", "https://w.com/graphql", "k")
    with pytest.raises(WikiJSError, match="already exists"):
        wikis.save_wiki("work", "https://other.com/graphql", "k2")


def test_save_wiki_rejects_duplicate_url(tmp_config):
    wikis.save_wiki("a", "https://same.com/graphql", "k")
    with pytest.raises(WikiJSError, match="url already saved"):
        wikis.save_wiki("b", "https://same.com/graphql", "k2")


def test_save_wiki_rejects_empty_name(tmp_config):
    with pytest.raises(WikiJSError, match="name required"):
        wikis.save_wiki("  ", "https://x.com/graphql", "k")


def test_save_wiki_rejects_name_with_whitespace(tmp_config):
    with pytest.raises(WikiJSError, match="no spaces"):
        wikis.save_wiki("my work", "https://x.com/graphql", "k")


def test_save_wiki_rejects_url_without_scheme(tmp_config):
    with pytest.raises(WikiJSError, match="http"):
        wikis.save_wiki("a", "wikijs.com/graphql", "k")


def test_save_wiki_rejects_empty_key(tmp_config):
    with pytest.raises(WikiJSError, match="api key required"):
        wikis.save_wiki("a", "https://x.com/graphql", "  ")


def test_remove_wiki(tmp_config):
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.remove_wiki("a")
    assert wikis.get_wiki("a") is None


def test_remove_wiki_missing_is_noop(tmp_config):
    wikis.remove_wiki("ghost")  # no raise


def test_set_and_get_active_wiki(tmp_config):
    assert wikis.get_active_wiki_name() is None
    wikis.set_active_wiki("work")
    assert wikis.get_active_wiki_name() == "work"


def test_active_file_permissions(tmp_config):
    _, f2 = tmp_config
    wikis.set_active_wiki("x")
    assert oct(f2.stat().st_mode & 0o777) == "0o600"


def test_set_active_wiki_none_clears(tmp_config):
    wikis.set_active_wiki("a")
    wikis.set_active_wiki(None)
    assert wikis.get_active_wiki_name() is None


def test_load_corrupt_json_returns_empty(tmp_config):
    f1, _ = tmp_config
    f1.write_text("{not json")
    assert wikis.list_wikis() == {}
```

- [ ] **Step 1.2: Run tests — verify failure**

Run: `pytest tests/test_wikis.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'wiki_cli.wikis'` (or `ImportError`).

- [ ] **Step 1.3: Implement `wiki_cli/wikis.py`**

```python
"""Wiki.js profile storage and active-client resolution.

Files (under ~/.config/wiki-cli/):
  - wikis.json         {name: {url, api_key}}   mode 0600
  - active_wiki.txt    single-line profile name  mode 0600
"""

from __future__ import annotations

import json
from pathlib import Path

from wiki_cli.exceptions import WikiJSError

WIKIS_DIR = Path.home() / ".config" / "wiki-cli"
WIKIS_FILE = WIKIS_DIR / "wikis.json"
ACTIVE_FILE = WIKIS_DIR / "active_wiki.txt"


def _ensure_mode(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _load_wikis() -> dict[str, dict[str, str]]:
    if not WIKIS_FILE.exists():
        return {}
    try:
        data = json.loads(WIKIS_FILE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_wikis(data: dict[str, dict[str, str]]) -> None:
    WIKIS_DIR.mkdir(parents=True, exist_ok=True)
    WIKIS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    _ensure_mode(WIKIS_FILE)


def list_wikis() -> dict[str, dict[str, str]]:
    """Return all saved wiki profiles."""
    return _load_wikis()


def get_wiki(name: str) -> dict[str, str] | None:
    """Return the profile named *name*, or None."""
    return _load_wikis().get(name)


def _validate(name: str, url: str, api_key: str) -> None:
    if not name or not name.strip():
        raise WikiJSError("name required")
    if any(ch.isspace() for ch in name):
        raise WikiJSError("name has no spaces allowed")
    if not url or not url.strip():
        raise WikiJSError("url required")
    stripped = url.strip()
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        raise WikiJSError("url must start with http:// or https://")
    if not api_key or not api_key.strip():
        raise WikiJSError("api key required")


def save_wiki(name: str, url: str, api_key: str) -> None:
    """Create or overwrite a named wiki profile. Rejects duplicates by name or URL."""
    _validate(name, url, api_key)
    name = name.strip()
    url = url.strip()
    api_key = api_key.strip()

    data = _load_wikis()

    if name.lower() in {k.lower() for k in data}:
        raise WikiJSError(f"wiki '{name}' already exists")

    for existing_name, entry in data.items():
        if entry.get("url") == url:
            raise WikiJSError(f"url already saved as '{existing_name}'")

    data[name] = {"url": url, "api_key": api_key}
    _save_wikis(data)


def remove_wiki(name: str) -> None:
    """Remove a profile by name. No-op if absent."""
    data = _load_wikis()
    if name in data:
        del data[name]
        _save_wikis(data)


def get_active_wiki_name() -> str | None:
    """Return the active profile name, or None."""
    if not ACTIVE_FILE.exists():
        return None
    name = ACTIVE_FILE.read_text().strip()
    return name or None


def set_active_wiki(name: str | None) -> None:
    """Persist the active profile name. Pass None to clear."""
    WIKIS_DIR.mkdir(parents=True, exist_ok=True)
    if name is None:
        ACTIVE_FILE.write_text("")
    else:
        ACTIVE_FILE.write_text(name + "\n")
    _ensure_mode(ACTIVE_FILE)
```

- [ ] **Step 1.4: Run tests — verify pass**

Run: `pytest tests/test_wikis.py -v`
Expected: all pass.

- [ ] **Step 1.5: Commit**

```bash
git add wiki_cli/wikis.py tests/test_wikis.py
git commit -m "feat(wikis): named profile storage with validation"
```

---

## Task 2: Active client resolver + `switch_wiki_flow`

**Files:**
- Modify: `wiki_cli/wikis.py`
- Test: `tests/test_wikis.py` (extend)

**Interfaces this task adds:**
```python
def get_active_client() -> WikiJSClient
def switch_wiki_flow(arg: str = "") -> WikiJSClient
```

- [ ] **Step 2.1: Write failing tests**

Append to `tests/test_wikis.py`:

```python
def test_get_active_client_raises_when_none(tmp_config):
    with pytest.raises(WikiJSError, match="no active wiki"):
        wikis.get_active_client()


def test_get_active_client_raises_when_active_missing(tmp_config):
    _, f2 = tmp_config
    f2.write_text("ghost")
    with pytest.raises(WikiJSError, match="no active wiki"):
        wikis.get_active_client()


def test_get_active_client_returns_client(tmp_config):
    wikis.save_wiki("w", "https://w.com/graphql", "k")
    wikis.set_active_wiki("w")
    client = wikis.get_active_client()
    assert client.url == "https://w.com/graphql"
    assert client.api_key == "k"


def test_switch_wiki_flow_jumps_to_named(tmp_config, capsys):
    wikis.save_wiki("work", "https://work.com/graphql", "wk")
    client = wikis.switch_wiki_flow("work")
    assert client.url == "https://work.com/graphql"
    assert wikis.get_active_wiki_name() == "work"
    out = capsys.readouterr().out
    assert "work" in out


def test_switch_wiki_flow_named_missing_no_state_change(tmp_config, capsys):
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.set_active_wiki("a")
    with pytest.raises(WikiJSError):
        wikis.switch_wiki_flow("ghost")
    assert wikis.get_active_wiki_name() == "a"


def test_switch_wiki_flow_new_creates_profile(tmp_config):
    inputs = iter(["work", "https://work.com/graphql", "secret"])
    with patch("builtins.input", side_effect=inputs):
        with patch("wiki_cli.wikis.getpass.getpass", return_value="secret"):
            client = wikis.switch_wiki_flow("--new")
    assert wikis.get_active_wiki_name() == "work"
    assert client.url == "https://work.com/graphql"
    assert wikis.get_wiki("work")["api_key"] == "secret"


def test_switch_wiki_flow_interactive_picks_existing(tmp_config):
    wikis.save_wiki("a", "https://a.com/graphql", "ka")
    inputs = iter(["1"])  # pick "a"
    with patch("builtins.input", side_effect=inputs):
        client = wikis.switch_wiki_flow()
    assert client.url == "https://a.com/graphql"
    assert wikis.get_active_wiki_name() == "a"
```

- [ ] **Step 2.2: Run new tests — verify failure**

Run: `pytest tests/test_wikis.py -v -k "get_active_client or switch_wiki_flow"`
Expected: FAIL (`AttributeError`).

- [ ] **Step 2.3: Add `get_active_client` + `switch_wiki_flow` to `wiki_cli/wikis.py`**

Append:

```python
import getpass


def get_active_client():
    """Return a WikiJSClient for the active profile. Raises WikiJSError if none."""
    from wiki_cli.client import WikiJSClient

    name = get_active_wiki_name()
    if not name:
        raise WikiJSError("no active wiki. run /switch-wiki to configure one.")
    entry = get_wiki(name)
    if not entry:
        raise WikiJSError(
            f"active wiki '{name}' not found. run /switch-wiki to reconfigure."
        )
    return WikiJSClient(url=entry["url"], api_key=entry["api_key"])


def _prompt_new_profile() -> tuple[str, str, str]:
    while True:
        name = input("  name: ").strip()
        if not name:
            print("  required")
            continue
        if any(ch.isspace() for ch in name):
            print("  no spaces allowed")
            continue
        break

    while True:
        url = input("  url: ").strip()
        if url.startswith("http://") or url.startswith("https://"):
            break
        print("  url must start with http:// or https://")

    while True:
        api_key = getpass.getpass("  api key: ").strip()
        if api_key:
            return name, url, api_key
        print("  required")

    return "", "", ""  # unreachable


def switch_wiki_flow(arg: str = "") -> "WikiJSClient":
    """Interactive wiki switcher. Returns a freshly-built WikiJSClient.

    Args:
        arg: "" → interactive picker. "<name>" → jump to that profile.
             "--new" → force new-profile flow.
    """
    from wiki_cli.client import WikiJSClient

    if arg == "--new":
        name, url, api_key = _prompt_new_profile()
        save_wiki(name, url, api_key)
        set_active_wiki(name)
        print(f"  saved → active: {name}")
        return WikiJSClient(url=url, api_key=api_key)

    if arg:
        entry = get_wiki(arg)
        if not entry:
            raise WikiJSError(f"wiki '{arg}' not found")
        set_active_wiki(arg)
        print(f"  switched → {arg}")
        return WikiJSClient(url=entry["url"], api_key=entry["api_key"])

    data = list_wikis()
    names = sorted(data.keys())

    if names:
        print("  saved wikis:")
        for i, n in enumerate(names, 1):
            print(f"    {i}    {n:<16} {data[n]['url']}")
        print(f"    {len(names) + 1}    add new")
        print()
        while True:
            choice = input("  > ").strip() or "1"
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(names):
                    picked = names[idx - 1]
                    set_active_wiki(picked)
                    print(f"  switched → {picked}")
                    entry = data[picked]
                    return WikiJSClient(url=entry["url"], api_key=entry["api_key"])
                if idx == len(names) + 1:
                    break
            print("  invalid choice")
    else:
        print("  no saved wikis")

    name, url, api_key = _prompt_new_profile()
    save_wiki(name, url, api_key)
    set_active_wiki(name)
    print(f"  saved → active: {name}")
    return WikiJSClient(url=url, api_key=api_key)
```

Also re-export from `wiki_cli/__init__.py`. Edit `wiki_cli/__init__.py`:

```python
from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError
from wiki_cli.models import Page, PageResponse, PageHistory, PageVersion
from wiki_cli.pages import PagesManager
from wiki_cli.wikis import switch_wiki_flow
from wiki_cli.cli_main import main

__all__ = [
    "WikiJSClient",
    "WikiJSError",
    "Page",
    "PageResponse",
    "PageHistory",
    "PageVersion",
    "PagesManager",
    "switch_wiki_flow",
    "main",
]
__version__ = "0.1.0"
```

- [ ] **Step 2.4: Run tests — verify pass**

Run: `pytest tests/test_wikis.py -v`
Expected: all pass.

- [ ] **Step 2.5: Commit**

```bash
git add wiki_cli/wikis.py wiki_cli/__init__.py tests/test_wikis.py
git commit -m "feat(wikis): active client resolver and interactive switcher"
```

---

## Task 3: `WikiJSClient` drops env, requires args

**Files:**
- Modify: `wiki_cli/client.py`

**Signature change:** `WikiJSClient(url: str, api_key: str)` — both required.

- [ ] **Step 3.1: Update `wiki_cli/client.py`**

Replace contents of `wiki_cli/client.py`:

```python
"""Core Wiki.js GraphQL client using the gql library."""

from __future__ import annotations

from typing import Any

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from wiki_cli.exceptions import WikiJSError


class WikiJSClient:
    """Manages the gql client, authentication, and query execution for Wiki.js.

    Attributes:
        url: The GraphQL endpoint URL.
        api_key: The API key used for Bearer auth.
        client: The underlying gql Client instance.
    """

    def __init__(self, url: str, api_key: str) -> None:
        if not url or not url.strip():
            raise WikiJSError("url is required")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise WikiJSError("url must start with http:// or https://")
        if not api_key or not api_key.strip():
            raise WikiJSError("api_key is required")

        self.url = url
        self.api_key = api_key

        transport = RequestsHTTPTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            verify=True,
            retries=3,
        )

        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def execute(
        self,
        query: str,
        variable_values: dict[str, Any] | None = None,
        operation_name: str | None = None,
        upload_files: bool = False,
    ) -> dict[str, Any]:
        """Execute a GraphQL operation against the Wiki.js API."""
        document = gql(query)

        if variable_values:
            document.variable_values = variable_values

        try:
            result = self.client.execute(
                document,
                operation_name=operation_name,
                upload_files=upload_files,
            )
        except Exception as exc:
            raise WikiJSError(f"GraphQL request failed: {exc}") from exc

        if isinstance(result, dict) and "errors" in result:
            raise WikiJSError(
                "GraphQL returned errors",
                errors=result["errors"],
            )

        return result
```

- [ ] **Step 3.2: Verify client still works in isolation**

Create scratch file at `/tmp/opencode/client_smoke.py`:

```python
from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError

c = WikiJSClient("https://x.com/graphql", "k")
assert c.url == "https://x.com/graphql"

for bad in [
    ("", "k"),
    ("x.com/g", "k"),
    ("https://x.com/graphql", ""),
]:
    try:
        WikiJSClient(*bad)
        assert False, f"should have raised for {bad}"
    except WikiJSError:
        pass

print("OK")
```

Run: `python /tmp/opencode/client_smoke.py`
Expected: prints `OK`.

- [ ] **Step 3.3: Commit**

```bash
git add wiki_cli/client.py
git commit -m "refactor(client): drop env loading, require url+api_key args"
```

---

## Task 4: `WikiAgent` accepts injected wiki client

**Files:**
- Modify: `wiki_cli/ai/agent.py`

- [ ] **Step 4.1: Update `WikiAgent.__init__`**

In `wiki_cli/ai/agent.py`, replace the `__init__` method (currently lines 66–74):

```python
    def __init__(
        self,
        config: AIConfig | None = None,
        wiki_client: WikiJSClient | None = None,
    ) -> None:
        self.config = config or AIConfig()
        if wiki_client is None:
            from wiki_cli.wikis import get_active_client

            self.wiki_client = get_active_client()
        else:
            self.wiki_client = wiki_client
        self.pages = PagesManager(self.wiki_client)
        self.client = self.config.get_client()
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.quiet = False
```

- [ ] **Step 4.2: Run existing test suite to surface regressions**

Run: `pytest tests/ -v --tb=short 2>&1 | tail -50`
Expected: existing tests should mostly pass (they use `MagicMock(spec=WikiJSClient)` or build `WikiJSClient` with positional args — none currently call `WikiJSClient()` with no args).

- [ ] **Step 4.3: Commit**

```bash
git add wiki_cli/ai/agent.py
git commit -m "refactor(agent): accept injected wiki_client, resolve active by default"
```

---

## Task 5: `cli_main` integration (startup + menu option 18)

**Files:**
- Modify: `wiki_cli/cli_main.py`
- Modify: `tests/main_menu/success.py` (update mocks for new startup path)
- Modify: `tests/conftest.py` (add `tmp_wiki_config` fixture)

- [ ] **Step 5.1: Add `tmp_wiki_config` fixture to `tests/conftest.py`**

Append to `tests/conftest.py`:

```python
import pytest

from wiki_cli import wikis


@pytest.fixture
def tmp_wiki_config(tmp_path, monkeypatch):
    f1 = tmp_path / "wikis.json"
    f2 = tmp_path / "active_wiki.txt"
    monkeypatch.setattr(wikis, "WIKIS_FILE", f1)
    monkeypatch.setattr(wikis, "ACTIVE_FILE", f2)
    return f1, f2
```

- [ ] **Step 5.2: Update `wiki_cli/cli_main.py`**

Replace the entire file:

```python
"""Main menu loop."""

from __future__ import annotations

import sys

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.pages import PagesManager
from wiki_cli.wikis import get_active_client, switch_wiki_flow

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
  18. Switch Wiki

  --- AI ---
  17. AI Assistant
  0. Exit
========================================
"""


def _ai_assistant() -> None:
    from wiki_cli.ai.cli import ai_mode

    ai_mode()


def _bootstrap_client() -> tuple[WikiJSClient, PagesManager]:
    """Return an active client + pages manager. Runs switch flow if none set."""
    try:
        client = get_active_client()
    except WikiJSError:
        print("No active wiki configured.")
        client = switch_wiki_flow()
    return client, PagesManager(client)


def main() -> None:
    try:
        client, pages = _bootstrap_client()
    except WikiJSError as exc:
        print(f"Error initializing client: {exc}", file=sys.stderr)
        sys.exit(1)

    def _switch_wiki() -> None:
        nonlocal client, pages
        client = switch_wiki_flow()
        pages = PagesManager(client)

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
        "18": ("Switch Wiki", _switch_wiki),
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
        except (EOFError, KeyboardInterrupt):
            print("Cancelled.", file=sys.stderr)

        input("\nPress Enter to continue...")
```

- [ ] **Step 5.3: Update existing main-menu tests**

Replace `tests/main_menu/success.py`:

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
    wikis_save = MagicMock()
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
                with patch("wiki_cli.cli_main.test_connection", side_effect=WikiJSError("Conn failed")):
                    main()
    output = capsys.readouterr().err
    assert "Error: Conn failed" in output
    print(f"\n  [MENU] WikiJSError handled gracefully")


def test_menu_switch_wiki_rebuilds(capsys, tmp_wiki_config):
    new_client = MagicMock(spec=WikiJSClient)
    new_client.url = "https://new.com/graphql"
    with patch(INPUT_PATCH, side_effect=iter(["18", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager") as mock_pm:
                with patch("wiki_cli.cli_main.switch_wiki_flow", return_value=new_client) as mock_sw:
                    main()
    mock_sw.assert_called_once()
    output = capsys.readouterr().out
    assert "Switch Wiki" in output
    print(f"\n  [MENU] Switch wiki rebuilds client")
```

- [ ] **Step 5.4: Run menu tests**

Run: `pytest tests/test_main_menu.py tests/main_menu/ -v`
Expected: all pass.

- [ ] **Step 5.5: Commit**

```bash
git add wiki_cli/cli_main.py tests/main_menu/success.py tests/conftest.py
git commit -m "feat(cli): switch wiki from main menu option 18"
```

---

## Task 6: AI assistant slash commands + startup

**Files:**
- Modify: `wiki_cli/ai/cli.py`

- [ ] **Step 6.1: Add slash commands to `wiki_cli/ai/cli.py`**

Three edits to `wiki_cli/ai/cli.py`:

**Edit 1** — add imports near the top (after the existing `from wiki_cli.ai.config import ...` block, around line 29):

```python
from wiki_cli.wikis import (
    get_active_client,
    list_wikis,
    remove_wiki,
    switch_wiki_flow,
)
```

**Edit 2** — extend `_cmd_help()` to include the new commands. Replace its body:

```python
def _cmd_help() -> None:
    print(f"""
  {B}commands:{R}
    {C}/edit{R}           open editor for multi-line input
    {C}/clear{R}          clear conversation history
    {C}/providers{R}      switch provider
    {C}/models{R}         switch model
    {C}/switch-wiki{R}    switch active wiki (interactive, or /switch-wiki <name> or --new)
    {C}/wikis{R}          list saved wikis
    {C}/remove-wiki{R}    remove a wiki profile (/remove-wiki [name])
    {C}/remove-key{R}     remove saved api key
    {C}/help{R}           show this help
    {C}exit{R}            quit
""")
```

**Edit 3** — add new slash-command handlers and dispatch. Insert before `# ── Main ──`:

```python
def _cmd_switch_wiki(agent: WikiAgent, arg: str) -> None:
    """Rebuild agent.wiki_client + agent.pages after switching."""
    new_client = switch_wiki_flow(arg)
    agent.wiki_client = new_client
    agent.pages = PagesManager(new_client)
    print()


def _cmd_wikis() -> None:
    data = list_wikis()
    active = None
    try:
        from wiki_cli.wikis import get_active_wiki_name
        active = get_active_wiki_name()
    except Exception:
        pass

    if not data:
        print(f"  {D}no saved wikis{R}\n")
        return

    print(f"  {D}saved wikis:{R}")
    print()
    for name in sorted(data):
        marker = f" {G}*{R}" if name == active else "  "
        print(f"  {marker} {B}{name}{R}  {data[name]['url']}")
    print()


def _cmd_remove_wiki(agent: WikiAgent, arg: str) -> None:
    from wiki_cli.wikis import get_active_wiki_name, set_active_wiki

    target = arg.strip() or get_active_wiki_name()
    if not target:
        print(f"  {Y}no wiki specified and no active wiki{R}\n")
        return
    remove_wiki(target)
    if get_active_wiki_name() == target:
        set_active_wiki(None)
        agent.wiki_client = None
        agent.pages = None
    print(f"  {G}removed '{target}'{R}\n")
```

**Edit 4** — extend the dispatch block in `ai_mode()` (around lines 351–382). Replace the existing `if prompt == ...` chain:

```python
        if prompt == "/help":
            _cmd_help()
            continue
        if prompt == "/clear":
            agent.clear_history()
            print(f"  {G}history cleared{R}\n")
            continue
        if prompt == "/edit":
            content = _open_editor()
            if content:
                prompt = content
            else:
                continue
        if prompt == "/providers":
            _cmd_providers(agent)
            continue
        if prompt == "/models":
            _cmd_models(agent)
            continue
        if prompt == "/remove-key":
            _cmd_remove_key(agent)
            continue
        if prompt.startswith("/switch-wiki"):
            arg = prompt[len("/switch-wiki"):].strip()
            try:
                _cmd_switch_wiki(agent, arg)
            except WikiJSError as exc:
                print(f"  {Y}{exc}{R}\n")
            continue
        if prompt == "/wikis":
            _cmd_wikis()
            continue
        if prompt.startswith("/remove-wiki"):
            arg = prompt[len("/remove-wiki"):].strip()
            try:
                _cmd_remove_wiki(agent, arg)
            except WikiJSError as exc:
                print(f"  {Y}{exc}{R}\n")
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            break
```

**Edit 5** — replace the startup block in `ai_mode()` (around lines 326–347). Replace the try/except for `last = _load_last_config()`:

```python
def ai_mode() -> None:
    _banner()

    try:
        try:
            client = get_active_client()
        except WikiJSError:
            print(f"  {D}no active wiki. let's configure one.{R}\n")
            client = switch_wiki_flow()

        last = _load_last_config()
        if last and get_saved_key(last.get("provider", "")):
            provider = last["provider"]
            model = last["model"]
            config = _build_config_from_saved(provider, model)
            agent = WikiAgent(config=config, wiki_client=client)
        else:
            config = _build_config()
            agent = WikiAgent(config=config, wiki_client=client)

    except WikiJSError as exc:
        print(f"  {Y}error: {exc}{R}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    except Exception as exc:
        print(f"  {Y}error: {exc}{R}", file=sys.stderr)
        sys.exit(1)

    _config_status(config)
```

- [ ] **Step 6.2: Manual smoke check**

Create scratch file at `/tmp/opencode/ai_switch_smoke.py`:

```python
from unittest.mock import patch, MagicMock
from wiki_cli.client import WikiJSClient
import sys

fake = MagicMock(spec=WikiJSClient)
fake.url = "https://w.com/graphql"

inputs = iter(["/wikis", "exit"])
with patch("builtins.input", side_effect=inputs):
    with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
        with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
            with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                with patch("wiki_cli.ai.cli._build_config") as bc:
                    from wiki_cli.ai.config import AIConfig
                    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")
                    bc.return_value = cfg
                    with patch("wiki_cli.ai.cli.WikiAgent"):
                        from wiki_cli.ai.cli import ai_mode
                        ai_mode()
print("OK")
```

Run: `python /tmp/opencode/ai_switch_smoke.py`
Expected: prints `OK`.

- [ ] **Step 6.3: Run full test suite**

Run: `pytest tests/ -v --tb=short 2>&1 | tail -80`
Expected: all green.

- [ ] **Step 6.4: Commit**

```bash
git add wiki_cli/ai/cli.py
git commit -m "feat(ai): /switch-wiki, /wikis, /remove-wiki commands"
```

---

## Task 7: Cleanup — `.env.example`, README

**Files:**
- Modify: `.env.example`
- Modify: `README.md`

- [ ] **Step 7.1: Update `.env.example`**

Replace contents:

```env
# Wiki.js credentials are no longer read from .env.
# Use the AI assistant (/switch-wiki) or main menu (option 18)
# to configure and switch between multiple Wiki.js instances.
#
# Profiles are stored at:
#   ~/.config/wiki-cli/wikis.json
#   ~/.config/wiki-cli/active_wiki.txt
```

- [ ] **Step 7.2: Update README — Configuration + AI sections**

In `README.md`, replace the "Configuration" section (lines 27–38):

```markdown
## Configuration

Wiki.js credentials are managed through named profiles — no `.env` required.

**First-time setup:** Run the AI assistant (`wiki-ai`) or main menu (`wiki-cli`) and use `/switch-wiki` (or menu option 18). You'll be prompted for a profile name, URL, and API key.

**Stored at:**
- `~/.config/wiki-cli/wikis.json` — all profiles (mode `0600`)
- `~/.config/wiki-cli/active_wiki.txt` — currently active profile (mode `0600`)

**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create)
- From the main menu: option `18. Switch Wiki`
- List profiles: `/wikis`
- Remove a profile: `/remove-wiki [name]`
```

In the AI Commands table (around line 154), replace the existing rows with:

```markdown
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (`/remove-wiki [name]`) |
```

Leave `/providers`, `/models`, `/remove-key`, `/help`, `exit` rows intact.

- [ ] **Step 7.3: Run full test suite one last time**

Run: `pytest tests/ -v --tb=short 2>&1 | tail -30`
Expected: all green.

- [ ] **Step 7.4: Commit**

```bash
git add .env.example README.md
git commit -m "docs: update configuration for multi-wiki profile support"
```

---

## Self-Review

**Spec coverage:**
- Named profiles → Tasks 1, 2
- Both AI + main menu → Tasks 5, 6
- Block duplicates by name + URL → Task 1 (`save_wiki` validation)
- Persist active across sessions → Tasks 1, 2 (`active_wiki.txt`)
- Drop `.env` → Task 7
- `~/.config/wiki-cli/wikis.json` → Task 1
- `/switch-wiki`, `/wikis`, `/remove-wiki` → Task 6
- Menu option 18 → Task 5
- `WikiJSClient(url, api_key)` signature → Task 3
- `get_active_client` raises when none → Task 2
- Interactive flow, flags optional → Task 2 (`switch_wiki_flow`)
- Tests for wikis + fix existing menu tests → Tasks 1, 2, 5

**Placeholder scan:** No TBDs. Every step has actual code.

**Type consistency:** `get_active_client` returns `WikiJSClient` in Task 2; `cli_main` uses it in Task 5; `ai/cli` uses it in Task 6. `switch_wiki_flow` returns `WikiJSClient` in Task 2; reused in Tasks 5 and 6. `WikiAgent(config, wiki_client)` signature introduced in Task 4; consumed in Task 6. All consistent.
