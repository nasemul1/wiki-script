# Migration Risks

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. Risk Register

Risks are ranked by composite score (Likelihood × Impact).

| # | Risk | Likelihood | Impact | Score | Category |
|---|---|---|---|---|---|
| R1 | Breaking existing CLI during repository restructure | High (4) | Critical (5) | **20** | Migration |
| R2 | AI provider API changes break agent | High (4) | High (4) | **16** | External |
| R3 | Prompt injection via Wiki.js content | Medium (3) | Critical (5) | **15** | Security |
| R4 | PostgreSQL schema migration failures | Medium (3) | Critical (5) | **15** | Data |
| R5 | Workflow state machine deadlocks | Medium (3) | High (4) | **12** | Architecture |
| R6 | Cost overruns from LLM usage | Medium (3) | High (4) | **12** | Operational |
| R7 | Model version drift breaks agents | High (4) | High (4) | **16** | External |
| R8 | GitHub rate limits during sync | Medium (3) | Medium (3) | **9** | External |
| R9 | Data loss from buggy agent writes | Low (2) | Critical (5) | **10** | Data |
| R10 | Jenkins flakiness blocks merges | High (4) | Medium (3) | **12** | Operational |
| R11 | Circular dependencies in new architecture | Medium (3) | High (4) | **12** | Architecture |
| R12 | Breaking backward compatibility during phased moves | High (4) | Critical (5) | **20** | Migration |
| R13 | Test suite becomes unmaintainable during transition | Medium (3) | High (4) | **12** | Testing |
| R14 | Configuration drift between `requirements.txt` and `pyproject.toml` | Medium (3) | Medium (3) | **9** | Config |
| R15 | Loss of institutional knowledge during refactoring | Medium (3) | Medium (3) | **9** | Process |

---

## 2. Detailed Risk Analysis

### R1 — Breaking existing CLI during repository restructure (Score: 20)

**Description:** Moving modules from `wiki_cli/` to `wiki_platform/` or reorganizing imports could break the existing `wiki-cli` entry point and all 67 existing tests.

**Trigger:** Renaming directories, changing `__init__.py` exports, or altering import paths without proper re-exports.

**Impact:** Users lose access to working CLI; CI pipeline fails; trust in project eroded.

**Mitigation:**
- Keep `wiki_cli` package as a thin compatibility shim with re-exports.
- Run full test suite after every file move.
- Never delete `wiki_cli/` — only deprecate.
- Use import redirects (re-export from old paths).

**Residual risk:** Low if mitigation is followed.

---

### R2 — AI provider API changes break agent (Score: 16)

**Description:** OpenAI, OpenRouter, Groq, or Mistral may change their API schemas, deprecate models, or alter rate limits.

**Trigger:** Provider API version bump, model deprecation, or response format change.

**Impact:** AI assistant stops working; tool calls fail; conversation history corrupted.

**Mitigation:**
- Pin model versions in profiles (Git-versioned).
- Implement model fallback chains.
- Add response validation layer.
- Monitor provider changelogs.

**Residual risk:** Medium — external dependency不可完全控制.

---

### R3 — Prompt injection via Wiki.js content (Score: 15)

**Description:** Malicious content in Wiki.js pages could manipulate the AI agent into performing unintended actions (e.g., deleting pages, leaking credentials).

**Trigger:** User creates a page containing prompt injection text that the AI agent processes.

**Impact:** Agent performs unauthorized Wiki.js operations; data loss; credential exposure.

**Mitigation:**
- Separate Author and Critic agents (different system prompts).
- Content sanitization before LLM processing.
- Approval gates for destructive operations.
- Eval suite specifically for prompt injection scenarios.

**Residual risk:** Medium — prompt injection is an active research area.

---

### R4 — PostgreSQL schema migration failures (Score: 15)

**Description:** Alembic migrations may fail due to data type mismatches, constraint violations, or backward-incompatible schema changes.

**Trigger:** Schema change that cannot be applied to existing data; migration script bug.

**Impact:** Runtime state unavailable; workflow engine fails; audit trail lost.

**Mitigation:**
- Backward-compatible migrations only (add columns, don't remove).
- Blue/green deployment for schema changes.
- Automated rollback scripts.
- Test migrations against production-like data.

**Residual risk:** Low with proper migration discipline.

---

### R5 — Workflow state machine deadlocks (Score: 12)

**Description:** Workflow transitions may reach a state where no further transitions are possible but the workflow is not in a terminal state.

**Trigger:** Missing transition definition, guard condition that never evaluates to true, or circular dependency in states.

**Impact:** Workflows stuck in intermediate state; approvals blocked; no automated recovery.

**Mitigation:**
- Formal reachability analysis on all workflow definitions.
- Timeout transitions for non-terminal states.
- Watchdog jobs that detect and alert on stuck workflows.
- Dead-end state detectors.

**Residual risk:** Low with formal verification.

---

### R6 — Cost overruns from LLM usage (Score: 12)

**Description:** AI agents making excessive API calls, using expensive models for routine tasks, or running in infinite loops.

**Trigger:** Unbounded agent loops, missing cost caps, or model selection defaulting to expensive options.

**Impact:** Unexpected bills; budget exhaustion; service disruption.

**Mitigation:**
- Per-workflow cost budgets (hard caps).
- Model routing with cost optimization.
- Escalation to cheaper models or human review.
- Real-time cost monitoring and alerts.

**Residual risk:** Low with proper cost controls.

---

### R7 — Model version drift breaks agents (Score: 16)

**Description:** Upgrading model versions (e.g., `gpt-4o` → `gpt-5`) may change behavior, tool-calling format, or response quality.

**Trigger:** Model provider updates default model; agent profile not pinned.

**Impact:** Agent behavior changes unexpectedly; tool calls fail; quality degrades.

**Mitigation:**
- Pin model versions in Git-versioned profiles.
- Snapshot evaluation suite that runs before model upgrades.
- A/B testing framework for model changes.
- Rollback capability for model profile changes.

**Residual risk:** Medium — model upgrades are inherently risky.

---

### R8 — GitHub rate limits during sync (Score: 9)

**Description:** GitHub API rate limits (5000 requests/hour for authenticated users) may be exceeded during large syncs or repeated operations.

**Trigger:** Bulk page sync, frequent policy checks, or parallel agent operations.

**Impact:** Sync failures; delayed deployments; temporary inability to push changes.

**Mitigation:**
- ETag caching and conditional requests.
- Request queuing with retry and backoff.
- Batch operations where possible.
- Monitor rate limit headers.

**Residual risk:** Low.

---

### R9 — Data loss from buggy agent writes (Score: 10)

**Description:** AI agent could overwrite or delete Wiki.js pages due to bugs in tool handlers or incorrect LLM arguments.

**Trigger:** Agent bug, LLM hallucination, or incorrect argument parsing.

**Impact:** Wiki.js pages lost; knowledge base corrupted; recovery from Wiki.js backups required.

**Mitigation:**
- Dry-run mode for destructive operations.
- Approval gates for page deletes and updates.
- Wiki.js automated backups.
- Version history for all changes.

**Residual risk:** Low with approval gates.

---

### R10 — Jenkins flakiness blocks merges (Score: 12)

**Description:** Jenkins pipeline may fail due to infrastructure issues, flaky tests, or external service unavailability.

**Trigger:** Network timeout, test order dependency, or service outage.

**Impact:** Merge blocked; developer velocity reduced; frustration.

**Mitigation:**
- Retry mechanisms for transient failures.
- Quarantine flaky tests.
- Separate fast (unit) vs slow (integration) test suites.
- Alert on repeated failures.

**Residual risk:** Medium — CI flakiness is common.

---

### R11 — Circular dependencies in new architecture (Score: 12)

**Description:** As `wiki_platform/` grows, circular imports between modules may emerge.

**Trigger:** Module A imports from B which imports from A.

**Impact:** Import errors; runtime failures; architecture degradation.

**Mitigation:**
- Enforce dependency direction (core → integrations → CLI).
- Use dependency injection at boundaries.
- Regular architecture reviews.
- Automated circular dependency detection.

**Residual risk:** Low with discipline.

---

### R12 — Breaking backward compatibility during phased moves (Score: 20)

**Description:** Each phase must preserve backward compatibility, but cumulative changes may break edge cases.

**Trigger:** Import path changes, API signature changes, or behavior changes.

**Impact:** Existing scripts break; users cannot upgrade; trust eroded.

**Mitigation:**
- Deprecation warnings one phase in advance.
- Compatibility shims with `DeprecationWarning`.
- Full test suite for existing functionality.
- Versioned API surfaces.

**Residual risk:** Low with strict discipline.

---

### R13 — Test suite becomes unmaintainable (Score: 12)

**Description:** During transition, tests may need to cover both old and new APIs, leading to duplication and confusion.

**Trigger:** Parallel test suites for `wiki_cli` and `wiki_platform`.

**Impact:** Test maintenance burden; confusion about which tests to run; coverage gaps.

**Mitigation:**
- Clear test directory structure (`unit/`, `integration/`, `workflow/`, etc.).
- Separate test suites for old and new APIs.
- Shared fixtures and helpers.
- Regular test suite cleanup.

**Residual risk:** Low.

---

### R14 — Configuration drift (Score: 9)

**Description:** `requirements.txt` and `pyproject.toml` may diverge further during migration.

**Trigger:** Adding dependencies to one file but not the other.

**Impact:** Install failures; missing dependencies; inconsistent environments.

**Mitigation:**
- Single source of truth (`pyproject.toml`).
- Generate `requirements.txt` from `pyproject.toml`.
- CI check for consistency.

**Residual risk:** Low.

---

### R15 — Loss of institutional knowledge (Score: 9)

**Description:** During refactoring, context about why certain decisions were made may be lost.

**Trigger:** Files moved, comments deleted, or documentation not updated.

**Impact:** Future developers repeat past mistakes; architecture degrades.

**Mitigation:**
- Architecture Decision Records (ADRs).
- Document decisions in `docs/architecture/adr/`.
- Preserve comments that explain "why", not "what".

**Residual risk:** Low.

---

## 3. Risk Matrix

| | Impact: Low (1) | Impact: Medium (3) | Impact: High (4) | Impact: Critical (5) |
|---|---|---|---|---|
| **Likelihood: High (4)** | | R10 | R2, R7 | R1, R12 |
| **Likelihood: Medium (3)** | | R8, R14, R15 | R5, R6, R11, R13 | R3, R4 |
| **Likelihood: Low (2)** | | | | R9 |

---

## 4. Risk Ownership

| Risk | Owner | Review cadence |
|---|---|---|
| R1, R12 | Lead Architect | Per phase |
| R2, R7 | AI Systems Architect | Per model change |
| R3 | Security Lead | Monthly |
| R4, R9 | Database Lead | Per migration |
| R5, R6 | Workflow Lead | Per workflow change |
| R8, R10 | DevOps Lead | Weekly |
| R11 | Lead Architect | Per phase |
| R13 | QA Lead | Per phase |
| R14, R15 | Lead Architect | Per phase |
