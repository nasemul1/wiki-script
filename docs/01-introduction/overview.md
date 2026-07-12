# Overview

**Lilac-wiki-cli** is a terminal-based Wiki.js management toolkit that lets you manage pages, revisions, and content entirely from the command line — or using natural language through an AI assistant.

## What It Does

Wiki.js exposes a powerful GraphQL API, but using it typically requires writing queries manually or using a web UI. wiki-script wraps that API into two interfaces:

1. **Interactive CLI menu** — numbered options for every operation (create, edit, delete, search, history, etc.)
2. **AI assistant** — chat in plain English and have the AI execute operations on your behalf

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌────────────┐
│  CLI Menu   │────▶│ PagesManager │────▶│  GraphQL   │────▶ Wiki.js
│  (wiki-cli) │     │              │     │  Client    │
└─────────────┘     └──────────────┘     └────────────┘
                          ▲
┌─────────────┐           │
│ AI Assistant│───────────┘
│  (wiki-ai)  │
└─────────────┘
```

- **CLI Menu** (`wiki-cli`) — interactive numbered menu, 17 options
- **AI Assistant** (`wiki-ai`) — natural language chat with tool-calling
- **PagesManager** — shared business logic layer used by both interfaces
- **GraphQL Client** — handles authentication, transport, and error handling

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Python 3.10+ | Uses `X | Y` union syntax, `match` statements |
| Pydantic models | Type-safe data structures with validation |
| `gql` for GraphQL | Mature, well-tested GraphQL client for Python |
| OpenAI-compatible API | All 6 AI providers use the same interface — single SDK |
| Lazy AI imports | `openai` dependency only loaded when AI mode is selected |
| Mock-based tests | All 67 tests run without a network connection |

## At a Glance

- **17 CLI operations** — CRUD, search, browse, move, clone, export, import, history, diff, restore
- **16 AI tools** — every CLI operation available via natural language
- **6 AI providers** — OpenAI, OpenRouter, Groq, Mistral, Ollama (local), Ollama Cloud
- **67 tests** — full coverage of all CLI handlers
- **Zero external UI dependencies** — pure ANSI terminal output
