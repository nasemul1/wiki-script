# Dependency Map

**Phase:** 0 — Discovery
**Date:** 2026-07-13
**Status:** Complete

---

## 1. External Dependencies (Runtime)

| Package | Version constraint | Used by | Purpose | Criticality |
|---|---|---|---|---|
| `gql[requests]` | `>=4.0.0` | `client.py` | GraphQL HTTP transport to Wiki.js | **Critical** — no Wiki.js access without it |
| `python-dotenv` | `>=1.0.0` | `client.py` | Load `.env` files into `os.environ` | **High** — env-based config loading |
| `pydantic` | `>=2.0.0` | `models.py` | Data model validation and serialization | **Medium** — used only for models |
| `openai` | `>=1.0.0` | `ai/agent.py`, `ai/config.py` | LLM API client (OpenAI-compatible) | **Critical** — AI assistant depends on it |
| `httpx` | (unlisted) | `ai/config.py` | HTTP client for model list fetching | **Medium** — only used for `fetch_models()` |

### Dependency graph (external)

```
gql[requests]  ──→  gql  ──→  requests  ──→  urllib3, certifi
python-dotenv  ──→  (stdlib only)
pydantic       ──→  (stdlib only)
openai         ──→  httpx  ──→  anyio, certifi, httpcore
httpx          ──→  anyio, certifi, httpcore, sniffio
```

---

## 2. External Dependencies (Dev)

| Package | Version constraint | Used by | Purpose |
|---|---|---|---|
| `pytest` | `>=7.0` | `tests/` | Test framework |
| `pytest-cov` | (unlisted in requirements.txt) | `tests/` | Coverage reporting |

### Dev dependency issues

| Issue | Details |
|---|---|
| `pytest-cov` not in `requirements.txt` | Only installable via `pip install -e ".[dev]"` |
| `httpx` missing from `requirements.txt` | Required by `ai/config.py` but not listed |
| No `requirements-dev.txt` | All dev deps embedded in `pyproject.toml` optional extras |

---

## 3. Internal Module Dependencies

### 3.1 Dependency matrix

| Module | Depends on (internal) |
|---|---|
| `wiki_cli/__init__.py` | `client`, `exceptions`, `models`, `pages`, `cli_main` |
| `wiki_cli/__main__.py` | `cli_main` |
| `wiki_cli/client.py` | `exceptions` |
| `wiki_cli/models.py` | (none) |
| `wiki_cli/exceptions.py` | (none) |
| `wiki_cli/utils.py` | `models` |
| `wiki_cli/cli_main.py` | `client`, `exceptions`, `pages`, `cli_pages`, `cli_history`, `cli_system`, `ai.cli` (lazy) |
| `wiki_cli/cli_pages.py` | `utils`, `models`, `pages` |
| `wiki_cli/cli_history.py` | `utils`, `pages` |
| `wiki_cli/cli_system.py` | `client`, `exceptions`, `pages` |
| `wiki_cli/pages/__init__.py` | `pages.manager` |
| `wiki_cli/pages/manager.py` | `client`, `exceptions`, `models`, `pages.queries`, `pages.history` |
| `wiki_cli/pages/queries.py` | (none) |
| `wiki_cli/pages/history.py` | (none) |
| `wiki_cli/ai/__init__.py` | `ai.agent`, `ai.config`, `ai.cli` |
| `wiki_cli/ai/agent.py` | `client`, `exceptions`, `models`, `pages`, `ai.config`, `ai.tools` |
| `wiki_cli/ai/cli.py` | `exceptions`, `ai.agent`, `ai.config` |
| `wiki_cli/ai/config.py` | (none) |
| `wiki_cli/ai/tools.py` | (none) |

### 3.2 Leaf modules (no internal dependencies)

- `wiki_cli/models.py`
- `wiki_cli/exceptions.py`
- `wiki_cli/pages/queries.py`
- `wiki_cli/pages/history.py`
- `wiki_cli/ai/config.py`
- `wiki_cli/ai/tools.py`

### 3.3 Hub modules (most dependents)

| Module | Depended on by | Count |
|---|---|---|
| `exceptions.py` | client, cli_main, cli_system, ai/agent, ai/cli | 5 |
| `models.py` | utils, cli_pages, pages/manager, ai/agent | 4 |
| `pages/manager.py` | cli_pages, cli_history, cli_main (via pages), ai/agent | 4 |
| `client.py` | pages/manager, cli_main, cli_system, ai/agent | 4 |

### 3.4 Circular dependency risk

No circular dependencies exist. The dependency graph is a DAG:

```
exceptions, models (leaf)
  ↓
client (depends on exceptions)
  ↓
pages/queries, pages/history (leaf, parallel to client)
  ↓
pages/manager (depends on client, exceptions, models, queries, history)
  ↓
utils (depends on models)
  ↓
cli_pages (depends on utils, models, pages)
cli_history (depends on utils, pages)
cli_system (depends on client, exceptions, pages)
  ↓
cli_main (depends on all cli_* modules, client, exceptions, pages)
  ↓
ai/tools, ai/config (leaf)
  ↓
ai/agent (depends on client, exceptions, models, pages, ai/config, ai/tools)
  ↓
ai/cli (depends on exceptions, ai/agent, ai/config)
```

---

## 4. Third-Party Service Dependencies

| Service | Protocol | Used by | Authentication |
|---|---|---|---|
| Wiki.js GraphQL API | HTTPS + GraphQL | `client.py` | Bearer token (API key) |
| OpenAI API | HTTPS + REST | `ai/agent.py` (via openai SDK) | API key |
| OpenRouter API | HTTPS + REST | `ai/config.py` (via openai SDK) | API key |
| Groq API | HTTPS + REST | `ai/config.py` (via openai SDK) | API key |
| Mistral API | HTTPS + REST | `ai/config.py` (via openai SDK) | API key |
| Ollama (local) | HTTP + REST | `ai/config.py` (via openai SDK) | None |
| Ollama (remote) | HTTP + REST | `ai/config.py` (via openai SDK) | None |

---

## 5. Filesystem Dependencies

| Path | Purpose | Created by |
|---|---|---|
| `.env` | Wiki.js credentials | User (manual) |
| `~/.config/wiki-cli/credentials.json` | AI provider API keys | `ai/config.py` |
| `~/.config/wiki-cli/last_config.json` | Last AI config | `ai/cli.py` |
| `export_page` output | Markdown file | `cli_pages.py` |
| `import_page` input | Markdown file | `cli_pages.py` |

---

## 6. Environment Variable Dependencies

| Variable | Required | Default | Used by |
|---|---|---|---|
| `WIKIJS_URL` | Yes | None | `client.py` (via `dotenv`) |
| `WIKIJS_API_KEY` | Yes | None | `client.py` (via `dotenv`) |
| `EDITOR` | No | Falls back to editor list | `ai/cli.py` |
| `VISUAL` | No | Falls back to editor list | `ai/cli.py` |

---

## 7. Dependency Issues Summary

| # | Issue | Severity | File |
|---|---|---|---|
| D1 | `httpx` used in `ai/config.py` but not in `requirements.txt` | High | `requirements.txt` |
| D2 | `openai` listed as hard dep in `requirements.txt` but optional in `pyproject.toml` | Medium | `requirements.txt` |
| D3 | `load_dotenv()` called at module import time in `client.py` | Medium | `client.py:14` |
| D4 | `getpass` imported but never used in `ai/config.py` | Low | `ai/config.py:15` |
| D5 | No version pins — all deps use `>=` without upper bounds | Medium | `pyproject.toml`, `requirements.txt` |
| D6 | No lock file (`requirements.lock` or similar) | Medium | Project root |
| D7 | `pytest-cov` not listed in `requirements.txt` | Low | `requirements.txt` |
