# ADR-004: PostgreSQL for Runtime State

**ADR:** 004
**Title:** PostgreSQL for Runtime State
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The platform needs to store runtime state: workflow runs, agent runs, findings, approvals, costs, and audit logs. Options include PostgreSQL, SQLite, MongoDB, or file-based storage.

## Decision

Use PostgreSQL as the primary runtime state store. Use SQLAlchemy ORM with Alembic migrations. Use Redis for caching and locking.

## Consequences

### Positive
- ACID transactions for critical state changes
- JSONB support for flexible metadata storage
- Strong ecosystem (SQLAlchemy, Alembic)
- Proven at scale
- Full-text search capabilities
- Rich indexing options

### Negative
- Requires PostgreSQL server (additional infrastructure)
- More complex than SQLite for single-user mode
- Connection pooling must be managed

### Risks
- PostgreSQL unavailability blocks all operations
- Migration failures can corrupt state

## Alternatives Considered

1. **SQLite** — rejected because it lacks concurrent access and JSONB support.
2. **MongoDB** — rejected because it lacks ACID transactions and relational integrity.
3. **File-based storage** — rejected because it lacks concurrent access, transactions, and querying.
