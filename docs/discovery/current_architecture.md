# Current Architecture Analysis

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. System Overview

The wiki-script repository implements a **Level 1 Wiki.js CLI** — a terminal-based
client for Wiki.js that provides page management and revision history through a
menu-driven interface. A **Level 2** AI assistant layer was added later, bolted on
top of the existing CLI without architectural refactoring.

### Architecture style

**Layered monolith** with three tiers:

```
┌─────────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                      │
│  cli_main.py  cli_pages.py  cli_history.py  cli_system.py   │
│  ai/cli.py                                                  │
├─────────────────────────────────────────────────────────────┤
│                     BUSINESS LOGIC LAYER                    │
│  pages/manager.py  ai/agent.py  ai/config.py               │
├─────────────────────────────────────────────────────────────┤
│                     DATA / TRANSPORT LAYER                  │
│  client.py  models.py  exceptions.py  pages/queries.py     │
│  pages/history.py  ai/tools.py                              │
└─────────────────────────────────────────────────────────────┘
```

### Call graph

```
cli_main.main()
  ├── cli_pages.* (11 handlers) ──→ PagesManager ──→ WikiJSClient
  ├── cli_history.* (4 handlers) ──→ PagesManager ──→ WikiJSClient
  ├── cli_system.test_connection() ──→ PagesManager ──→ WikiJSClient
  └── ai.cli.ai_mode() ──→ WikiAgent ──→ PagesManager ──→ WikiJSClient
                                    └──→ openai client ──→ LLM API
```

---

## 2. Module Inventory

| Module | Lines | Responsibility | Side effects |
|---|---|---|---|
| `wiki_cli/__init__.py` | 19 | Public API re-exports | None |
| `wiki_cli/__main__.py` | 6 | Entry point (`python -m wiki_cli`) | Calls `main()` |
| `wiki_cli/client.py` | 82 | GraphQL HTTP transport | Network, env loading |
| `wiki_cli/models.py` | 63 | Pydantic data models | None (pure data) |
| `wiki_cli/exceptions.py` | 23 | Custom exception class | None (pure data) |
| `wiki_cli/utils.py` | 35 | CLI display helpers | stdout/stdin |
| `wiki_cli/cli_main.py` | 118 | Main menu loop | stdout/stdin, sys.exit |
| `wiki_cli/cli_pages.py` | 389 | Page CLI handlers | stdout/stdin, filesystem |
| `wiki_cli/cli_history.py` | 136 | History CLI handlers | stdout/stdin |
| `wiki_cli/cli_system.py` | 22 | System commands | stdout |
| `wiki_cli/pages/__init__.py` | 5 | Package re-export | None |
| `wiki_cli/pages/manager.py` | 262 | Page business logic | Network (GraphQL) |
| `wiki_cli/pages/queries.py` | 172 | GraphQL query strings | None (pure data) |
| `wiki_cli/pages/history.py` | 59 | History GraphQL strings | None (pure data) |
| `wiki_cli/ai/__init__.py` | 7 | Package re-export | None |
| `wiki_cli/ai/agent.py` | 574 | AI agent loop | Network (LLM + Wiki), filesystem |
| `wiki_cli/ai/cli.py` | 365 | AI interactive REPL | stdout/stdin, filesystem, subprocess |
| `wiki_cli/ai/config.py` | 162 | AI provider config | Filesystem, network |
| `wiki_cli/ai/tools.py` | 393 | OpenAI tool schemas | None (pure data) |
| **Total** | **~3,000** | | |

---

## 3. Layer Analysis

### 3.1 Transport Layer

**`wiki_cli/client.py`** — The single gateway to Wiki.js.

- Wraps `gql[requests]` with Bearer token auth.
- Calls `load_dotenv()` at **module import time** (global side effect).
- Provides `execute(query, variable_values, operation_name)` → `dict[str, Any]`.
- Retry configured at transport level: `retries=3` (hardcoded).
- TLS verification hardcoded: `verify=True`.
- No connection pooling configuration exposed.
- No request/response logging.
- No retry backoff configuration.

### 3.2 Data Layer

**`wiki_cli/models.py`** — Four Pydantic v2 models:

| Model | Fields | Notes |
|---|---|---|
| `Page` | 10 fields | Core wiki page representation |
| `PageResponse` | 4 fields | Mutation response wrapper |
| `PageHistory` | 7 fields | History trail entry |
| `PageVersion` | 17 fields | Full revision snapshot |

- All models have sensible defaults.
- `PageVersion` has 2 dead fields: `publishStartDate`, `publishEndDate` (never populated).
- Field names use camelCase to match GraphQL schema (deviates from PEP-8).

**`wiki_cli/exceptions.py`** — Single exception class `WikiJSError`:

- Carries `message: str` and optional `errors: list[dict]`.
- `__str__` joins sub-error messages with `"; "`.
- Used in 7 of 19 modules — the universal error type.

**`wiki_cli/pages/queries.py`** and **`wiki_cli/pages/history.py`** — Pure data:

- 10 GraphQL string constants total.
- Tightly coupled to Wiki.js v2 GraphQL schema.
- No validation of query structure.

### 3.3 Business Logic Layer

**`wiki_cli/pages/manager.py`** — The core orchestration class:

- 14 public methods covering CRUD, search, history, move, clone, restore.
- Each method calls `self.client.execute()` — no caching, no batching.
- Error handling: checks `responseResult.succeeded` and raises `WikiJSError`.
- `_parse_response()` and `_parse_single_page()` handle GraphQL response unwrapping.
- Hardcoded defaults: `locale="en"`, `editor="markdown"`, `isPublished=True`, `isPrivate=False`.
- `move_or_rename()` is implemented as get-then-update (two network calls).
- `clone_page()` is implemented as get-then-create (two network calls).

**`wiki_cli/ai/agent.py`** — Single AI agent:

- 574 lines — the largest file in the codebase.
- Creates its own `WikiJSClient` internally (no dependency injection).
- Maintains conversation history with token-based trimming.
- `MAX_CONTEXT_TOKENS = 50_000` — hardcoded.
- Token estimation: `len(content) // 4` — rough heuristic.
- Dispatches tool calls to `PagesManager` methods via a dict mapping.
- Error handling: wraps each tool call in try/except, returns structured dicts.
- No input validation on LLM-supplied arguments.
- Anti-pattern: `agent.__init__(config)` re-calls constructor on existing instance.

**`wiki_cli/ai/config.py`** — Provider configuration:

- Credential storage at `~/.config/wiki-cli/credentials.json`.
- `AIConfig` dataclass with `get_client()` → `openai.OpenAI`.
- `fetch_models()` uses `httpx` to list available models.
- 6 providers supported: openai, openrouter, groq, mistral, ollama, ollama-cloud.
- Provider URLs hardcoded in `PROVIDER_DEFAULTS` — no override mechanism.
- `getpass` imported but never used (dead import).
- Config directory path duplicated in `cli.py`.

### 3.4 Presentation Layer

**`wiki_cli/cli_main.py`** — Main menu:

- 17-option menu (0–17, option 17 = AI assistant).
- Lazy-loads AI module to avoid import overhead.
- Catches `WikiJSError` at menu loop level.
- `KeyboardInterrupt` and `EOFError` not caught.
- Imports all 15 handler functions at module level.

**`wiki_cli/cli_pages.py`** — Page handlers (389 lines):

- 11 functions, one per page operation.
- All take `pages: PagesManager` as first argument.
- Reads from stdin, writes to stdout.
- `export_page` writes Markdown with YAML frontmatter.
- `import_page` reads Markdown with hand-rolled frontmatter parser.
- No try/except blocks — all errors propagate to `cli_main`.

**`wiki_cli/cli_history.py`** — History handlers (136 lines):

- 4 functions for history operations.
- Uses `difflib.unified_diff` for revision diffing.
- Pagination via `PAGE_SIZE` constant (20).
- Same error propagation pattern as page handlers.

**`wiki_cli/ai/cli.py`** — AI REPL (365 lines):

- Startup flow: provider selection → API key → model selection.
- Slash commands: `/edit`, `/clear`, `/providers`, `/models`, `/remove-key`, `/help`.
- External editor integration via `$EDITOR` / `$VISUAL`.
- Saves last config to `~/.config/wiki-cli/last_config.json`.
- Duplicates config directory path from `config.py`.

---

## 4. Data Flow

### 4.1 Page CRUD Flow

```
User input → cli_pages.py → PagesManager.method() → WikiJSClient.execute()
                                                        ↓
                                                   GraphQL HTTP POST
                                                        ↓
                                                   Wiki.js Server
                                                        ↓
                                                   Response dict
                                                        ↓
                                              PagesManager._parse_response()
                                                        ↓
                                                   Pydantic model
                                                        ↓
                                              cli_pages.py (display)
```

### 4.2 AI Assistant Flow

```
User prompt → ai/cli.py → WikiAgent.run()
                              ↓
                    OpenAI API (chat.completions.create)
                              ↓
                    LLM returns tool_call
                              ↓
                    WikiAgent._execute_tool()
                              ↓
                    PagesManager.method() → Wiki.js
                              ↓
                    Result → back to LLM
                              ↓
                    LLM returns final response
                              ↓
                    ai/cli.py (display)
```

### 4.3 File Import/Export Flow

```
Export: PagesManager.get_by_id() → Markdown + YAML frontmatter → file.write()
Import: file.read() → parse frontmatter → PagesManager.create()
```

---

## 5. Testing Architecture

| Aspect | Current State |
|---|---|
| Framework | pytest |
| Test count | 67 tests across 17 top-level files |
| Pattern | Modular delegation (test files import from subdirectories) |
| Mocking | `MagicMock(spec=PagesManager)` + `patch("builtins.input")` |
| Coverage gaps | Zero tests for client, models, exceptions, utils, manager, AI |
| CI | None configured |

### Test coverage map

| Module | Has tests | Test count | Notes |
|---|---|---|---|
| `client.py` | No | 0 | Critical gap |
| `models.py` | No | 0 | Critical gap |
| `exceptions.py` | No | 0 | Critical gap |
| `utils.py` | No | 0 | Critical gap |
| `pages/manager.py` | No | 0 | Critical gap |
| `cli_pages.py` | Yes | 42 | All 11 handlers tested |
| `cli_history.py` | Yes | 14 | All 4 handlers tested |
| `cli_main.py` | Yes | 4 | Menu dispatch tested |
| `cli_system.py` | Yes | 2 | Connection test only |
| `ai/*` | No | 0 | Zero AI tests |

---

## 6. Configuration Surface

| Config | Location | Mechanism |
|---|---|---|
| Wiki.js URL | `.env` or env var | `WIKIJS_URL` |
| Wiki.js API key | `.env` or env var | `WIKIJS_API_KEY` |
| AI provider credentials | `~/.config/wiki-cli/credentials.json` | `ai/config.py` |
| AI last config | `~/.config/wiki-cli/last_config.json` | `ai/cli.py` |
| Default locale | Hardcoded in `manager.py` | `"en"` |
| Default editor | Hardcoded in `manager.py` | `"markdown"` |
| Page size | Hardcoded in `utils.py` | `20` |
| Token budget | Hardcoded in `agent.py` | `50,000` |
| Retry count | Hardcoded in `client.py` | `3` |

---

## 7. Summary

| Metric | Value |
|---|---|
| Total source files | 19 |
| Total lines of code | ~3,000 |
| Test files | 17 top-level + 25 sub-modules |
| Test count | 67 |
| External dependencies | 4 runtime (`gql`, `dotenv`, `pydantic`, `openai`) |
| Side-effect modules | 7 (client, cli_main, cli_pages, cli_history, ai/agent, ai/cli, ai/config) |
| Pure-data modules | 4 (models, exceptions, queries, history, tools) |
| Coupling hotspots | `cli_main.py` (6 imports), `ai/agent.py` (5 imports), `pages/manager.py` (8 imports) |
| Hardcoded values | 15+ across config, constants, defaults |
