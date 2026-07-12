# Runtime Design (C4 Level 3)

**Phase:** 1 — Target Architecture
**Date:** 2026-07-13
**Status:** Complete

---

## 1. Container Diagram

```mermaid
graph TB
    subgraph "wiki_platform Process"
        subgraph "CLI Layer"
            TyperApp["Typer App"]
            REPL["Interactive REPL"]
        end

        subgraph "Orchestration Layer"
            WfEngine["Workflow Engine"]
            AgentRuntime["Agent Runtime"]
            ModelRouter["Model Router"]
        end

        subgraph "Domain Layer"
            DomainCore["Domain Core\n(pure, no I/O)"]
            EvalEngine["Evaluation Engine"]
            PolicyEngine["Policy Engine"]
        end

        subgraph "Integration Layer"
            WikiAdapter["Wiki.js Adapter"]
            GitAdapter["Git/GitHub Adapter"]
            JiraAdapter["Jira Adapter"]
            JenkinsAdapter["Jenkins Adapter"]
            LLMAdapter["LLM Adapter"]
        end

        subgraph "Infrastructure Layer"
            DBRepo["DB Repository"]
            AuditLog["Audit Logger"]
            CacheLayer["Cache Layer"]
        end
    end

    subgraph "External"
        WikiJS[("Wiki.js")]
        GitHub[("GitHub")]
        Jira[("Jira")]
        Jenkins[("Jenkins")]
        PG[("PostgreSQL")]
        RD[("Redis")]
        LLM[("LLM APIs")]
    end

    TyperApp --> WfEngine
    REPL --> WfEngine
    WfEngine --> AgentRuntime
    WfEngine --> DBRepo
    WfEngine --> AuditLog
    AgentRuntime --> ModelRouter
    AgentRuntime --> WikiAdapter
    AgentRuntime --> GitAdapter
    AgentRuntime --> DBRepo
    AgentRuntime --> AuditLog
    ModelRouter --> LLMAdapter
    EvalEngine --> AgentRuntime
    PolicyEngine --> WfEngine
    PolicyEngine --> AgentRuntime
    WikiAdapter --> WikiJS
    GitAdapter --> GitHub
    JiraAdapter --> Jira
    JenkinsAdapter --> Jenkins
    LLMAdapter --> LLM
    DBRepo --> PG
    CacheLayer --> RD
```

---

## 2. Component Responsibilities

### 2.1 CLI Layer

| Component | Responsibility |
|---|---|
| `TyperApp` | Top-level CLI with subcommands (`workflow`, `agent`, `eval`, `config`, `wiki`) |
| `REPL` | Interactive session with auto-complete, history, slash commands |

### 2.2 Orchestration Layer

| Component | Responsibility |
|---|---|
| `WorkflowEngine` | Executes workflow definitions, manages state transitions, triggers approvals |
| `AgentRuntime` | Instantiates agents, manages lifecycle, dispatches tool calls, collects results |
| `ModelRouter` | Selects optimal model based on task type, cost budget, latency requirements |

### 2.3 Domain Layer

| Component | Responsibility |
|---|---|
| `DomainCore` | Value objects, entities, domain events, error hierarchy — zero I/O |
| `EvalEngine` | Runs evaluation suites, scores agent output, manages regression corpus |
| `PolicyEngine` | Evaluates policies against actions, enforces approval gates, blocks violations |

### 2.4 Integration Layer

| Component | Responsibility |
|---|---|
| `WikiAdapter` | GraphQL operations against Wiki.js, page CRUD, history, search |
| `GitAdapter` | Git operations (clone, pull, push, commit), GitHub API (PR, issues) |
| `JiraAdapter` | Jira ticket CRUD, requirement linking, status sync |
| `JenkinsAdapter` | Pipeline trigger, status polling, artifact retrieval |
| `LLMAdapter` | OpenAI-compatible API calls, streaming, tool-calling, response parsing |

### 2.5 Infrastructure Layer

| Component | Responsibility |
|---|---|
| `DBRepo` | SQLAlchemy ORM queries, repository pattern, connection pooling |
| `AuditLog` | Structured logging of every operation, trace correlation |
| `CacheLayer` | Redis read/write, TTL management, lock acquisition |

---

## 3. Request Flow — Page Review Workflow

```mermaid
sequenceDiagram
    actor User
    participant CLI as CLI (Typer)
    participant WE as Workflow Engine
    participant AR as Agent Runtime
    participant MR as Model Router
    participant LLM as LLM Provider
    participant Wiki as Wiki.js
    participant DB as PostgreSQL
    participant Audit as Audit Logger

    User->>CLI: wiki workflow run doc-review --page=docs/intro
    CLI->>WE: start_workflow("doc-review", page_id="docs/intro")
    WE->>DB: create work_package
    WE->>Audit: emit WorkflowStarted
    WE->>WE: transition(draft → in_progress)

    loop For each agent step
        WE->>AR: execute_step(current_agent, context)
        AR->>MR: select_model(task_type="review", budget=0.50)
        MR-->>AR: model_profile (gpt-4o, cost_cap=0.10/step)
        AR->>LLM: chat.completions.create(prompt, tools)
        LLM-->>AR: tool_call (fetch_page)
        AR->>Wiki: get_by_id(page_id)
        Wiki-->>AR: page content
        AR->>LLM: tool_result(page_content)
        LLM-->>AR: tool_call (analyze_content)
        AR->>LLM: tool_result(analysis)
        LLM-->>AR: final_response
        AR-->>WE: step_result(findings, score)
        WE->>DB: store findings
        WE->>Audit: emit AgentStepCompleted
    end

    WE->>WE: transition(in_progress → pending_review)
    WE->>User: Notification: approval required

    User->>CLI: wiki workflow approve <workflow_id>
    CLI->>WE: approve(workflow_id, user_id)
    WE->>WE: transition(pending_review → approved)
    WE->>DB: store approval
    WE->>Audit: emit WorkflowApproved

    WE->>Wiki: publish_reviewed_content(page_id, content)
    WE->>WE: transition(approved → completed)
    WE->>DB: update work_package status
    WE->>Audit: emit WorkflowCompleted
```

---

## 4. Request Flow — AI Agent Tool Execution

```mermaid
sequenceDiagram
    participant AR as Agent Runtime
    participant Tools as Tool Registry
    participant Policy as Policy Engine
    participant Wiki as Wiki.js Adapter
    participant DB as DB Repository
    participant Audit as Audit Logger

    AR->>Tools: get_tool("create_page")
    Tools-->>AR: tool_definition

    AR->>Policy: check_permission(agent_role, "wiki.create_page")
    Policy-->>AR: allowed (with constraints)

    AR->>AR: validate_arguments(tool_args, schema)
    AR->>Audit: emit ToolExecutionStarted

    alt Tool is wiki operation
        AR->>Wiki: create_page(validated_args)
        Wiki-->>AR: page_created
    else Tool is git operation
        AR->>Wiki: git_commit(validated_args)
        Wiki-->>AR: commit_hash
    else Tool is db operation
        AR->>DB: store_finding(validated_args)
        DB-->>AR: finding_id
    end

    AR->>DB: store tool_execution record
    AR->>Audit: emit ToolExecutionCompleted
    AR-->>AR: return result to LLM
```

---

## 5. Configuration Hierarchy

Configuration is loaded in order (later overrides earlier):

| Priority | Source | Example |
|---|---|---|
| 1 (lowest) | Defaults in code | `locale="en"`, `editor="markdown"` |
| 2 | Config file | `~/.config/wiki-platform/config.yaml` |
| 3 | Environment variables | `WIKI_PLATFORM_DB_URL=...` |
| 4 (highest) | CLI flags | `--db-url=...` |

### Config file structure

```yaml
# ~/.config/wiki-platform/config.yaml
wiki:
  url: "https://wiki.example.com/graphql"
  api_key: "${WIKIJS_API_KEY}"

database:
  url: "postgresql://user:pass@localhost:5432/wiki_platform"
  pool_size: 10

redis:
  url: "redis://localhost:6379/0"

agents:
  default_model_profile: "balanced"
  max_concurrent_steps: 5

models:
  profiles_dir: "models/profiles/"
  cost_alert_threshold: 10.0  # USD/day

workflows:
  definitions_dir: "workflows/"
  default_timeout: 3600  # seconds

evals:
  corpus_dir: "evals/regression/"
  min_score_threshold: 0.8

logging:
  level: "INFO"
  format: "json"
```

---

## 6. Concurrency Model

| Aspect | Design |
|---|---|
| **Workflow execution** | Single workflow runs sequentially through steps; multiple workflows run concurrently |
| **Agent steps** | Steps within a workflow execute sequentially (dependency order); independent steps may run in parallel |
| **LLM calls** | Async (`httpx` async client) with connection pooling |
| **Database access** | Synchronous SQLAlchemy with connection pool; async via `asyncpg` for high-throughput paths |
| **Redis operations** | Synchronous `redis-py` with connection pool |
| **File I/O** | Synchronous for Git operations; async for large file reads |
| **CLI** | Synchronous (Typer handles async internally) |

### Locking strategy

| Resource | Lock type | Implementation |
|---|---|---|
| Workflow instance | Distributed lock | Redis `SET NX` with TTL |
| Agent step | Optimistic lock | PostgreSQL version column |
| Model cost budget | Atomic counter | Redis `INCR` with TTL |
| Git repository | File lock | `fcntl.flock` on local Git repos |

---

## 7. Error Recovery

| Error type | Recovery strategy |
|---|---|
| LLM API timeout | Retry 3x with exponential backoff; fallback to next provider |
| LLM API error (4xx) | Log, skip step, continue workflow |
| Wiki.js unavailable | Queue operations, retry later; degrade to read-only |
| PostgreSQL unavailable | Fail fast, alert; no partial operations |
| Redis unavailable | Degrade to no-cache mode; no workflow locking |
| GitHub rate limit | Queue operations, retry after reset; use ETag cache |
| Agent tool failure | Log error, return error result to LLM, continue conversation |
| Workflow stuck | Watchdog detects after timeout, alerts admin, optionally cancels |
| Policy violation | Block action, log violation, require human override |

---

## 8. Resource Limits

| Resource | Limit | Configurable |
|---|---|---|
| Max concurrent workflows | 10 | Yes (`agents.max_concurrent_steps`) |
| Max agent steps per workflow | 50 | Yes (workflow definition) |
| Max tokens per LLM call | 128,000 | Yes (model profile) |
| Max tokens per conversation | 200,000 | Yes (agent config) |
| Max tool calls per step | 10 | Yes (agent config) |
| Workflow timeout | 3600s | Yes (workflow definition) |
| DB connection pool | 10 | Yes (`database.pool_size`) |
| Redis connection pool | 5 | Yes |
| Cost per workflow | $5.00 | Yes (model profile) |
| Cost per day | $50.00 | Yes (global config) |
