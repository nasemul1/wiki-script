# `/add-wiki` Slash Command Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `/add-wiki` slash command to the AI assistant that prompts for name/url/api_key, saves the profile, sets it active, rebuilds the agent's wiki client + pages, and clears conversation history.

**Architecture:** Single new handler `_cmd_add_wiki` in `wiki_cli/ai/cli.py`. Reuses existing `_prompt_new_profile()`, `save_wiki()`, `set_active_wiki()` from `wiki_cli/wikis.py`. No new modules, no storage changes.

**Tech Stack:** Python 3.10+, `MagicMock` for tests, `pytest` with `tmp_wiki_config` fixture.

## Global Constraints

- Storage: `~/.config/wiki-cli/wikis.json` (mode 0600) + `~/.config/wiki-cli/active_wiki.txt` (mode 0600).
- Prompt order: name → url → api_key.
- Validation reuses `save_wiki()` rules: name non-empty no-whitespace case-insensitive unique; URL http(s):// exact-match unique; api_key non-empty.
- Post-add: set active, rebuild `agent.wiki_client`, rebuild `agent.pages`, call `agent.clear_history()`.
- Auto-switch to new wiki + fresh conversation context per user requirement.
- Interactive only — no `/add-wiki <args>` form.
- Tests use `tmp_wiki_config` fixture from `tests/conftest.py`.
- ANSI codes: `G = "\033[32m"` (green), `R = "\033[0m"` (reset), `B = "\033[1m"` (bold), `D = "\033[2m"` (dim), `C = "\033[36m"` (cyan), `Y = "\033[33m"` (yellow).

---

## Task 1: `_cmd_add_wiki` handler + dispatch + help

**Files:**
- Modify: `wiki_cli/ai/cli.py` (add handler, dispatch entry, help line)
- Modify: `tests/ai_cli/success.py` (append 3 new tests)
- Modify: `tests/test_ai_cli.py` (append 3 wrappers)

**Interfaces this task produces:**
```python
# wiki_cli/ai/cli.py
def _cmd_add_wiki(agent: WikiAgent) -> None
```

- [ ] **Step 1.1: Write failing tests**

Append to `tests/ai_cli/success.py` (at the end of the file):

```python
def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    """Verify profile saved, set active, agent rebuilt."""
    from wiki_cli.ai.cli import _cmd_add_wiki
    from wiki_cli.pages import PagesManager

    agent = MagicMock()
    inputs = iter(["prod", "https://prod.com/graphql", "secret"])
    with patch(INPUT_PATCH, side_effect=inputs):
        _cmd_add_wiki(agent)
    assert wikis.get_wiki("prod") == {
        "url": "https://prod.com/graphql",
        "api_key": "secret",
    }
    assert wikis.get_active_wiki_name() == "prod"
    assert agent.wiki_client is not None
    assert agent.wiki_client.url == "https://prod.com/graphql"
    assert agent.wiki_client.api_key == "secret"
    assert isinstance(agent.pages, PagesManager)
    agent.clear_history.assert_called_once()
    out = capsys.readouterr().out
    assert "saved → active: prod" in out
    assert "history cleared" in out
    print(f"\n  [AI] /add-wiki saves + auto-switches + clears history")


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    """Verify conversation history cleared after add."""
    from wiki_cli.ai.cli import _cmd_add_wiki

    agent = MagicMock()
    inputs = iter(["w", "https://w.com/graphql", "k"])
    with patch(INPUT_PATCH, side_effect=inputs):
        _cmd_add_wiki(agent)
    agent.clear_history.assert_called_once()
    print(f"\n  [AI] /add-wiki clears conversation history")


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    """Duplicate name raises WikiJSError; active not set, agent not rebuilt."""
    import pytest
    from wiki_cli import WikiJSError
    from wiki_cli.ai.cli import _cmd_add_wiki

    wikis.save_wiki("existing", "https://e.com/graphql", "k1")
    agent = MagicMock()
    original_client = agent.wiki_client
    inputs = iter(["existing", "https://other.com/graphql", "k2"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with pytest.raises(WikiJSError):
            _cmd_add_wiki(agent)
    assert wikis.get_active_wiki_name() is None
    assert agent.wiki_client is original_client
    print(f"\n  [AI] /add-wiki duplicate name raises and preserves state")
```

- [ ] **Step 1.2: Append 3 wrappers to `tests/test_ai_cli.py`**

Append to `tests/test_ai_cli.py`:

```python
from ai_cli.success import test_ai_add_wiki_saves_profile as _add_save
from ai_cli.success import test_ai_add_wiki_clears_history as _add_clear
from ai_cli.success import test_ai_add_wiki_duplicate_name_no_change as _add_dup


def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    _add_save(capsys, tmp_wiki_config)


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    _add_clear(capsys, tmp_wiki_config)


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    _add_dup(capsys, tmp_wiki_config)
```

- [ ] **Step 1.3: Run tests — verify RED**

Run: `uv run pytest tests/test_ai_cli.py -v -k "add_wiki"`
Expected: FAIL with `AttributeError: module 'wiki_cli.ai.cli' has no attribute '_cmd_add_wiki'`.

- [ ] **Step 1.4: Implement `_cmd_add_wiki` in `wiki_cli/ai/cli.py`**

Three edits.

**Edit 1** — Add `_cmd_add_wiki` function. Find a good location: after the existing `_cmd_remove_wiki` (around line 397 in the current file). Insert:

```python
def _cmd_add_wiki(agent: WikiAgent) -> None:
    """Add a new wiki profile, set as active, rebuild agent, clear history."""
    from wiki_cli.client import WikiJSClient
    from wiki_cli.pages import PagesManager
    from wiki_cli.wikis import _prompt_new_profile, save_wiki, set_active_wiki

    name, url, api_key = _prompt_new_profile()
    save_wiki(name, url, api_key)
    set_active_wiki(name)

    agent.wiki_client = WikiJSClient(url=url, api_key=api_key)
    agent.pages = PagesManager(agent.wiki_client)
    agent.clear_history()

    print(f"  {G}saved → active: {name} (history cleared){R}\n")
```

**Edit 2** — Add help text line. Find `_cmd_help()` body (around line 326-336). Add this line near the top of the commands list, before `/switch-wiki`:

```python
    {C}/add-wiki{R}        add a new wiki profile (auto-switches + clears history)
```

**Edit 3** — Add dispatch entry. Find the dispatch block in `ai_mode()` (around line 471 where `/switch-wiki` is handled). Add before the `/switch-wiki` check:

```python
        if prompt == "/add-wiki":
            _cmd_add_wiki(agent)
            continue
```

Note on `PagesManager` import: the existing top-level import at line 36 already imports `PagesManager`. No new top-level import needed. Verify by reading the file — if `PagesManager` is not yet top-level-imported, add it. The brief expects it to already exist (per Task 6 of the prior multi-wiki plan which added this import).

Also: `WikiJSClient` is imported at the top of `wiki_cli/ai/cli.py` already (line 19 area — `from wiki_cli import WikiJSClient, WikiJSError`). Confirm before adding.

If either import is missing, add it to the top-level imports block. Both should already be present from prior tasks.

- [ ] **Step 1.5: Run tests — verify GREEN**

Run: `uv run pytest tests/test_ai_cli.py -v -k "add_wiki"`
Expected: 3 pass.

- [ ] **Step 1.6: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --tb=short -q 2>&1 | tail -5`
Expected: 108/108 pass (105 prior + 3 new).

- [ ] **Step 1.7: Commit**

```bash
git add wiki_cli/ai/cli.py tests/ai_cli/success.py tests/test_ai_cli.py
git commit -m "feat(ai): /add-wiki slash command (save + switch + clear history)"
```

---

## Task 2: README update

**Files:**
- Modify: `README.md` (AI Commands table — add `/add-wiki` row)

- [ ] **Step 2.1: Update README AI Commands table**

In `README.md`, find the AI Commands table. The table currently starts with:

```
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
```

Add a new row above `/switch-wiki`:

```
| `/add-wiki` | Add a new wiki profile (auto-switches + clears history) |
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
```

Also update the "Switching wikis" bullet list in the Configuration section. Find:

```
**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create)
- From the main menu: option `17. Manage Wikis` (submenu with switch / add / list / remove)
- List profiles: `/wikis` or main menu option `17 → 3`
- Remove a profile: `/remove-wiki [name]` or main menu option `17 → 4` (both ask to confirm)
```

Add a bullet for add:

```
**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create), `/add-wiki` (add + auto-switch)
- From the main menu: option `17. Manage Wikis` (submenu with switch / add / list / remove)
- List profiles: `/wikis` or main menu option `17 → 3`
- Remove a profile: `/remove-wiki [name]` or main menu option `17 → 4` (both ask to confirm)
```

- [ ] **Step 2.2: Verify no regressions**

Run: `uv run pytest tests/ --tb=short -q 2>&1 | tail -5`
Expected: still 108 green.

- [ ] **Step 2.3: Commit**

```bash
git add README.md
git commit -m "docs: document /add-wiki command in README"
```

---

## Self-Review

**Spec coverage:**
- `/add-wiki` interactive prompts (name/url/api_key) → Task 1 via `_prompt_new_profile()` reuse
- Save profile → Task 1 via `save_wiki()`
- Set active → Task 1 via `set_active_wiki()`
- Rebuild `agent.wiki_client` + `agent.pages` → Task 1
- Clear conversation history → Task 1 via `agent.clear_history()`
- Dispatch entry → Task 1 Edit 3
- Help text → Task 1 Edit 2
- README update → Task 2
- Tests (3 scenarios) → Task 1 Steps 1.1-1.2

**Placeholder scan:** No TBDs. Every step has actual code.

**Type consistency:**
- `_cmd_add_wiki(agent)` signature matches spec.
- `WikiAgent.clear_history()` exists — confirmed via prior context (line 89 of `wiki_cli/ai/agent.py`).
- `PagesManager` and `WikiJSClient` already imported in `wiki_cli/ai/cli.py` from prior tasks.
- `_prompt_new_profile()` returns `(name, url, api_key)` tuple — confirmed in `wiki_cli/wikis.py:127`.
