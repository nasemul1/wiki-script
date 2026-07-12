# Wiki Intelligence Platform — Master Transformation Plan

> **Single source of truth.** Any AI agent, engineer, reviewer, or auditor working on
> this repository MUST read this file first. When this document and a phase
> document conflict, the phase document wins for that phase's scope; otherwise
> this plan is authoritative.

---

## 0. Document Control

| Field | Value |
|---|---|
| Plan version | 1.0.0 |
| Repository | `wiki-script` |
| Source product | Wiki.js CLI (Level 1) |
| Target product | **Wiki Intelligence Platform** (Level 5) |
| Owner | Lead Architect |
| Status | **Planning — Phases 0–8 to be completed; Phase 9+ gated on approval** |
| Last updated | 2026-07-13 |

### Revision history

| Version | Date | Author | Notes |
|---|---|---|---|
| 1.0.0 | 2026-07-13 | Lead Architect | Initial master plan, replaces prior `plan.md` |

---

## 1. Executive Summary

The `wiki-script` repository currently implements a **Level 1** terminal client for
Wiki.js (CRUD + history + a single AI assistant). The target is a **Level 5
Intelligence Platform** that combines:

- Wiki.js (knowledge store)
- Git / GitHub (versioned intelligence + change provenance)
- Jenkins (CI/CD + automated validation)
- PostgreSQL (runtime state, audit, observability)
- Jira (work intake + traceability)
- AI Agents (specialized roles)
- Model Routing (multi-provider, cost-aware, fallback)
- Workflow Engine (document / requirement / architecture / employee review)
- Evaluations (regression + quality + cost)
- Human Review (approval gates)
- Versioned Policies (governance)

The transformation is **non-breaking**: every existing CLI command keeps working
across every milestone until an explicit deprecation notice is published.

### Vision statement

> A versioned, governed, AI-augmented knowledge and workflow platform where
> Git is the source of intelligence, Jenkins validates change, PostgreSQL stores
> runtime state, Wiki.js stores knowledge, agents perform specialized roles, and
> humans approve important decisions.

### Core principles

1. **Git defines intelligence** — prompts, policies, agent definitions, and model
   profiles live in version control.
2. **Jenkins validates changes** — every change is gated by automated tests,
   evals, and policy checks.
3. **PostgreSQL stores runtime state** — workflow runs, agent runs, findings,
   approvals, costs, audit logs.
4. **Wiki.js stores knowledge** — documents, decisions, generated artifacts.
5. **AI agents perform specialized roles** — Author, Critic, Judge, Synthesizer,
   Verifier, Researcher, Test Generator, Evidence Collector.
6. **Humans approve important decisions** — approval gates are first-class.
7. **Every AI failure becomes a regression test.**
8. **Every production behavior is traceable** — full audit trail from intent
   to artifact.
9. **Backward compatibility is mandatory** during every phase.
10. **No hardcoded models, providers, or workflows** — everything is
    configurable through Git.

---

## 2. Current State (Baseline)

### 2.1 Repository layout (as of plan v1.0.0)

```
wiki-script/
├── wiki_cli/
│   ├── client.py            # WikiJSClient (gql[requests] transport)
│   ├── exceptions.py        # WikiJSError
│   ├── models.py            # Pydantic v2 models (Page, PageVersion, ...)
│   ├── utils.py             # Shared helpers
│   ├── __init__.py          # Public re-exports
│   ├── __main__.py          # `python -m wiki_cli` entry point
│   ├── cli_main.py          # Interactive menu
│   ├── cli_pages.py         # Page CLI commands
│   ├── cli_history.py       # History CLI commands
│   ├── cli_system.py        # System commands (test connection, ...)
│   ├── pages/
│   │   ├── manager.py       # PagesManager (business logic)
│   │   ├── queries.py       # GraphQL queries/mutations
│   │   └── history.py       # History queries/mutations
│   └── ai/
│       ├── __init__.py
│       ├── agent.py         # Single AI assistant loop
│       ├── cli.py           # AI CLI commands
│       ├── config.py        # AIConfig + credential store
│       └── tools.py         # Tool dispatch
├── tests/                   # Pytest suite (mirrors wiki_cli structure)
├── docs/                    # User docs (01-introduction, 02-getting-started, ...)
├── README.md
├── AI_INTEGRATION.md
├── TEST_PLAN.md
├── pyproject.toml
├── requirements.txt
└── .env / .env.example
```

### 2.2 Current capabilities (must not regress)

| # | Capability | Module | Notes |
|---|---|---|---|
| 1 | Wiki.js GraphQL transport | `wiki_cli/client.py` | `gql[requests]`, API key auth |
| 2 | Page CRUD | `wiki_cli/pages/manager.py` | create / get / update / delete |
| 3 | Page search & tree browse | `wiki_cli/pages/manager.py` | list, search, tree |
| 4 | Page move / clone | `wiki_cli/pages/manager.py` | rename, clone |
| 5 | Page import / export | `wiki_cli/pages/manager.py` | file round-trip |
| 6 | History & diff & restore | `wiki_cli/pages/history.py` | versions, diff, restore |
| 7 | AI assistant | `wiki_cli/ai/agent.py` | OpenAI-compatible client |
| 8 | AI credential store | `wiki_cli/ai/config.py` | multi-provider keys on disk |
| 9 | Interactive CLI | `wiki_cli/cli_*.py` | menu-driven |
| 10 | User docs | `docs/0X-...` | MkDocs-friendly structure |
| 11 | Test suite | `tests/` | pytest, mock-based |

### 2.3 Maturity model

| Level | Name | Description | Status |
|---|---|---|---|
| 1 | Wiki.js CLI | CRUD + history | **Current** |
| 2 | Wiki.js CLI + AI | Adds single-agent assistance | **Current** |
| 3 | Intelligence Workbench | Multi-agent workflows + state | Target M1 |
| 4 | Governed Platform | Versioned policies, evaluations, approvals | Target M3 |
| 5 | Intelligence Platform | Full integration (Jira/Jenkins/PostgreSQL/Git) | Target M5 |

---

## 3. Target State (Vision)

### 3.1 Target architecture pillars

| Pillar | Responsibility | Backing store / system |
|---|---|---|
| Knowledge | Authoritative content | Wiki.js |
| Versioning | Prompts, policies, agent defs, model profiles | Git + GitHub |
| Validation | Tests, evals, policy checks, deploys | Jenkins |
| Runtime state | Workflow / agent / approval / cost records | PostgreSQL |
| Work intake | Requirements, tickets, traceability | Jira |
| Agents | Specialized AI roles | `wiki_platform/agents/` |
| Models | Multi-provider routing, fallback, cost caps | `wiki_platform/models/` |
| Workflows | State machine, approvals, lifecycle | `wiki_platform/workflows/` |
| Evaluations | Quality + cost + regression gates | `wiki_platform/evals/` |
| Governance | Versioned policies, sign-off rules | `policies/` (Git) |
| Human review | Approvals, comments, sign-off | CLI + Wiki + DB |
| Observability | Audit logs, traces, metrics | PostgreSQL + Wiki |

### 3.2 Target repository layout (final, Level 5)

```
wiki-script/
├── wiki_cli/                       # PRESERVED — Level 1/2 surface (back-compat)
│   └── ...                         # All existing modules + thin re-exports
├── wiki_platform/                  # NEW — Level 3+ core (public package)
│   ├── __init__.py
│   ├── config/                     # Settings, DI, feature flags
│   ├── core/                       # Domain primitives (no I/O)
│   ├── integrations/               # Wiki.js, Git, GitHub, Jira, Jenkins
│   │   ├── wiki/                   # Wiki.js client (moved from wiki_cli/client.py)
│   │   ├── git/                    # Git provider abstraction
│   │   ├── github/                 # GitHub API wrapper
│   │   ├── jira/                   # Jira API wrapper
│   │   └── jenkins/                # Jenkins API wrapper
│   ├── agents/                     # Agent framework (Phase 3)
│   │   ├── base.py
│   │   ├── registry.py
│   │   ├── roles/                  # Author, Critic, Judge, ...
│   │   ├── prompts/                # Versioned prompts (mirror Git)
│   │   └── runtime.py
│   ├── models/                     # Model router (Phase 4)
│   │   ├── router.py
│   │   ├── profiles/
│   │   ├── providers/
│   │   ├── pricing.py
│   │   └── escalation.py
│   ├── workflows/                  # Workflow engine (Phase 5)
│   │   ├── engine.py
│   │   ├── state_machine.py
│   │   ├── approvals.py
│   │   ├── definitions/            # Versioned workflow YAML
│   │   └── examples/
│   ├── db/                         # PostgreSQL state layer (Phase 6)
│   │   ├── orm.py
│   │   ├── repositories/
│   │   ├── migrations/             # alembic
│   │   └── session.py
│   ├── evals/                      # Evaluations (Phase 7)
│   │   ├── runner.py
│   │   ├── scorers/
│   │   └── regression/             # Auto-grown regression corpus
│   ├── cli/                        # New top-level CLI (Typer-based)
│   │   ├── main.py
│   │   ├── commands/
│   │   └── repl.py
│   └── observability/              # Audit + traces
├── policies/                       # Versioned policies (Git-tracked)
│   ├── agents/
│   ├── workflows/
│   ├── models/
│   └── governance/
├── prompts/                        # Versioned prompts (Git-tracked)
│   ├── author/
│   ├── critic/
│   ├── judge/
│   └── ...
├── workflows/                      # Versioned workflow YAML (Git-tracked)
├── evals/                          # Versioned eval suites (Git-tracked)
├── db/                             # SQL migrations + seed
├── reports/                        # Quality, coverage, risk, architecture reports
├── docs/
│   ├── 01-introduction/ ...        # User docs (preserved)
│   ├── discovery/                  # Phase 0
│   ├── architecture/               # Phase 1
│   ├── migration/                  # Phase 2
│   ├── agents/                     # Phase 3
│   ├── models/                     # Phase 4
│   ├── workflows/                  # Phase 5
│   ├── database/                   # Phase 6
│   ├── testing/                    # Phase 7
│   └── roadmap/                    # Phase 8
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── workflow/
│   ├── agent/
│   ├── regression/
│   ├── security/
│   ├── eval/
│   └── e2e/
├── scripts/                        # Dev, CI, Jenkins helpers
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── README.md
├── plan.md                         # THIS FILE
└── CHANGELOG.md
```

### 3.3 Backward compatibility contract

- `wiki_cli` package continues to import and run unchanged for Level 1/2 users.
- All existing CLI commands keep working.
- New functionality is exposed under `wiki_platform` and a new top-level CLI
  (`wiki-platform`).
- Deprecations are announced one milestone in advance with a `DeprecationWarning`
  and a `CHANGELOG.md` entry.

---

## 4. Phase Plan (Authoritative)

The master prompt defines 11 phases. Phases 0–8 are documentation-only. Phase 9
(implementation) and Phase 10 (quality gates) are gated on prior approval.

| # | Phase | Output directory | Code changes | Tests added | Gate |
|---|---|---|---|---|---|
| 0 | Discovery | `docs/discovery/` | No | No | Review |
| 1 | Target Architecture | `docs/architecture/` | No | No | Review |
| 2 | Repository Restructure | `docs/migration/` | No | No | Review |
| 3 | Agent Framework Design | `docs/agents/` | No | No | Review |
| 4 | Model Routing Design | `docs/models/` | No | No | Review |
| 5 | Workflow System Design | `docs/workflows/` | No | No | Review |
| 6 | Database Design | `docs/database/` | No | No | Review |
| 7 | Testing Strategy | `docs/testing/` | No | No | Review |
| 8 | Implementation Roadmap | `docs/roadmap/` | No | No | Review |
| 9 | Implementation | (code) | Yes | Yes | Quality gate per milestone |
| 10 | Quality Gates | `reports/` | Reports | Tests | Per merge |

### Phase 0 — Discovery

**Goal:** produce an objective, evidence-based picture of the current codebase.

**Deliverables** (`docs/discovery/`):
- `current_architecture.md` — modules, layers, call graph
- `dependency_map.md` — runtime + dev dependencies and their roles
- `module_analysis.md` — per-module responsibilities, public API, side effects
- `technical_debt.md` — coupling, duplication, missing abstractions
- `migration_risks.md` — risk register with likelihood/impact
- `recommendations.md` — prioritized recommendations

**Exit criteria:**
- Every file in the repo has been opened and assessed.
- Risks are ranked.
- Recommendations trace to specific files/lines.

### Phase 1 — Target Architecture

**Goal:** design the future system before writing code.

**Deliverables** (`docs/architecture/`):
- `architecture_overview.md`
- `system_context.md` (C4 Level 1)
- `runtime_design.md` (C4 Level 3)
- `workflow_engine.md`
- `state_management.md`
- `model_routing.md`
- `agent_system.md`
- `integrations.md`
- `testing_strategy.md`
- `release_strategy.md`

**Artifacts:**
- Component diagram (Mermaid)
- Sequence diagrams for: page review, employee review, weekly improvement cycle
- State diagram for workflow engine
- Database ERD (preview; finalized in Phase 6)

**Exit criteria:** architecture review meeting notes recorded in
`docs/architecture/review_notes.md`.

### Phase 2 — Repository Restructure Plan

**Deliverables** (`docs/migration/`):
- `repository_structure.md` (target tree — see §3.2)
- `migration_steps.md` (ordered, reversible steps)
- `compatibility_plan.md` (re-exports, shims, warnings)
- `rollback_plan.md` (how to revert each step)
- `release_plan.md` (versioning, SemVer, deprecation calendar)

**Exit criteria:** every move is justified, reversible, and tested.

### Phase 3 — Agent Framework Design

**Deliverables** (`docs/agents/`):
- `overview.md`
- `agent_lifecycle.md` (draft → review → approve → publish → retire)
- `versioning.md` (Git-backed prompt + role versions)
- `boundaries.md` (what an agent may/may not do)
- `permissions.md` (per-role scopes)
- `evaluation.md` (quality + cost + safety)
- `governance.md` (who can change an agent definition)

**Roles to design (8):**
Author, Critic, Judge, Synthesizer, Verifier, Researcher, Test Generator,
Evidence Collector. For each: responsibilities, permissions, prohibitions,
inputs, outputs, evaluation criteria.

### Phase 4 — Model Routing Design

**Deliverables** (`docs/models/`):
- `profiles.md` (versioned model profiles in `wiki_platform/models/profiles/*.yaml`)
- `routing.md` (router algorithm, fallback chains)
- `pricing.md` (cost tables, budgets, alerts)
- `benchmarking.md` (latency, quality, cost-per-task)
- `escalation.md` (when to escalate to a larger model / human)

**Constraints:**
- OpenRouter supported.
- Multi-provider.
- No hardcoded model names — all from Git-versioned profiles.

### Phase 5 — Workflow System Design

**Deliverables** (`docs/workflows/`):
- `overview.md`
- `lifecycle.md`
- `states.md` (full state set)
- `transitions.md` (allowed transitions, guards)
- `approvals.md` (human review, multi-signer, quorum)
- `examples.md` (doc review, req review, arch review, employee review, weekly)

**Workloads to support:**
- Document review
- Requirements review
- Architecture review
- Employee work analysis
- Weekly improvement cycle
- Knowledge publication

### Phase 6 — Database Design

**Deliverables** (`docs/database/`):
- `schema.md`
- `entities.md` (work_packages, workflow_runs, agent_runs, findings,
  approvals, human_reviews, costs, audit_logs, policies, prompts, evals)
- `migrations.md` (alembic workflow)
- `indexing.md`
- `retention.md`

### Phase 7 — Testing Strategy

**Deliverables** (`docs/testing/`):
- `unit_tests.md`
- `integration_tests.md`
- `workflow_tests.md`
- `agent_tests.md`
- `regression_tests.md`
- `security_tests.md`
- `evaluation_tests.md`
- `e2e_tests.md`

**Rule:** every feature ships with tests; every AI failure becomes a
regression test.

### Phase 8 — Implementation Roadmap

**Deliverables** (`docs/roadmap/`):
- `milestone_1.md` — Multi-agent core + workflow engine (no DB yet)
- `milestone_2.md` — Model router + cost controls
- `milestone_3.md` — PostgreSQL state + approvals
- `milestone_4.md` — Integrations (Git, GitHub, Jira, Jenkins)
- `milestone_5.md` — Evaluations, policies, observability
- `timeline.md` — sequencing, dependencies, staffing

Each milestone document specifies: goals, deliverables, risks, dependencies,
test requirements, acceptance criteria.

### Phase 9 — Implementation (GATED)

Rules:
- Incremental, one milestone at a time.
- After every milestone: run tests, update docs, generate changelog,
  generate migration notes, refresh architecture.
- Never make large uncontrolled changes.
- Backward compatibility must hold at every commit on `main`.

### Phase 10 — Quality Gates (PER MERGE)

Required reports under `reports/`:
- `quality_report.md`
- `coverage_report.md`
- `architecture_compliance.md`
- `risk_report.md`

Gates:
- tests pass
- lint passes
- type checks pass
- docs updated
- architecture updated
- changelog updated

---

## 5. Cross-Cutting Standards

### 5.1 Code standards

- **Python 3.10+**, fully typed (`mypy --strict` target on `wiki_platform/`).
- **Pydantic v2** for all data models.
- **Dependency injection** at module boundaries (no global state for I/O).
- **Modular architecture** — no circular imports.
- **No hardcoded model names, providers, or prompts** in code.

### 5.2 Documentation standards

- Every public function has a docstring (Google style).
- Every module has a top-level `__doc__`.
- Architecture decisions recorded in `docs/architecture/adr/NNNN-title.md`.
- Every milestone produces: changelog entry, migration notes, architecture
  update, test report.

### 5.3 Testing standards

- `pytest` for unit, integration, workflow, agent, regression, e2e.
- Mock I/O at the integration boundary, not deep inside the code.
- Every AI failure → regression test under `tests/regression/`.
- Coverage target: ≥ 85% on `wiki_platform/`, ≥ 70% overall.

### 5.4 Security standards

- Credentials in `~/.config/wiki-cli/` with `0600` (existing pattern preserved).
- Secret material never logged.
- All external HTTP calls go through a single audited client.
- Prompt-injection guardrails evaluated in `evals/`.

### 5.5 Release standards

- Semantic Versioning: `MAJOR.MINOR.PATCH`.
- `MAJOR` bumps on breaking API changes.
- Deprecations announced one MINOR release in advance.
- CHANGELOG.md updated on every merge to `main`.

---

## 6. Risks (Top 10 — to be expanded in Phase 0)

| # | Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|---|
| R1 | Breaking Wiki.js CLI surface during refactor | Med | High | Compatibility shims, regression tests, phased moves |
| R2 | AI provider drift / pricing changes | High | Med | Versioned profiles, OpenRouter abstraction, cost alerts |
| R3 | Prompt-injection via Wiki content | Med | High | Author/Critic separation, content sanitization, evals |
| R4 | PostgreSQL schema migration failures | Med | High | Backward-compatible migrations, blue/green, rollback scripts |
| R5 | Workflow state machine deadlocks | Med | Med | Reachability tests, timeouts, watchdog jobs |
| R6 | Jenkins flakiness blocking merges | High | Med | Retry, quarantine, separate fast vs slow suites |
| R7 | Cost overruns from LLM use | Med | Med | Per-workflow budgets, hard caps, escalation to human |
| R8 | GitHub rate limits during sync | Med | Med | ETag caching, conditional requests, queue + retry |
| R9 | Data loss in Wiki.js from buggy agent writes | Low | High | Dry-run mode, approval gates, Wiki.js backups |
| R10 | Model version drift breaking agents | High | Med | Pinned model profiles, snapshot evals on upgrade |

---

## 7. Decision Log (initial)

| # | Decision | Rationale | Date |
|---|---|---|---|
| D1 | Preserve `wiki_cli` package as the Level 1/2 surface | Backward compatibility mandate | 2026-07-13 |
| D2 | New core package is `wiki_platform` | Clean separation, allows independent versioning | 2026-07-13 |
| D3 | All prompts, policies, agent defs, model profiles live in Git | "Git defines intelligence" | 2026-07-13 |
| D4 | PostgreSQL for runtime state, Wiki.js for knowledge | Stated in core principles | 2026-07-13 |
| D5 | Alembic for migrations | De facto Python standard, reversible | 2026-07-13 |
| D6 | OpenRouter as primary multi-model aggregator | Single API, broad coverage | 2026-07-13 |
| D7 | Typer for new top-level CLI | Type-safe, modern, plays well with Pydantic | 2026-07-13 |

(Future decisions are appended here and mirrored to `docs/architecture/adr/`.)

---

## 8. How to use this plan

1. **Read this file first** before any work.
2. Identify the current phase from §4.
3. Open the phase's deliverable directory under `docs/`.
4. Follow the phase's exit criteria before moving to the next phase.
5. After every code change, update:
   - the relevant `docs/<phase>/` document,
   - `CHANGELOG.md`,
   - `reports/` (once they exist),
   - the ADR that records the decision.

---

## 9. PHASE STATUS (live)

> Updated at the end of each phase. Latest status appears at the top of the
> section that follows when implementation begins.

### Phase 0 — Discovery
- **Status:** ✅ Completed
- **Artifacts:**
  - `docs/discovery/current_architecture.md` — Full architecture analysis (layers, call graph, module inventory)
  - `docs/discovery/dependency_map.md` — Runtime, dev, internal, and external dependency analysis
  - `docs/discovery/module_analysis.md` — Per-module deep dive (19 source files, 17 test files)
  - `docs/discovery/technical_debt.md` — 34 debt items (3 critical, 8 high, 16 medium, 7 low)
  - `docs/discovery/migration_risks.md` — 15 risks with likelihood/impact scoring and mitigation plans
  - `docs/discovery/recommendations.md` — 20 prioritized recommendations (P0–P3) with implementation order
- **Code changes:** None (read-only phase)
- **Tests added:** None
- **Risks identified:** 15 risks, top 3:
  - R1/R12: Breaking backward compatibility during restructure (Score: 20)
  - R2/R7: AI provider drift and model version drift (Score: 16)
  - R3: Prompt injection via Wiki content (Score: 15)
- **Key findings:**
  - 34 technical debt items identified across 5 categories
  - Zero test coverage for core modules (client, models, exceptions, utils, manager)
  - Zero test coverage for entire AI package
  - 3 critical debt items: no DI, no core tests, no AI tests
- **Recommendation:** Proceed to Phase 1 — Target Architecture. Before Phase 9, address P0 recommendations (REC-01 through REC-04) to establish baseline stability.

### Phase 1 — Target Architecture
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 2 — Repository Restructure Plan
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 3 — Agent Framework Design
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 4 — Model Routing Design
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 5 — Workflow System Design
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 6 — Database Design
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 7 — Testing Strategy
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 8 — Implementation Roadmap
- **Status:** Not started
- **Artifacts:** —
- **Code changes:** None
- **Tests added:** None
- **Risks:** —
- **Recommendation:** —

### Phase 9 — Implementation
- **Status:** Gated on Phases 0–8 approval
- **Artifacts:** —
- **Code changes:** —
- **Tests added:** —
- **Risks:** —
- **Recommendation:** —

### Phase 10 — Quality Gates
- **Status:** Will activate on first merge
- **Artifacts:** —
- **Code changes:** —
- **Tests added:** —
- **Risks:** —
- **Recommendation:** —

---

## 10. Approval

This plan is **proposed** and becomes **active** once the owner signs off below.

| Role | Name | Date | Signature |
|---|---|---|---|
| Lead Architect | — | — | — |
| Product Manager | — | — | — |
| QA Lead | — | — | — |
| DevOps Lead | — | — | — |
| AI Systems Architect | — | — | — |
