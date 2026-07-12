# Module Analysis

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. Core Library Modules

### 1.1 `wiki_cli/client.py` (82 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | GraphQL HTTP transport to Wiki.js |
| **Public API** | `WikiJSClient(url?, api_key?)` class with `execute(query, variable_values?, operation_name?)` |
| **Side effects** | `load_dotenv()` at import time; HTTP POST on every `execute()` call |
| **Error handling** | Raises `WikiJSError` for missing config, gql errors, GraphQL errors |
| **Type annotations** | ~90% (public signatures full, internal vars inferred) |
| **Hardcoded values** | `retries=3`, `verify=True`, env var names `WIKIJS_URL`/`WIKIJS_API_KEY` |
| **Coupling** | Depends on `gql`, `dotenv`, `requests`; raises `WikiJSError` |
| **Public surface** | `WikiJSClient` (1 class, 1 method beyond `__init__`) |

**Issues:**
- `load_dotenv()` at import time is a global side effect that cannot be disabled.
- No connection pooling configuration.
- No request/response logging or observability hooks.
- No timeout configuration for individual requests.
- `fetch_schema_from_transport=False` hardcoded — schema validation disabled.

### 1.2 `wiki_cli/models.py` (63 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Pydantic v2 data models for Wiki.js domain objects |
| **Public API** | `Page`, `PageResponse`, `PageHistory`, `PageVersion` (4 models) |
| **Side effects** | None (pure data) |
| **Error handling** | Pydantic validation errors |
| **Type annotations** | 100% |
| **Hardcoded values** | Default values: `editor="markdown"`, `isPublished=True`, `isPrivate=False`, `locale="en"` |
| **Coupling** | Only `pydantic` — leaf module |
| **Public surface** | 4 Pydantic models, ~45 fields total |

**Issues:**
- `PageVersion` has 2 dead fields: `publishStartDate`, `publishEndDate` (never populated).
- Field names use camelCase (`errorCode`) matching GraphQL but deviating from PEP-8.
- No custom validators for business rules (e.g., path format, locale codes).
- No model-level documentation (docstrings).

### 1.3 `wiki_cli/exceptions.py` (23 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Custom exception class |
| **Public API** | `WikiJSError(message, errors?)` |
| **Side effects** | None |
| **Error handling** | N/A (defines the error type) |
| **Type annotations** | 100% |
| **Hardcoded values** | `"Unknown error"` fallback, `"; "` separator |
| **Coupling** | None — leaf module |
| **Public surface** | 1 exception class |

**Issues:**
- Single exception type for all errors — no distinction between auth, network, validation, or not-found errors.
- No structured error codes for programmatic handling.
- `errors` field stores raw GraphQL error dicts — no Pydantic model for them.

### 1.4 `wiki_cli/utils.py` (35 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | CLI display helpers (table printing, input prompting) |
| **Public API** | `PAGE_SIZE=20`, `input_with_default()`, `print_page_table()`, `print_history_table()` |
| **Side effects** | stdout/stdin I/O |
| **Error handling** | None — assumes valid input |
| **Type annotations** | 100% |
| **Hardcoded values** | `PAGE_SIZE=20`, column widths, separator lengths, `[:19]` date truncation |
| **Coupling** | Depends on `models.Page`, `models.PageHistory` |
| **Public surface** | 1 constant, 3 functions |

**Issues:**
- No error handling for malformed page/history data.
- `[:19]` date truncation is fragile (assumes ISO format).
- Column widths are hardcoded — cannot adapt to terminal width.
- `PAGE_SIZE` is a module-level constant — not configurable.

---

## 2. CLI Presentation Modules

### 2.1 `wiki_cli/cli_main.py` (118 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Main menu loop, client initialization, handler dispatch |
| **Public API** | `main()`, `MENU` constant |
| **Side effects** | stdout/stdin, `sys.exit(1)` on init failure |
| **Error handling** | Catches `WikiJSError` at menu level; misses `KeyboardInterrupt`/`EOFError` |
| **Type annotations** | ~80% |
| **Hardcoded values** | Menu string, option numbers, exit code 1 |
| **Coupling** | Imports from 6 modules (heaviest hub) |
| **Public surface** | 1 function, 1 constant |

**Issues:**
- Imports all 15 handler functions at module level — no lazy loading.
- `KeyboardInterrupt` and `EOFError` not caught — ugly stack traces on Ctrl+C.
- Menu string is a 31-line hardcoded literal — not configurable or localizable.
- No graceful shutdown or cleanup on exit.

### 2.2 `wiki_cli/cli_pages.py` (389 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | 11 page-related CLI handlers |
| **Public API** | 11 functions (create, fetch, update, delete, list, search, browse_tree, move_rename, clone, export, import) |
| **Side effects** | stdin/stdout, filesystem (export writes, import reads), network (via PagesManager) |
| **Error handling** | Input validation only; no try/except — all errors propagate to cli_main |
| **Type annotations** | ~50% (signatures full, internals inferred) |
| **Hardcoded values** | Sort order map, locale, file encoding, frontmatter delimiters, confirmation strings |
| **Coupling** | Depends on `utils`, `models`, `pages` |
| **Public surface** | 11 functions |

**Issues:**
- Largest file in the codebase (389 lines) — should be split.
- No try/except blocks — all WikiJSError exceptions propagate unhandled.
- `browse_tree` does not catch errors during recursive page fetch.
- `import_page` has a fragile hand-rolled frontmatter parser.
- `export_page` hardcodes YAML frontmatter format.
- All functions take `pages: PagesManager` — no way to test without mocking the entire manager.

### 2.3 `wiki_cli/cli_history.py` (136 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | 4 history-related CLI handlers |
| **Public API** | 4 functions (view_history, view_revision, diff_revisions, restore_revision) |
| **Side effects** | stdin/stdout, network (via PagesManager) |
| **Error handling** | Input validation only; no try/except |
| **Type annotations** | ~40% (signatures full, internals untyped) |
| **Hardcoded values** | Date truncation `[:10]`, separator widths, `difflib` default context |
| **Coupling** | Depends on `utils`, `pages` |
| **Public surface** | 4 functions |

**Issues:**
- No pagination test for >20 history entries.
- `diff_two_revisions` uses `difflib.unified_diff` with hardcoded context lines.
- Same error propagation pattern as `cli_pages`.

### 2.4 `wiki_cli/cli_system.py` (22 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Connection test |
| **Public API** | `test_connection(client, pages)` |
| **Side effects** | stdout, network (via PagesManager) |
| **Error handling** | Catches `WikiJSError` |
| **Type annotations** | 100% |
| **Hardcoded values** | `order_by="CREATED"` |
| **Coupling** | Depends on `client`, `exceptions`, `pages` |
| **Public surface** | 1 function |

**Issues:**
- Minimal module — could be merged into `cli_main.py` or kept separate for clarity.
- Only tests `list_all()` — does not test write operations.

---

## 3. Pages Package

### 3.1 `wiki_cli/pages/manager.py` (262 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Core CRUD + search + history operations for Wiki.js pages |
| **Public API** | `PagesManager(client)` with 14 methods |
| **Side effects** | Network I/O (GraphQL API calls) |
| **Error handling** | Checks `responseResult.succeeded`, raises `WikiJSError` with descriptive messages |
| **Type annotations** | ~90% (public signatures full) |
| **Hardcoded values** | `locale="en"`, `editor="markdown"`, `isPublished=True`, `isPrivate=False`, `offset_page=0`, `offset_size=100` |
| **Coupling** | Depends on `client`, `exceptions`, `models`, `queries`, `history` |
| **Public surface** | 1 class, 14 methods |

**Issues:**
- `move_or_rename()` is get-then-update (2 network calls) — no atomic operation.
- `clone_page()` is get-then-create (2 network calls) — no atomic operation.
- No caching — repeated calls to `list_all()` or `get_by_id()` make fresh requests.
- No batching — each operation is a separate GraphQL request.
- `_parse_response()` and `_parse_single_page()` handle complex response unwrapping — error-prone.
- Default locale `"en"` appears 4+ times — should be a constant.

### 3.2 `wiki_cli/pages/queries.py` (172 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | GraphQL query/mutation string constants |
| **Public API** | 7 string constants |
| **Side effects** | None (pure data) |
| **Error handling** | None |
| **Type annotations** | N/A |
| **Hardcoded values** | GraphQL schema structure |
| **Coupling** | None — leaf module |
| **Public surface** | 7 constants |

**Issues:**
- Tightly coupled to Wiki.js v2 GraphQL schema.
- `errorCode` field requested in responses but never used by `manager.py`.
- No validation of query structure.
- No documentation of what each query does.

### 3.3 `wiki_cli/pages/history.py` (59 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | History GraphQL query/mutation string constants |
| **Public API** | 3 string constants |
| **Side effects** | None (pure data) |
| **Error handling** | None |
| **Type annotations** | N/A |
| **Hardcoded values** | GraphQL schema structure |
| **Coupling** | None — leaf module |
| **Public surface** | 3 constants |

**Issues:**
- Same coupling concerns as `queries.py`.
- Could be merged with `queries.py` for simplicity.

---

## 4. AI Package

### 4.1 `wiki_cli/ai/agent.py` (574 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | AI agent loop: LLM tool-calling → PagesManager dispatch → result formatting |
| **Public API** | `WikiAgent(config)` with `run(prompt)`, `clear_history()` |
| **Side effects** | Network (LLM API + Wiki.js), filesystem (export/import), stdout (logging) |
| **Error handling** | Multi-layered: try/except per tool call, JSON decode errors, structured error dicts |
| **Type annotations** | ~80% |
| **Hardcoded values** | `MAX_CONTEXT_TOKENS=50_000`, token estimate `len(content)//4`, `SYSTEM_PROMPT`, `TOOL_LABELS` |
| **Coupling** | Very high: depends on `client`, `exceptions`, `models`, `pages`, `ai/config`, `ai/tools` |
| **Public surface** | 1 class, 2 methods, 4 constants |

**Issues:**
- Largest file in codebase (574 lines) — should be decomposed.
- Creates its own `WikiJSClient()` with no arguments — no dependency injection.
- Anti-pattern: `agent.__init__(config)` re-calls constructor on existing instance.
- Token estimation is a rough heuristic (`len(content) // 4`).
- No input validation on LLM-supplied arguments.
- `TOOL_LABELS` dict must stay in sync with `TOOLS` list manually.
- `_tool_fetch_page` returns `{"error": ...}` instead of `{"success": False, ...}` — inconsistent error format.
- `_tool_import_page` has a fragile hand-rolled YAML frontmatter parser.
- ANSI color constants duplicated from `cli.py`.

### 4.2 `wiki_cli/ai/cli.py` (365 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | AI interactive REPL with startup config, slash commands, editor integration |
| **Public API** | `ai_mode()` |
| **Side effects** | stdin/stdout, filesystem, subprocess (editor), `sys.exit` |
| **Error handling** | Catches `WikiJSError`, `EOFError`, `KeyboardInterrupt`, generic `Exception` |
| **Type annotations** | ~80% |
| **Hardcoded values** | `PAD=28`, default model `"gpt-4o"`, editor list, config paths |
| **Coupling** | Depends on `exceptions`, `ai/agent`, `ai/config` |
| **Public surface** | 1 function |

**Issues:**
- Config directory path `~/.config/wiki-cli/` duplicated from `config.py`.
- `_cmd_providers` re-calls `agent.__init__(config)` — anti-pattern.
- Default model `"gpt-4o"` hardcoded.
- External editor integration is fragile (subprocess, temp files).
- No graceful handling of missing `$EDITOR` / `$VISUAL`.

### 4.3 `wiki_cli/ai/config.py` (162 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | AI provider configuration, credential storage, model fetching |
| **Public API** | `AIConfig` dataclass, `get_saved_key()`, `save_key()`, `remove_key()`, `list_saved_keys()`, `fetch_models()` |
| **Side effects** | Filesystem (credential read/write), network (model list fetch), `chmod(0o600)` |
| **Error handling** | Swallows all exceptions silently (returns `{}` or `""`) |
| **Type annotations** | ~90% |
| **Hardcoded values** | `~/.config/wiki-cli/credentials.json`, `chmod 0o600`, all provider URLs, timeout=10 |
| **Coupling** | Depends on `httpx`, `openai` (lazy import) |
| **Public surface** | 1 dataclass, 5 functions, 1 constant |

**Issues:**
- `getpass` imported but never used (dead import).
- Config directory path duplicated in `cli.py`.
- All provider URLs hardcoded — no override mechanism.
- `get_client()` has no error handling for missing `openai` package.
- `fetch_models()` catches all exceptions broadly — hides bugs.

### 4.4 `wiki_cli/ai/tools.py` (393 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | OpenAI function-calling tool schemas |
| **Public API** | `TOOLS` (list of 17 tool definition dicts) |
| **Side effects** | None (pure data) |
| **Error handling** | None |
| **Type annotations** | N/A |
| **Hardcoded values** | Tool defaults: `isPublished=True`, `isPrivate=False`, `locale="en"`, `order_by="TITLE"` |
| **Coupling** | None — leaf module |
| **Public surface** | 1 list constant |

**Issues:**
- Tool names must stay in sync with `agent.py` dispatch table manually.
- No validation that tool schemas match actual `PagesManager` method signatures.
- Default values duplicated from `models.py` and `manager.py`.

---

## 5. Test Modules

### 5.1 `tests/conftest.py` (37 lines)

| Aspect | Detail |
|---|---|
| **Responsibility** | Shared pytest fixtures |
| **Fixtures** | `mock_manager`, `sample_page`, `sample_page_response` |
| **Issues** | `sample_page` and `sample_page_response` are unused; `INPUT_PATCH` constant unused |

### 5.2 Test files (17 top-level, 25 sub-modules)

| Test file | Module tested | Test count | Handler tested |
|---|---|---|---|
| `test_create_page.py` | `cli_pages.create_page` | 6 | create |
| `test_fetch_page.py` | `cli_pages.fetch_page` | 5 | fetch |
| `test_update_page.py` | `cli_pages.update_page` | 5 | update |
| `test_delete_page.py` | `cli_pages.delete_page` | 3 | delete |
| `test_list_pages.py` | `cli_pages.list_pages` | 5 | list |
| `test_search_pages.py` | `cli_pages.search_pages` | 5 | search |
| `test_browse_tree.py` | `cli_pages.browse_tree` | 4 | browse_tree |
| `test_move_rename.py` | `cli_pages.move_rename_page` | 4 | move_rename |
| `test_clone_page.py` | `cli_pages.clone_page` | 3 | clone |
| `test_export_page.py` | `cli_pages.export_page` | 3 | export |
| `test_import_page.py` | `cli_pages.import_page` | 4 | import |
| `test_view_history.py` | `cli_history.view_page_history` | 3 | view_history |
| `test_view_revision.py` | `cli_history.view_specific_revision` | 3 | view_revision |
| `test_diff_revisions.py` | `cli_history.diff_two_revisions` | 4 | diff |
| `test_restore_revision.py` | `cli_history.restore_revision` | 4 | restore |
| `test_connection.py` | `cli_system.test_connection` | 2 | connection |
| `test_main_menu.py` | `cli_main.main` | 4 | menu |
| **Total** | | **67** | |

**Issues:**
- Zero tests for `client.py`, `models.py`, `exceptions.py`, `utils.py`, `pages/manager.py`.
- Zero tests for entire `ai/` package.
- Duplicate test `test_delete_invalid_id` in `delete_page/validation.py` (never imported).
- `sample_pages` fixture from TEST_PLAN.md not implemented.
- `mock_input` fixture from TEST_PLAN.md not implemented.
- No CI configuration for automated test runs.
