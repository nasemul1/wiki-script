# Recommendations

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. Priority Matrix

Recommendations are ordered by priority (P0 = do first, P3 = do last).

| # | Recommendation | Priority | Addresses | Effort |
|---|---|---|---|---|
| REC-01 | Establish `wiki_cli` backward compatibility contract | P0 | R1, R12 | 0.5 day |
| REC-02 | Add dependency injection to `WikiAgent` | P0 | TD-01, TD-02 | 1 day |
| REC-03 | Fix `load_dotenv()` import-time side effect | P0 | TD-03 | 0.5 day |
| REC-04 | Write tests for core modules (`client`, `models`, `exceptions`, `utils`) | P0 | TD-15 | 2 days |
| REC-05 | Write tests for `pages/manager.py` | P1 | TD-15 | 2 days |
| REC-06 | Fix inconsistent error formats in AI tools | P1 | TD-08 | 0.5 day |
| REC-07 | Replace hand-rolled frontmatter parser with library | P1 | TD-09 | 1 day |
| REC-08 | Add input validation to AI tool handlers | P1 | TD-10 | 1 day |
| REC-09 | Consolidate hardcoded constants into config | P1 | TD-12, TD-13 | 1 day |
| REC-10 | Fix dependency declarations in `requirements.txt` and `pyproject.toml` | P1 | TD-25 | 0.5 day |
| REC-11 | Add CI pipeline (GitHub Actions) | P1 | TD-28 | 1 day |
| REC-12 | Write tests for AI package | P2 | TD-16 | 3 days |
| REC-13 | Add error path tests for all handlers | P2 | TD-17 | 2 days |
| REC-14 | Update `STRUCTURE.md` and `AI_INTEGRATION.md` | P2 | TD-21, TD-22 | 0.5 day |
| REC-15 | Add version pins and lock file | P2 | TD-26, TD-27 | 0.5 day |
| REC-16 | Create Architecture Decision Records (ADRs) | P2 | TD-23 | 1 day |
| REC-17 | Add `CHANGELOG.md` | P2 | TD-24 | 0.5 day |
| REC-18 | Remove dead code (unused import, dead fields, unused fixtures) | P3 | TD-06, TD-07, TD-18, TD-19 | 0.5 day |
| REC-19 | Decompose large files (`agent.py`, `cli_pages.py`, `ai/cli.py`) | P3 | TD-05 | 2 days |
| REC-20 | Add type stubs or `mypy --strict` for new code | P3 | General | 1 day |

---

## 2. Detailed Recommendations

### REC-01: Establish backward compatibility contract (P0)

**What:** Create a `COMPATIBILITY.md` that documents:
- All public import paths that must remain valid.
- All CLI commands that must continue to work.
- All Pydantic model fields that must remain available.
- Deprecation policy (one phase warning before removal).

**Why:** The master plan mandates backward compatibility during every phase. Without a contract, regressions are inevitable.

**How:**
- Write `COMPATIBILITY.md` with explicit lists.
- Add a `test_compat.py` test that verifies all public imports work.
- Run this test in CI on every PR.

**Dependencies:** None.
**Risk:** Low.

---

### REC-02: Add dependency injection to `WikiAgent` (P0)

**What:** Refactor `WikiAgent.__init__` to accept optional `WikiJSClient` and `PagesManager` instances instead of creating them internally.

**Why:** This is the #1 blocker for testing the AI agent and for supporting multiple transports.

**How:**
```python
class WikiAgent:
    def __init__(
        self,
        config: AIConfig,
        client: WikiJSClient | None = None,
        pages: PagesManager | None = None,
    ):
        self.config = config
        self.client = client or WikiJSClient()
        self.pages = pages or PagesManager(self.client)
        ...
```

Also fix the `agent.__init__(config)` anti-pattern in `ai/cli.py` by creating a new instance instead.

**Dependencies:** None.
**Risk:** Low — additive change, existing callers unaffected.

---

### REC-03: Fix `load_dotenv()` import-time side effect (P0)

**What:** Move `load_dotenv()` from module-level to an explicit initialization call.

**Why:** Import-time side effects break test isolation and make behavior unpredictable.

**How:**
```python
# client.py
_loaded = False

def _ensure_env():
    global _loaded
    if not _loaded:
        load_dotenv()
        _loaded = True

class WikiJSClient:
    def __init__(self, ...):
        _ensure_env()
        ...
```

Or better: accept `url` and `api_key` as required parameters (no env fallback).

**Dependencies:** None.
**Risk:** Medium — existing callers rely on env loading at import time.

---

### REC-04: Write tests for core modules (P0)

**What:** Add unit tests for:
- `wiki_cli/client.py` — initialization, execute, error handling
- `wiki_cli/models.py` — validation, defaults, serialization
- `wiki_cli/exceptions.py` — message formatting, error chaining
- `wiki_cli/utils.py` — table formatting, input prompting

**Why:** These are foundational modules with zero test coverage. Any change to them could break everything.

**How:**
- Mock `gql` transport for `client.py` tests.
- Test Pydantic model creation, validation, and edge cases.
- Test `WikiJSError.__str__` with various error formats.
- Test `print_page_table` and `print_history_table` with `capsys`.

**Dependencies:** REC-02 (for `WikiAgent` testing, but not blocking).
**Risk:** Low.

---

### REC-05: Write tests for `pages/manager.py` (P1)

**What:** Add unit tests for all 14 `PagesManager` methods.

**Why:** `PagesManager` is the core business logic class with zero tests. It handles all Wiki.js operations.

**How:**
- Mock `WikiJSClient.execute()` with fixture data.
- Test success paths, error paths, and edge cases.
- Test `_parse_response()` and `_parse_single_page()` with malformed data.

**Dependencies:** None.
**Risk:** Low.

---

### REC-06: Fix inconsistent error formats in AI tools (P1)

**What:** Standardize all `_tool_*` methods to return `{"success": bool, "data": ..., "error": ...}` format.

**Why:** Inconsistent error formats make LLM tool-calling unreliable and error handling fragile.

**How:**
- Define a `ToolResult` TypedDict or Pydantic model.
- Update all `_tool_*` methods to use it.
- Update `_execute_tool` to validate the format.

**Dependencies:** None.
**Risk:** Low — internal change, LLM sees the same text.

---

### REC-07: Replace hand-rolled frontmatter parser (P1)

**What:** Replace the custom YAML frontmatter parser with a library (e.g., `python-frontmatter` or `pyyaml`).

**Why:** The current parser is fragile and will fail on non-trivial Markdown files.

**How:**
- Add `python-frontmatter` to dependencies.
- Replace hand-rolled parsing in `cli_pages.py` and `ai/agent.py`.
- Add tests for edge cases (multi-line values, special characters).

**Dependencies:** REC-10 (dependency declaration fix).
**Risk:** Low.

---

### REC-08: Add input validation to AI tool handlers (P1)

**What:** Validate all LLM-supplied arguments before passing to `PagesManager`.

**Why:** Untrusted input from LLM could cause errors, data corruption, or security issues.

**How:**
- Add Pydantic models for each tool's arguments.
- Validate in `_execute_tool` before dispatch.
- Return clear error messages for invalid arguments.

**Dependencies:** None.
**Risk:** Low.

---

### REC-09: Consolidate hardcoded constants (P1)

**What:** Move all hardcoded values to a central configuration module.

**Why:** 15+ hardcoded values scattered across the codebase prevent customization.

**How:**
- Create `wiki_cli/config.py` with all constants.
- Import from config in all modules.
- Support environment variable overrides where appropriate.

**Dependencies:** None.
**Risk:** Low.

---

### REC-10: Fix dependency declarations (P1)

**What:** Reconcile `requirements.txt` and `pyproject.toml`.

**Why:** Inconsistent dependencies cause install failures and confusion.

**How:**
- Make `pyproject.toml` the single source of truth.
- Generate `requirements.txt` from `pyproject.toml` if needed.
- Add `httpx` to core dependencies.
- Make `openai` optional in both files.

**Dependencies:** None.
**Risk:** Low.

---

### REC-11: Add CI pipeline (P1)

**What:** Set up GitHub Actions for automated testing, linting, and type checking.

**Why:** No automated quality gates exist; regressions can be merged undetected.

**How:**
- Create `.github/workflows/ci.yml`.
- Run `pytest`, `mypy`, `ruff` on every PR.
- Run on Python 3.10, 3.11, 3.12.
- Cache dependencies for speed.

**Dependencies:** REC-04, REC-05 (need tests to run).
**Risk:** Low.

---

### REC-12: Write tests for AI package (P2)

**What:** Add unit tests for `ai/agent.py`, `ai/cli.py`, `ai/config.py`, `ai/tools.py`.

**Why:** Zero tests exist for the entire AI package. This is the most complex part of the codebase.

**How:**
- Mock LLM responses for `agent.py` tests.
- Mock file I/O for `cli.py` tests.
- Mock HTTP for `config.py` tests.
- Validate tool schemas against `PagesManager` method signatures.

**Dependencies:** REC-02 (dependency injection).
**Risk:** Medium — AI testing is inherently complex.

---

### REC-13: Add error path tests (P2)

**What:** Add tests for `WikiJSError` raised by `PagesManager` methods in all handlers.

**Why:** Error handling code is untested; regressions in error paths are undetected.

**How:**
- Add `side_effect=WikiJSError(...)` to mock manager methods.
- Verify error messages are displayed correctly.
- Verify the menu loop continues after errors.

**Dependencies:** None.
**Risk:** Low.

---

### REC-14: Update documentation (P2)

**What:** Fix inaccuracies in `STRUCTURE.md` and `AI_INTEGRATION.md`.

**Why:** Misleading documentation confuses contributors and creates false impressions of coverage.

**How:**
- Remove references to non-existent `docs/` directory in `STRUCTURE.md`.
- Mark AI test examples as "planned" in `AI_INTEGRATION.md`.
- Add badges for test coverage and CI status.

**Dependencies:** None.
**Risk:** Low.

---

### REC-15: Add version pins and lock file (P2)

**What:** Pin dependency versions and generate a lock file.

**Why:** Builds are not reproducible; breaking changes in upstream packages can break the project.

**How:**
- Use `pip-compile` (from `pip-tools`) to generate `requirements.lock`.
- Add upper bounds to critical dependencies.
- Run `pip-compile` in CI to verify lock file is current.

**Dependencies:** REC-10.
**Risk:** Low.

---

### REC-16: Create Architecture Decision Records (P2)

**What:** Create `docs/architecture/adr/` directory with ADR templates.

**Why:** Decisions are not documented with rationale; future developers cannot understand why choices were made.

**How:**
- Create `docs/architecture/adr/000-template.md`.
- Document existing decisions (e.g., "Use Pydantic v2", "Use gql for GraphQL").
- Require ADR for all significant architectural decisions.

**Dependencies:** None.
**Risk:** Low.

---

### REC-17: Add CHANGELOG.md (P2)

**What:** Create a changelog following Keep a Changelog format.

**Why:** No version history tracking; users cannot see what changed between versions.

**How:**
- Create `CHANGELOG.md` with entries for existing versions.
- Update on every merge to `main`.
- Use semantic versioning.

**Dependencies:** None.
**Risk:** Low.

---

### REC-18: Remove dead code (P3)

**What:** Clean up unused imports, dead fields, unused fixtures, and duplicate tests.

**Why:** Dead code confuses readers and inflates metrics.

**How:**
- Remove `getpass` import from `ai/config.py`.
- Remove `publishStartDate`/`publishEndDate` from `PageVersion`.
- Remove unused fixtures from `conftest.py`.
- Remove duplicate test in `delete_page/validation.py`.

**Dependencies:** None.
**Risk:** Low.

---

### REC-19: Decompose large files (P3)

**What:** Split `ai/agent.py` (574 lines), `cli_pages.py` (389 lines), and `ai/cli.py` (365 lines) into smaller modules.

**Why:** Large files are hard to navigate, test, and refactor.

**How:**
- `ai/agent.py` → `ai/agent.py` (core loop), `ai/tools_dispatch.py` (tool handlers), `ai/prompts.py` (system prompt).
- `cli_pages.py` → `cli_pages_create.py`, `cli_pages_read.py`, `cli_pages_update.py`, `cli_pages_delete.py`, `cli_pages_io.py`.
- `ai/cli.py` → `ai/cli.py` (REPL), `ai/cli_config.py` (startup config), `ai/cli_editor.py` (editor integration).

**Dependencies:** None.
**Risk:** Medium — many imports to update.

---

### REC-20: Add type checking (P3)

**What:** Enable `mypy --strict` for new code under `wiki_platform/`.

**Why:** Type checking catches bugs at development time and improves code quality.

**How:**
- Add `mypy` to dev dependencies.
- Configure `mypy.ini` with strict settings for `wiki_platform/`.
- Run in CI on every PR.

**Dependencies:** None.
**Risk:** Low.

---

## 3. Implementation Order

The recommended implementation order for Phase 9 (Implementation) is:

### Pre-implementation (before Phase 9)
1. REC-01 (compatibility contract)
2. REC-11 (CI pipeline)
3. REC-16 (ADRs)
4. REC-17 (CHANGELOG)

### Milestone 1: Core stability
1. REC-02 (dependency injection)
2. REC-03 (fix load_dotenv)
3. REC-04 (core module tests)
4. REC-05 (manager tests)
5. REC-09 (consolidate constants)
6. REC-10 (fix dependencies)
7. REC-18 (remove dead code)

### Milestone 2: AI hardening
1. REC-06 (error format standardization)
2. REC-07 (frontmatter parser)
3. REC-08 (input validation)
4. REC-12 (AI tests)
5. REC-13 (error path tests)
6. REC-19 (decompose large files)

### Milestone 3: Documentation & polish
1. REC-14 (update docs)
2. REC-15 (version pins)
3. REC-20 (type checking)

---

## 4. Success Criteria

Phase 0 (Discovery) is complete when:

- [x] All 19 source files analyzed
- [x] All 17 test files analyzed
- [x] All configuration files analyzed
- [x] Technical debt inventory (34 items) documented
- [x] Migration risks (15 items) documented
- [x] Recommendations (20 items) prioritized
- [x] Implementation order defined
- [ ] Phase 0 status updated in `plan.md` (next step)
