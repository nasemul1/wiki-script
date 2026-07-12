# ADR-001: Preserve wiki_cli Package as Backward Compatibility Shim

**ADR:** 001
**Title:** Preserve wiki_cli Package as Backward Compatibility Shim
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The existing `wiki_cli` package is used by current users and must continue working during the transformation to `wiki_platform`. The master plan mandates backward compatibility during every phase.

## Decision

Keep the `wiki_cli` package as a thin re-export layer that imports from `wiki_platform`. All existing import paths (`from wiki_cli import WikiJSClient, Page, PagesManager`) continue to work. Deprecation warnings are added to guide users to the new `wiki_platform` imports.

## Consequences

### Positive
- Existing users can upgrade without breaking their code
- Migration is gradual, not a big-bang rewrite
- Tests for existing functionality continue to pass
- Trust is maintained during transition

### Negative
- Two packages must be maintained temporarily
- Import overhead from re-exports
- Confusion for new users about which package to use

### Risks
- Re-export layer may drift from actual implementation if not tested

## Alternatives Considered

1. **Delete wiki_cli and rename to wiki_platform** — rejected because it breaks all existing users immediately.
2. **Fork wiki_cli into wiki_platform, freeze wiki_cli** — rejected because bug fixes would need to be applied to both.
