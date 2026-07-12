# ADR-005: Custom Agent Framework

**ADR:** 005
**Title:** Custom Agent Framework
**Date:** 2026-07-13
**Status:** Accepted

---

## Context

The platform needs an agent framework to orchestrate LLM interactions with tool calling, permission management, and evaluation. Options include LangChain, LlamaIndex, CrewAI, or a custom framework.

## Decision

Build a custom agent framework with:
- `BaseAgent` abstract class for all agents
- Tool registry with permission-based access
- Runtime for agent lifecycle management
- Git-versioned prompt management
- Built-in evaluation and regression capture

## Consequences

### Positive
- Full control over agent behavior and permissions
- No external framework lock-in
- Lightweight — no unnecessary abstractions
- Easy to integrate with workflow engine
- Built-in evaluation from day one

### Negative
- Must build tool-calling, conversation management, and evaluation from scratch
- No community ecosystem of pre-built agents
- Must maintain compatibility with OpenAI tool-calling format

### Risks
- May need to add features that external frameworks already provide
- OpenAI tool-calling format may change

## Alternatives Considered

1. **LangChain** — rejected because it's too opinionated, has frequent breaking changes, and adds unnecessary complexity.
2. **LlamaIndex** — rejected because it's designed for RAG, not agent orchestration.
3. **CrewAI** — rejected because it's too rigid in its multi-agent paradigm.
