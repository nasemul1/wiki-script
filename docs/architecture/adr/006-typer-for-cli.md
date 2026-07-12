# ADR-006: Typer for New CLI

**ADR:** 006
**Title:** Typer for New CLI
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The platform needs a new CLI for Level 3+ features (workflows, agents, evaluations, configuration). The existing CLI is menu-driven and hard to extend. Options include Typer, Click, argparse, or Rich.

## Decision

Use Typer for the new top-level CLI (`wiki-platform`). Keep the existing menu-driven CLI in `wiki_cli` for backward compatibility.

## Consequences

### Positive
- Type-safe CLI arguments (Pydantic integration)
- Auto-generated help text and completion
- Modern, well-maintained library
- Rich output support (tables, colors)
- Easy to test with CliRunner

### Negative
- Another dependency to manage
- Different paradigm from existing menu-driven CLI
- Users must learn new command structure

### Risks
- Typer may have bugs or missing features for complex use cases

## Alternatives Considered

1. **Click** — rejected because Typer is built on Click with better type safety.
2. **argparse** — rejected because it's too low-level and verbose.
3. **Rich + custom** — rejected because it doesn't provide CLI structure.
