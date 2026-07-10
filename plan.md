# Wiki-Script Implementation Plan

## Context

This document is the single source of truth for the wiki-script project. Any AI agent
working on this project MUST read this file first.

---

## 1. Project Overview

**Goal:** Build a full-featured terminal-based Wiki.js manager. Users should be able to
manage pages and revisions entirely from the CLI.

**Tech stack:**
- Python 3.10+
- `gql[requests]` for GraphQL
- `pydantic` v2 for data models
- `python-dotenv` for env config

**Wiki.js version:** 2.x (GraphQL API at `/graphql`)

---

## 2. Project Structure

```
wiki-script/
├── wiki_cli/                      # Core library (importable)
│   ├── __init__.py                # Public API
│   ├── client.py                  # WikiJSClient (gql transport)
│   ├── exceptions.py              # WikiJSError
│   ├── models.py                  # Page, PageResponse, PageHistory, PageVersion
│   └── pages/
│       ├── __init__.py            # Re-exports PagesManager
│       ├── manager.py             # PagesManager class
│       ├── queries.py             # GraphQL CRUD queries/mutations
│       └── history.py             # GraphQL history queries/mutations
├── cli.py                         # Interactive terminal menu
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── test_exceptions.py
│   ├── test_models.py
│   ├── test_client.py
│   └── test_pages/
│       └── test_manager.py
├── pyproject.toml
├── requirements.txt
├── requirements-dev.txt
├── .env
├── .env.example
├── README.md
└── plan.md
```

---

## 3. Architecture

### Layered Design

```
cli.py  ──────────>  wiki_cli/pages/manager.py  ──>  wiki_cli/client.py
   (UI)                   (Business logic)              (Transport)
                              │
                              v
                       wiki_cli/models.py  (Data)
                       wiki_cli/exceptions.py  (Errors)
```

### Import Pattern

```python
from wiki_cli import WikiJSClient, WikiJSError, Page, PagesManager
```

---

## 4. Current Features

| # | Feature | Status |
|---|---------|--------|
| 1 | Create Page | Working |
| 2 | Fetch Page (by ID or path) | Working |
| 3 | Update Page | Working |
| 4 | Delete Page | Working |
| 5 | List Pages | Working |
| 6 | Search Pages | Working |
| 7 | Browse Pages (tree) | Working |
| 8 | Move/Rename Page | Working |
| 9 | Clone Page | Working |
| 10 | Export Page to File | Working |
| 11 | Import Page from File | Working |
| 12 | View Page History | Working |
| 13 | View Specific Revision | Working |
| 14 | Diff Two Revisions | Working |
| 15 | Restore Revision | Working |
| 16 | Test Connection | Working |

---

## 5. Testing

### Running Tests

```bash
# TBD
```

### Test Structure

- `tests/conftest.py` — Shared fixtures (mock client, sample data)
- `tests/test_exceptions.py` — WikiJSError behavior
- `tests/test_models.py` — Pydantic model validation
- `tests/test_client.py` — WikiJSClient (mocked transport)
- `tests/test_pages/test_manager.py` — PagesManager (mocked client)

### Writing New Tests

- Mock `WikiJSClient` using `unittest.mock.MagicMock(spec=WikiJSClient)`
- Use fixtures from `conftest.py` (`mock_client`, `sample_page`, `sample_pages`)
- Test both success and failure paths
- Test edge cases (empty results, missing fields, invalid input)

---

## 6. GraphQL API Reference

### Queries

```graphql
query { pages { list(orderBy: TITLE|PATH|CREATED|UPDATED) { id path title description isPublished isPrivate locale tags } } }
query { pages { single(id: $id) { id path title description content editor isPublished isPrivate locale tags { tag } } } }
query { pages { singleByPath(path: $path, locale: $locale) { ... } } }
query { pages { search(query: $query, locale: $locale) { results { id path title description locale } totalHits } } }
query { pages { history(id: $id, offsetPage: $o, offsetSize: $s) { trail { versionId versionDate authorName actionType } total } } }
query { pages { version(pageId: $p, versionId: $v) { versionId content title authorName ... } } }
```

### Mutations

```graphql
mutation { pages { create(...) { responseResult { succeeded message } page { id } } } }
mutation { pages { update(id: $id, ...) { responseResult { succeeded message } page { id } } } }
mutation { pages { delete(id: $id) { responseResult { succeeded } } } }
mutation { pages { restore(pageId: $p, versionId: $v) { responseResult { succeeded } } } }
```

### Tag Format Notes
- `pages.list` and `pages.search` return `tags` as `[String]`
- `pages.single` and `pages.singleByPath` return `tags` as `[{ tag: "..." }]`

---

## 7. Environment Variables

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

---

## 8. Dependencies

```
# Runtime
gql[requests]>=4.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
```
