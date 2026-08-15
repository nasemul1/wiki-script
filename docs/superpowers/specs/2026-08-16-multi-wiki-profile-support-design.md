# Multi-Wiki Profile Support — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Replace single-wiki env-var config with named profiles. User can store multiple Wiki.js instances and switch between them from inside both the main interactive menu and the AI assistant.

## Decisions

- **Storage model:** Named profiles. URL+key stored per name.
- **Scope:** Both AI assistant (`/switch-wiki`) and main menu (option 18).
- **Duplicates:** Block. Saving a profile whose name OR URL already exists fails.
- **Persistence:** Active profile persisted across sessions in `active_wiki.txt`.
- **Env file:** Dropped. `.env` / `.env.example` no longer carry wiki credentials.
- **Disk location:** `~/.config/wiki-cli/wikis.json` + `~/.config/wiki-cli/active_wiki.txt`.
- **Management:** Full CRUD via slash commands and menu option.
- **Switch flow:** Interactive by default. `/switch-wiki <name>` jumps. `/switch-wiki --new` forces create.

## Architecture

### New module: `wiki_cli/wikis.py`

Responsibilities: read/write wiki profile storage, resolve active client.

Public API:

```python
def list_wikis() -> dict[str, dict[str, str]]   # name → {url, api_key}
def get_wiki(name: str) -> dict[str, str] | None
def save_wiki(name: str, url: str, api_key: str) -> None
def remove_wiki(name: str) -> None
def get_active_wiki_name() -> str | None
def set_active_wiki(name: str | None) -> None
def get_active_client() -> WikiJSClient
def switch_wiki_flow(arg: str = "") -> WikiJSClient   # interactive UI
```

Storage paths:

```
~/.config/wiki-cli/wikis.json         # chmod 0600
~/.config/wiki-cli/active_wiki.txt    # chmod 0600
```

`wikis.json` schema:

```json
{
  "work":     {"url": "https://wiki.work.com/graphql",  "api_key": "..."},
  "personal": {"url": "https://wiki.home.io/graphql",   "api_key": "..."}
}
```

`active_wiki.txt` contents: a single line with the active profile name, or empty file.

### Changes to `wiki_cli/client.py`

`WikiJSClient.__init__` signature changes:

```python
def __init__(self, url: str, api_key: str) -> None
```

- Both args required.
- No `os.getenv` calls. No env fallback.
- Remove `load_dotenv()` from this file (no longer needed for wiki creds).
- Validation: `WikiJSError` if `url` empty or `api_key` empty.
- URL prefix check: must start with `http://` or `https://`. Otherwise `WikiJSError`.

### Changes to `wiki_cli/ai/agent.py`

`WikiAgent.__init__` accepts optional pre-built client:

```python
def __init__(self, config: AIConfig | None = None, wiki_client: WikiJSClient | None = None) -> None
```

- If `wiki_client` given → use it.
- Else → fall back to `get_active_client()`. Raise `WikiJSError("no active wiki...")` if none.

After `/switch-wiki`, caller rebuilds agent's wiki client + pages manager:

```python
agent.wiki_client = new_client
agent.pages = PagesManager(new_client)
```

LLM client (`self.client`) untouched.

### Changes to `wiki_cli/cli_main.py`

`main()` entry:
1. Call `get_active_client()`. If `WikiJSError` (no active wiki) → call `switch_wiki_flow()` then retry once.
2. Build `PagesManager`.
3. Add menu entry **18. Switch Wiki** before `0. Exit`. Handler: `switch_wiki_flow()` then rebuild `pages` from new client.
4. On `WikiJSError` from any handler, print error and continue (existing behavior).

### New commands in `wiki_cli/ai/cli.py`

Slash-command dispatch additions:

| Command | Behavior |
|---|---|
| `/switch-wiki` | Interactive: list profiles + "add new", pick one or create. |
| `/switch-wiki <name>` | Jump to that profile. Error if not found. |
| `/switch-wiki --new` | Force new-profile flow. |
| `/wikis` | List all profiles. Mark active with `*`. |
| `/remove-wiki` | Remove active profile. |
| `/remove-wiki <name>` | Remove named profile. Error if not found. |

Interactive flow (in `switch_wiki_flow`):

```
saved wikis:
  1    work        https://wiki.work.com/graphql
  2    personal    https://wiki.home.io/graphql
  3    add new
> _
```

New-profile sub-flow:

```
name: work
url: https://wiki.work.com/graphql
api key: ********    (getpass, no echo)
saved → active: work
```

After switch (any path): return `WikiJSClient` so caller can rebuild.

### Help text

`/help` adds:

```
/switch-wiki     switch active wiki (interactive)
/wikis           list saved wikis
/remove-wiki     remove a wiki profile
```

## Data flow

```
startup
  → get_active_client()
    → read active_wiki.txt → name
    → load wikis.json[name]
    → WikiJSClient(url, api_key)
  → build PagesManager

user: /switch-wiki work
  → switch_wiki_flow("work")
    → load wikis.json["work"]
    → set_active_wiki("work")
    → WikiJSClient(url, api_key)
  → agent.wiki_client = new
  → agent.pages = PagesManager(new)

LLM tool call: agent.pages.create(...)
  → agent.wiki_client.execute(...)    # GraphQL against work wiki
```

## Error handling

| Case | Behavior |
|---|---|
| `wikis.json` missing or invalid JSON | Treat as empty dict. No crash. |
| `active_wiki.txt` missing or empty | `get_active_client` raises. Caller prompts to configure. |
| `active_wiki.txt` references deleted profile | Raise. Caller prompts to reconfigure. |
| `save_wiki` duplicate name (case-insensitive) | Raise `WikiJSError("wiki '<name>' already exists")`. |
| `save_wiki` duplicate URL (exact match) | Raise `WikiJSError("url already saved as '<name>'")`. |
| URL missing scheme | Raise `WikiJSError("url must start with http:// or https://")`. |
| API key empty | Raise `WikiJSError("api key required")`. |
| Profile name empty / whitespace | Raise `WikiJSError("name required, no spaces")`. |
| `/switch-wiki <unknown>` | Print error, no state change. |
| `/remove-wiki <unknown>` | Print error, no state change. |
| Removing active profile | Clear `active_wiki.txt`. User must pick or create next session. |
| GraphQL 401 on first tool call after switch | Tool error surfaces. No silent fallback. |

## Validation rules

- **Name:** non-empty after strip. No whitespace inside. Case-insensitive uniqueness.
- **URL:** non-empty. Must start with `http://` or `https://`. Exact-match uniqueness.
- **API key:** non-empty after strip.

## Testing

New file `tests/test_wikis.py` covering:

- `list_wikis()` empty when file missing.
- `list_wikis()` returns parsed dict when file exists.
- `save_wiki()` roundtrips via `get_wiki()`.
- `save_wiki()` rejects duplicate name (case-insensitive).
- `save_wiki()` rejects duplicate URL.
- `save_wiki()` rejects empty name / URL / key.
- `save_wiki()` rejects URL without scheme.
- `remove_wiki()` removes entry. Idempotent on missing name.
- `set_active_wiki()` / `get_active_wiki_name()` roundtrip.
- `get_active_client()` raises when no active wiki.
- `get_active_client()` returns `WikiJSClient` with active profile's url+key.

Existing `tests/test_connection.py` and any tests that build `WikiJSClient()` directly: update to pass `url` and `api_key` explicitly.

`tests/conftest.py`: add `tmp_wiki_config` fixture using `monkeypatch` + `tmp_path` to redirect `wikis.json` and `active_wiki.txt` to a temp dir. Avoid touching real `~/.config/wiki-cli`.

## Files touched

- **New:** `wiki_cli/wikis.py`
- **New:** `tests/test_wikis.py`
- **Modify:** `wiki_cli/client.py` (signature + remove env loading)
- **Modify:** `wiki_cli/ai/agent.py` (accept wiki_client)
- **Modify:** `wiki_cli/ai/cli.py` (slash commands + startup)
- **Modify:** `wiki_cli/cli_main.py` (startup + menu option 18)
- **Modify:** `wiki_cli/__init__.py` (export `switch_wiki_flow` if useful)
- **Modify:** `.env.example` (remove `WIKIJS_URL` / `WIKIJS_API_KEY`)
- **Modify:** `README.md` (document multi-wiki flow)
- **Modify:** `tests/conftest.py` (add tmp config fixture)
- **Modify:** existing tests that build `WikiJSClient()` directly

## Out of scope (deferred)

- Encrypted at-rest storage for API keys. Current AI creds stored plaintext — parity.
- Multi-wiki batch operations ("apply this on all profiles").
- Per-wiki AI provider config.
- Project-local profiles (`./.wiki-config`).
- Import/export profile bundles.
- Backwards-compat layer reading `WIKIJS_URL` / `WIKIJS_API_KEY`.
