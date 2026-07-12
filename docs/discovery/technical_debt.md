# Technical Debt Inventory

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. Debt Classification

Debt items are classified by category and severity:

- **Critical** — Blocks migration or causes production failures
- **High** — Significantly increases migration cost or risk
- **Medium** — Should be addressed but not blocking
- **Low** — Nice to fix, minimal impact

---

## 2. Architecture Debt

### TD-01: No dependency injection
- **Severity:** Critical
- **Location:** `wiki_cli/ai/agent.py:68`
- **Description:** `WikiAgent.__init__` creates its own `WikiJSClient()` with no arguments, bypassing any dependency injection. Cannot inject mock clients for testing or alternative transports.
- **Impact:** Makes unit testing impossible without monkeypatching; prevents multi-transport support.

### TD-02: Anti-pattern — re-calling `__init__`
- **Severity:** High
- **Location:** `wiki_cli/ai/cli.py:244`
- **Description:** `_cmd_providers` calls `agent.__init__(config)` on an existing instance instead of creating a new `WikiAgent`. This re-initializes internal state and creates new `WikiJSClient`/`PagesManager` instances.
- **Impact:** Unpredictable behavior, leaked side effects, violates object lifecycle expectations.

### TD-03: Global side effect at import time
- **Severity:** High
- **Location:** `wiki_cli/client.py:14`
- **Description:** `load_dotenv()` is called at module import time, modifying `os.environ` globally. Cannot be disabled or deferred.
- **Impact:** Affects all modules that import `client.py`; cannot control when env loading happens; breaks test isolation.

### TD-04: No abstraction layers
- **Severity:** High
- **Location:** All modules
- **Description:** No interfaces, protocols, or abstract base classes. All modules depend on concrete implementations.
- **Impact:** Cannot swap Wiki.js for another wiki system; cannot swap `gql` for another transport; cannot test without real implementations.

### TD-05: Monolithic file sizes
- **Severity:** Medium
- **Location:** `ai/agent.py` (574 lines), `cli_pages.py` (389 lines), `ai/cli.py` (365 lines)
- **Description:** Three files exceed 350 lines with multiple responsibilities.
- **Impact:** Hard to navigate, test, and refactor; increases merge conflict risk.

---

## 3. Code Debt

### TD-06: Dead import
- **Severity:** Low
- **Location:** `wiki_cli/ai/config.py:15`
- **Description:** `getpass` is imported but never used.
- **Impact:** Minor — confuses readers, adds unnecessary dependency.

### TD-07: Dead fields in model
- **Severity:** Low
- **Location:** `wiki_cli/models.py` — `PageVersion.publishStartDate`, `PageVersion.publishEndDate`
- **Description:** Two fields defined in `PageVersion` but never populated by any code path.
- **Impact:** Misleading API surface; consumers may expect these fields to have data.

### TD-08: Inconsistent error formats
- **Severity:** Medium
- **Location:** `wiki_cli/ai/agent.py` — `_tool_fetch_page` returns `{"error": ...}` while other tools return `{"success": False, "error": ...}`
- **Description:** Error return format varies across tool handlers.
- **Impact:** LLM and downstream code must handle multiple error formats; fragile error handling.

### TD-09: Fragile frontmatter parser
- **Severity:** High
- **Location:** `wiki_cli/cli_pages.py:345-355`, `wiki_cli/ai/agent.py:481-489`
- **Description:** Hand-rolled YAML frontmatter parser that cannot handle multi-line values, quoted strings, colons in values, or nested structures.
- **Impact:** Data corruption or import failure on non-trivial Markdown files.

### TD-10: No input validation on LLM arguments
- **Severity:** High
- **Location:** `wiki_cli/ai/agent.py` — all `_tool_*` methods
- **Description:** Tool handlers trust LLM-supplied values entirely. No validation for negative page IDs, empty paths, invalid locales, or malicious content.
- **Impact:** Potential security issues, data corruption, confusing error messages.

### TD-11: Duplicate ANSI color constants
- **Severity:** Low
- **Location:** `wiki_cli/ai/agent.py:18-22`, `wiki_cli/ai/cli.py:33-39`
- **Description:** ANSI escape codes (`R`, `B`, `D`, `C`, `G`, `Y`, `X`) defined independently in both files.
- **Impact:** Maintenance burden; must update both files when adding/changing colors.

### TD-12: Hardcoded configuration values
- **Severity:** Medium
- **Location:** Multiple files
- **Description:** 15+ hardcoded values across the codebase: `PAGE_SIZE=20`, `retries=3`, `locale="en"`, `editor="markdown"`, `MAX_CONTEXT_TOKENS=50_000`, `PAD=28`, `sys.exit(1)`, version `"0.1.0"`, etc.
- **Impact:** Cannot customize behavior without code changes; violates "configurable through Git" principle.

### TD-13: Duplicated config directory path
- **Severity:** Medium
- **Location:** `wiki_cli/ai/config.py:25-26`, `wiki_cli/ai/cli.py:40`
- **Description:** `~/.config/wiki-cli/` path defined independently in both files.
- **Impact:** If path changes, must update both locations; risk of inconsistency.

### TD-14: Token estimation heuristic
- **Severity:** Medium
- **Location:** `wiki_cli/ai/agent.py:99,102`
- **Description:** Token count estimated as `len(content) // 4` — a rough heuristic with no documented justification.
- **Impact:** May over/under-estimate token usage, leading to context window overflow or unnecessary trimming.

---

## 4. Testing Debt

### TD-15: Zero tests for core modules
- **Severity:** Critical
- **Location:** `tests/`
- **Description:** No tests exist for `client.py`, `models.py`, `exceptions.py`, `utils.py`, `pages/manager.py`. These are the foundational modules.
- **Impact:** Changes to core modules cannot be validated; regression risk is high.

### TD-16: Zero tests for AI package
- **Severity:** Critical
- **Location:** `tests/`
- **Description:** No tests exist for `ai/agent.py`, `ai/cli.py`, `ai/config.py`, `ai/tools.py`. Only aspirational examples in `AI_INTEGRATION.md`.
- **Impact:** AI functionality is completely untested; any change could break the assistant silently.

### TD-17: No error path tests
- **Severity:** High
- **Location:** All test files
- **Description:** No test verifies behavior when `PagesManager` raises `WikiJSError`. All happy-path only.
- **Impact:** Error handling code is untested; regressions in error paths undetected.

### TD-18: Unused fixtures in conftest
- **Severity:** Low
- **Location:** `tests/conftest.py`
- **Description:** `sample_page`, `sample_page_response`, and `INPUT_PATCH` are defined but unused.
- **Impact:** Dead code in test infrastructure.

### TD-19: Duplicate test never imported
- **Severity:** Low
- **Location:** `tests/delete_page/validation.py`
- **Description:** `test_delete_invalid_id` is defined but never imported by `test_delete_page.py`.
- **Impact:** Dead test code; test count is inflated.

### TD-20: Missing tests from TEST_PLAN
- **Severity:** Medium
- **Location:** `TEST_PLAN.md`
- **Description:** `sample_pages` fixture, `mock_input` fixture, `test_list_pagination`, `test_menu_press_enter_to_continue` are specified in TEST_PLAN but not implemented.
- **Impact:** TEST_PLAN is out of sync with actual test coverage.

---

## 5. Documentation Debt

### TD-21: STRUCTURE.md references non-existent directory
- **Severity:** Medium
- **Location:** `STRUCTURE.md`
- **Description:** References a `docs/` directory with 19 documentation files that do not exist on disk.
- **Impact:** Misleading documentation; new contributors may search for non-existent files.

### TD-22: AI_INTEGRATION.md contains non-existent tests
- **Severity:** Medium
- **Location:** `AI_INTEGRATION.md`
- **Description:** Contains test examples (`test_ai_tools.py`, `test_ai_agent.py`) that are not implemented.
- **Impact:** Creates false impression of test coverage.

### TD-23: No architecture decision records
- **Severity:** Medium
- **Location:** Project root
- **Description:** No ADRs exist. Decisions are not documented with rationale.
- **Impact:** New contributors cannot understand why certain choices were made.

### TD-24: No CHANGELOG.md
- **Severity:** Medium
- **Location:** Project root
- **Description:** No changelog to track version history.
- **Impact:** Users cannot see what changed between versions.

---

## 6. Configuration Debt

### TD-25: Inconsistent dependency declarations
- **Severity:** Medium
- **Location:** `requirements.txt`, `pyproject.toml`
- **Description:** `httpx` in pyproject.toml optional deps but missing from requirements.txt. `openai` is hard dep in requirements.txt but optional in pyproject.toml.
- **Impact:** Different install paths may result in missing dependencies.

### TD-26: No version pins
- **Severity:** Medium
- **Location:** `requirements.txt`, `pyproject.toml`
- **Description:** All dependencies use `>=` without upper bounds or exact pins.
- **Impact:** Builds are not reproducible; breaking changes in upstream packages can break the project silently.

### TD-27: No lock file
- **Severity:** Medium
- **Location:** Project root
- **Description:** No `requirements.lock`, `pip-compile` output, or similar.
- **Impact:** Dependency resolution may differ across environments.

### TD-28: No CI configuration
- **Severity:** High
- **Location:** Project root
- **Description:** No `.github/workflows/`, `Makefile`, `tox.ini`, or `noxfile.py` for automated testing.
- **Impact:** No automated quality gates; regressions can be merged undetected.

---

## 7. Debt Summary

| Category | Critical | High | Medium | Low | Total |
|---|---|---|---|---|---|
| Architecture | 1 | 3 | 1 | 0 | **5** |
| Code | 0 | 3 | 5 | 4 | **12** |
| Testing | 2 | 1 | 2 | 3 | **8** |
| Documentation | 0 | 0 | 4 | 0 | **4** |
| Configuration | 0 | 1 | 4 | 0 | **5** |
| **Total** | **3** | **8** | **16** | **7** | **34** |

### Debt hotspots (files with most issues)

| File | Debt items |
|---|---|
| `wiki_cli/ai/agent.py` | TD-01, TD-08, TD-10, TD-14 |
| `wiki_cli/ai/cli.py` | TD-02, TD-13 |
| `wiki_cli/client.py` | TD-03 |
| `wiki_cli/cli_pages.py` | TD-09, TD-05 |
| `wiki_cli/ai/config.py` | TD-06, TD-13 |
| `tests/` | TD-15, TD-16, TD-17, TD-18, TD-19, TD-20 |

---

## 8. Estimated Remediation Cost

| Severity | Count | Estimated effort |
|---|---|---|
| Critical | 3 | 2–3 days each |
| High | 8 | 0.5–1 day each |
| Medium | 16 | 0.25–0.5 day each |
| Low | 7 | < 0.25 day each |
| **Total** | **34** | **~12–18 days** |

Note: This estimate is for debt remediation only, not for the full Level 5 transformation.
