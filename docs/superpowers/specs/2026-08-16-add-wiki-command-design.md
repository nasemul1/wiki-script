# `/add-wiki` Slash Command — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Add a discoverable `/add-wiki` slash command in the AI assistant. Prompts for name/url/api_key, saves the profile, sets it active, rebuilds the agent's wiki client + pages manager, and clears conversation history (fresh context for the new wiki).

## Decisions

- **Command name:** `/add-wiki` (clear, discoverable, single-purpose).
- **Post-add behavior:** Auto-switch + clear history. Fresh context per wiki.
- **Prompt order:** name → url → api_key.
- **Argument form:** Interactive only. No `/add-wiki <name>` shortcut. Matches `/switch-wiki` (no-args) pattern.
- **Storage layer:** Unchanged. Reuses `save_wiki()`, `set_active_wiki()`, `_prompt_new_profile()` from `wiki_cli/wikis.py`.

## Architecture

### Single new handler in `wiki_cli/ai/cli.py`

```python
def _cmd_add_wiki(agent: WikiAgent) -> None:
    from wiki_cli.wikis import _prompt_new_profile, save_wiki, set_active_wiki

    name, url, api_key = _prompt_new_profile()
    save_wiki(name, url, api_key)
    set_active_wiki(name)

    agent.wiki_client = WikiJSClient(url=url, api_key=api_key)
    agent.pages = PagesManager(agent.wiki_client)
    agent.clear_history()

    print(f"  {G}saved → active: {name} (history cleared){R}\n")
```

### Dispatch

Add to the dispatch block in `ai_mode()`:

```python
if prompt == "/add-wiki":
    _cmd_add_wiki(agent)
    continue
```

### Help text

Append to `_cmd_help()` body:

```python
{C}/add-wiki{R}        add a new wiki profile (auto-switches + clears history)
```

## Behavior

```
> /add-wiki

name: production
url: https://wiki.prod.com/graphql
api key: ********
saved → active: production (history cleared)
```

## Reused components

- `wiki_cli/wikis.py:_prompt_new_profile()` — already exists; handles name/url/api_key prompts + validation. Returns `(name, url, api_key)`.
- `wiki_cli/wikis.py:save_wiki(name, url, api_key)` — already exists; persists to `~/.config/wiki-cli/wikis.json` with validation (rejects duplicate name + URL, validates scheme).
- `wiki_cli/wikis.py:set_active_wiki(name)` — already exists; writes to `~/.config/wiki-cli/active_wiki.txt`.
- `wiki_cli/client.py:WikiJSClient(url, api_key)` — already exists.
- `wiki_cli/pages.py:PagesManager(client)` — already exists.
- `wiki_cli/ai/agent.py:WikiAgent.clear_history()` — already exists; resets messages to system prompt only.

## Error handling

| Case | Behavior |
|---|---|
| Duplicate name | `save_wiki` raises `WikiJSError("wiki '<name>' already exists")`. Dispatch catches, prints yellow error, no state change. |
| Duplicate URL | `save_wiki` raises `WikiJSError("url already saved as '<existing>'")`. Same handling. |
| Invalid URL | `_prompt_new_profile` re-prompts until valid. |
| Empty name | `_prompt_new_profile` re-prompts. |
| Empty api_key | `_prompt_new_profile` re-prompts. |
| EOFError / KeyboardInterrupt during prompts | Propagates out of `_prompt_new_profile` → falls through to main loop's existing `except (EOFError, KeyboardInterrupt)` handler. |

## Testing

### `tests/ai_cli/success.py` — 3 new tests

```python
def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    """Verify profile saved, set active, agent rebuilt."""
    from wiki_cli.ai.cli import _cmd_add_wiki
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
    assert agent.pages is not None
    agent.clear_history.assert_called_once()
    out = capsys.readouterr().out
    assert "saved → active: prod" in out


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    """Verify conversation history cleared after add."""
    from wiki_cli.ai.cli import _cmd_add_wiki
    agent = MagicMock()
    inputs = iter(["w", "https://w.com/graphql", "k"])
    with patch(INPUT_PATCH, side_effect=inputs):
        _cmd_add_wiki(agent)
    agent.clear_history.assert_called_once()


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    """Duplicate name raises WikiJSError; no state change, agent not rebuilt."""
    from wiki_cli import WikiJSError
    from wiki_cli.ai.cli import _cmd_add_wiki
    wikis.save_wiki("existing", "https://e.com/graphql", "k1")
    agent = MagicMock()
    original_client = agent.wiki_client
    inputs = iter(["existing", "https://other.com/graphql", "k2"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with pytest.raises(WikiJSError):
            _cmd_add_wiki(agent)
    assert wikis.get_active_wiki_name() is None  # active not set
    assert agent.wiki_client is original_client  # not rebuilt
```

### `tests/test_ai_cli.py` — 3 wrappers

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

## Files touched

- **Modify:** `wiki_cli/ai/cli.py` — add `_cmd_add_wiki` function, dispatch entry, help text line
- **Modify:** `tests/ai_cli/success.py` — append 3 new tests
- **Modify:** `tests/test_ai_cli.py` — append 3 wrappers
- **Modify:** `README.md` — add `/add-wiki` row to AI Commands table (above `/switch-wiki`)

## Out of scope (deferred)

- Argument form `/add-wiki <name> <url> <key>` — interactive only per decision.
- Per-wiki conversation history persistence — YAGNI.
- Auto-test connection after add — YAGNI; user can run `/` then any tool to verify.
- Migration from old `.env` — out of scope.
