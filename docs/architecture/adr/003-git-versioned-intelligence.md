# ADR-003: Git as Source of Intelligence

**ADR:** 003
**Title:** Git as Source of Intelligence
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The platform uses AI agents, prompts, policies, model profiles, and workflow definitions. These must be versioned, auditable, and rollback-capable. Options include database storage, file storage, or Git.

## Decision

Store all intelligence artifacts (prompts, policies, agent definitions, model profiles, workflow definitions) in Git repositories. The `prompts/`, `policies/`, `models/profiles/`, and `workflows/` directories are Git-tracked and versioned.

## Consequences

### Positive
- Full version history with `git log`
- Easy rollback with `git revert`
- Pull request workflow for changes
- Branch-based A/B testing of prompts
- Audit trail via Git commits
- No database schema changes for intelligence updates

### Negative
- Git operations add latency to configuration reads
- Must handle Git conflicts for concurrent edits
- Large files in Git can bloat the repository

### Risks
- Git corruption could affect all intelligence artifacts
- Must ensure Git is available for platform operation

## Alternatives Considered

1. **PostgreSQL for prompts** — rejected because it doesn't provide version history or pull request workflow.
2. **S3/object storage** — rejected because it lacks versioning and audit trail.
3. **Wiki.js for prompts** — rejected because Wiki.js is for knowledge, not configuration.
