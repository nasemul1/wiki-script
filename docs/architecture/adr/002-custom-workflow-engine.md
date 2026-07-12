# ADR-002: Custom Workflow Engine (In-Process)

**ADR:** 002
**Title:** Custom Workflow Engine (In-Process)
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The platform needs a workflow engine to orchestrate multi-step agent processes with state management, approvals, and error recovery. Options include external systems (Temporal, Prefect, Airflow) or a custom in-process engine.

## Decision

Build a custom workflow engine that runs in-process with the Python application. Workflows are defined in YAML, state is stored in PostgreSQL, and execution is managed by a lightweight engine core.

## Consequences

### Positive
- No external infrastructure dependency (Temporal/Prefect servers)
- Full control over workflow semantics and agent integration
- Simple deployment — just a Python process
- Easy to test with in-memory state
- Low operational overhead

### Negative
- Must build concurrency, persistence, and monitoring from scratch
- No built-in distributed execution (single-node only initially)
- Must implement our own retry, timeout, and compensation logic

### Risks
- Scaling limitations if workflow volume grows significantly
- May need to migrate to Temporal if distributed execution becomes necessary

## Alternatives Considered

1. **Temporal** — rejected because it requires separate server infrastructure and adds operational complexity.
2. **Prefect** — rejected because it's designed for data pipelines, not agent orchestration.
3. **Airflow** — rejected because it's too heavy for this use case.
4. **Simple script** — rejected because it lacks state management, approvals, and error recovery.
