# AI Integration Guide for wiki-script

## Overview

This document describes how to integrate an AI assistant into the `wiki-script` CLI project. The AI agent receives natural language prompts from the user and executes Wiki.js operations (create, update, delete, search, etc.) automatically using the existing `PagesManager` API.

**Architecture:**

```
User Prompt → AI Agent (LLM with tool calling) → PagesManager methods → Wiki.js GraphQL API
```

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Architecture](#architecture)
3. [Project Structure](#project-structure)
4. [Configuration](#configuration)
5. [Tool Definitions](#tool-definitions)
6. [Agent Implementation](#agent-implementation)
7. [CLI Entry Point](#cli-entry-point)
8. [Usage Examples](#usage-examples)
9. [Dependencies](#dependencies)
10. [Testing](#testing)
11. [Security Considerations](#security-considerations)

---

## Prerequisites

- Python 3.10+
- An LLM API key from one of the supported providers (OpenRouter, Groq, Mistral, Ollama, or OpenAI)
- A running Wiki.js instance with API access (already configured in the base project)

---

## Architecture

### Why This Works

The existing project has a clean separation of concerns that makes AI integration straightforward:

| Layer | File | Purpose |
|-------|------|---------|
| Transport | `wiki_cli/client.py` | GraphQL client (gql + requests) |
| Business Logic | `wiki_cli/pages/manager.py` | `PagesManager` — all page operations |
| Data Models | `wiki_cli/models.py` | Pydantic models (`Page`, `PageResponse`, etc.) |

`PagesManager` already exposes all 16 Wiki.js operations as programmatic methods. An AI agent calls these methods directly — no interactive CLI input needed.

### Flow Diagram

```
User types prompt
       │
       ▼
┌─────────────────────────────┐
│       AI Agent (LLM)        │
│  - Receives user prompt      │
│  - Decides which tools to    │
│    call (function calling)   │
│  - Returns text response     │
└──────────┬──────────────────┘
           │ tool_calls
           ▼
┌─────────────────────────────┐
│     Tool Dispatcher         │
│  - Maps tool name to        │
│    PagesManager method      │
│  - Converts args to models  │
│  - Returns structured result│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│    PagesManager             │
│  - Executes GraphQL query   │
│  - Returns Page/PageResponse│
└──────────┬──────────────────┘
           │
           ▼
┌─────────────────────────────┐
│    Wiki.js GraphQL API      │
└─────────────────────────────┘
```

---

## Project Structure

Add the following files to the existing project:

```
wiki_cli/
├── __init__.py
├── client.py
├── models.py
├── pages/
│   ├── manager.py
│   ├── queries.py
│   └── history.py
├── cli_main.py
├── cli_pages.py
├── cli_history.py
├── cli_system.py
├── utils.py
├── exceptions.py
└── ai/                          # NEW
    ├── __init__.py
    ├── tools.py                 # Tool definitions (JSON schemas)
    ├── agent.py                 # AI agent loop + tool dispatcher
    ├── config.py                # AI provider configuration
    └── cli.py                   # Interactive AI chat interface
```

---

## Configuration

### How It Works

When you start the AI assistant (`wiki-ai` or option 17 from the menu), you go through 3 steps:

1. **Pick a provider** — OpenRouter, Groq, Mistral, OpenAI, Ollama
2. **Enter API key** — saved to `~/.config/wiki-cli/credentials.json`, reused next time
3. **Pick a model** — live list fetched from the provider, you choose one

API keys are stored locally in `~/.config/wiki-cli/credentials.json` (mode `0600`).
On subsequent runs you can reuse saved keys or enter new ones.

### Config Module

**`wiki_cli/ai/config.py`:**

```python
"""AI provider configuration and credential storage.

Supported providers:
  - openai       OpenAI API (gpt-4o, gpt-4o-mini, etc.)
  - openrouter   OpenRouter (access 100+ models via openrouter.ai)
  - groq         Groq (fast inference for llama, mixtral, gemma, etc.)
  - mistral      Mistral AI (mistral-tiny, mistral-small, etc.)
  - ollama       Ollama local (llama3, mistral, codellama, etc.)
  - ollama-cloud Ollama via remote server
"""

from __future__ import annotations

import json
import httpx
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Credential storage  (~/.config/wiki-cli/credentials.json)
# ---------------------------------------------------------------------------

_CRED_DIR = Path.home() / ".config" / "wiki-cli"
_CRED_FILE = _CRED_DIR / "credentials.json"


def _load_credentials() -> dict[str, str]:
    """Load saved API keys from disk."""
    if not _CRED_FILE.exists():
        return {}
    try:
        return json.loads(_CRED_FILE.read_text())
    except Exception:
        return {}


def _save_credentials(creds: dict[str, str]) -> None:
    """Persist API keys to disk."""
    _CRED_DIR.mkdir(parents=True, exist_ok=True)
    _CRED_FILE.write_text(json.dumps(creds, indent=2) + "\n")
    _CRED_FILE.chmod(0o600)


def get_saved_key(provider: str) -> str:
    """Return the saved API key for *provider*, or empty string."""
    return _load_credentials().get(provider, "")


def save_key(provider: str, api_key: str) -> None:
    """Save an API key for *provider*."""
    creds = _load_credentials()
    creds[provider] = api_key
    _save_credentials(creds)


def remove_key(provider: str) -> None:
    """Remove the saved API key for *provider*."""
    creds = _load_credentials()
    creds.pop(provider, None)
    _save_credentials(creds)


def list_saved_keys() -> dict[str, str]:
    """Return all saved API keys."""
    return _load_credentials()


# ---------------------------------------------------------------------------
# Provider defaults
# ---------------------------------------------------------------------------

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {"base_url": "https://api.openai.com/v1", "models_url": "https://api.openai.com/v1/models"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1", "models_url": "https://openrouter.ai/api/v1/models"},
    "groq": {"base_url": "https://api.groq.com/openai/v1", "models_url": "https://api.groq.com/openai/v1/models"},
    "mistral": {"base_url": "https://api.mistral.ai/v1", "models_url": "https://api.mistral.ai/v1/models"},
    "ollama": {"base_url": "http://localhost:11434/v1", "models_url": "http://localhost:11434/api/tags"},
    "ollama-cloud": {"base_url": "", "models_url": ""},
}


@dataclass
class AIConfig:
    """Configuration for the AI provider."""

    provider: str = ""
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    def get_client(self):
        """Initialize and return the OpenAI-compatible LLM client."""
        import openai
        kwargs: dict[str, str] = {}
        if self.provider == "ollama":
            kwargs["api_key"] = "ollama"
        else:
            kwargs["api_key"] = self.api_key
        if self.base_url:
            kwargs["base_url"] = self.base_url
        return openai.OpenAI(**kwargs)


def fetch_models(provider: str, api_key: str = "") -> list[str]:
    """Fetch available models from the provider's API."""
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    models_url = defaults.get("models_url", "")
    if not models_url:
        return []
    headers: dict[str, str] = {}
    if api_key and provider != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"
    try:
        resp = httpx.get(models_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []
    if provider == "ollama":
        return sorted(m.get("name", "") for m in data.get("models", []) if m.get("name"))
    return sorted(m.get("id", "") for m in data.get("data", []) if m.get("id"))
```

---

## Tool Definitions

Each tool maps 1:1 to a `PagesManager` method. The AI uses these schemas to understand what arguments to pass.

**`wiki_cli/ai/tools.py`:**

```python
"""Tool definitions for AI function calling.

Each tool corresponds to a PagesManager method. The JSON schemas
are passed to the LLM so it knows what operations are available
and what arguments they accept.
"""

from __future__ import annotations

TOOLS = [
    # ── CRUD ──────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "create_page",
            "description": "Create a new Wiki.js page with the given path, title, and content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Page path, e.g. 'docs/getting-started'",
                    },
                    "title": {"type": "string", "description": "Page title"},
                    "content": {
                        "type": "string",
                        "description": "Page content in Markdown",
                    },
                    "description": {
                        "type": "string",
                        "description": "Short page description",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags",
                    },
                    "isPublished": {
                        "type": "boolean",
                        "default": True,
                        "description": "Whether the page is published",
                    },
                    "isPrivate": {
                        "type": "boolean",
                        "default": False,
                        "description": "Whether the page is private",
                    },
                    "locale": {
                        "type": "string",
                        "default": "en",
                        "description": "Page locale",
                    },
                },
                "required": ["path", "title", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_page",
            "description": "Fetch a Wiki.js page by its ID or path. Returns full page details including content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "integer",
                        "description": "Page ID (use this OR path, not both)",
                    },
                    "path": {
                        "type": "string",
                        "description": "Page path (use this OR page_id, not both)",
                    },
                    "locale": {
                        "type": "string",
                        "default": "en",
                        "description": "Locale for path-based lookup",
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_page",
            "description": "Update an existing Wiki.js page. Only provided fields are changed; others stay the same.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "ID of the page to update"},
                    "title": {"type": "string", "description": "New title"},
                    "content": {"type": "string", "description": "New content (Markdown)"},
                    "description": {"type": "string", "description": "New description"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New tags list",
                    },
                    "isPublished": {"type": "boolean", "description": "Publish status"},
                    "isPrivate": {"type": "boolean", "description": "Privacy status"},
                },
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_page",
            "description": "Permanently delete a Wiki.js page by ID. This is irreversible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "integer",
                        "description": "ID of the page to delete",
                    }
                },
                "required": ["page_id"],
            },
        },
    },

    # ── Discovery ─────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "list_pages",
            "description": "List all pages in the wiki. Optionally sort by TITLE, PATH, CREATED, or UPDATED.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_by": {
                        "type": "string",
                        "enum": ["TITLE", "PATH", "CREATED", "UPDATED"],
                        "default": "TITLE",
                        "description": "Sort order",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_pages",
            "description": "Full-text search across all Wiki.js pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query string",
                    },
                    "locale": {
                        "type": "string",
                        "default": "en",
                        "description": "Locale filter",
                    },
                },
                "required": ["query"],
            },
        },
    },

    # ── Organization ──────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "move_page",
            "description": "Move or rename a page to a new path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "Page ID to move"},
                    "new_path": {
                        "type": "string",
                        "description": "New path for the page",
                    },
                },
                "required": ["page_id", "new_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clone_page",
            "description": "Clone an existing page to a new path with a new title.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_id": {
                        "type": "integer",
                        "description": "ID of the source page to clone",
                    },
                    "new_path": {
                        "type": "string",
                        "description": "Path for the cloned page",
                    },
                    "new_title": {
                        "type": "string",
                        "description": "Title for the cloned page",
                    },
                },
                "required": ["source_id", "new_path", "new_title"],
            },
        },
    },

    # ── Import / Export ───────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "export_page",
            "description": "Export a page as Markdown with YAML frontmatter to a local file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "Page ID to export"},
                    "filename": {
                        "type": "string",
                        "description": "Output filename (e.g. 'docs_page.md')",
                    },
                },
                "required": ["page_id", "filename"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "import_page",
            "description": "Import a page from a local Markdown file (with optional YAML frontmatter).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Path to the Markdown file",
                    },
                    "path": {
                        "type": "string",
                        "description": "Page path (overrides frontmatter)",
                    },
                    "title": {
                        "type": "string",
                        "description": "Page title (overrides frontmatter)",
                    },
                },
                "required": ["filename"],
            },
        },
    },

    # ── History ───────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "view_history",
            "description": "View revision history for a page. Returns list of versions with metadata.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "integer",
                        "description": "Page ID to get history for",
                    },
                    "offset_page": {
                        "type": "integer",
                        "default": 0,
                        "description": "Page number for pagination",
                    },
                    "offset_size": {
                        "type": "integer",
                        "default": 100,
                        "description": "Results per page",
                    },
                },
                "required": ["page_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "view_revision",
            "description": "View the content and metadata of a specific page revision.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "Page ID"},
                    "version_id": {
                        "type": "integer",
                        "description": "Version ID to view",
                    },
                },
                "required": ["page_id", "version_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "diff_revisions",
            "description": "Compare two revisions of a page side by side (unified diff).",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "Page ID"},
                    "version_id_1": {
                        "type": "integer",
                        "description": "Older version ID",
                    },
                    "version_id_2": {
                        "type": "integer",
                        "description": "Newer version ID",
                    },
                },
                "required": ["page_id", "version_id_1", "version_id_2"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "restore_revision",
            "description": "Restore a page to a specific previous version. This overwrites current content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_id": {"type": "integer", "description": "Page ID"},
                    "version_id": {
                        "type": "integer",
                        "description": "Version ID to restore to",
                    },
                },
                "required": ["page_id", "version_id"],
            },
        },
    },

    # ── System ────────────────────────────────────────────────────────
    {
        "type": "function",
        "function": {
            "name": "test_connection",
            "description": "Test connectivity to the Wiki.js API and return basic info.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
]
```

---

## Agent Implementation

**`wiki_cli/ai/agent.py`:**

```python
"""AI agent that translates natural language prompts into Wiki.js operations."""

from __future__ import annotations

import json
from typing import Any

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.models import Page
from wiki_cli.pages import PagesManager
from wiki_cli.ai.config import AIConfig
from wiki_cli.ai.tools import TOOLS

SYSTEM_PROMPT = """You are a Wiki.js assistant. You manage wiki pages using the tools provided.

Rules:
- Always confirm with the user before performing destructive actions (delete, restore, move).
- When creating or updating pages, generate high-quality Markdown content when the user provides a topic.
- If a tool returns an error, explain it to the user and suggest fixes.
- For searches or lists, summarize results in a readable format instead of dumping raw data.
- Never fabricate page IDs or paths. Always fetch first if unsure.
"""


class WikiAgent:
    """AI agent that uses LLM tool calling to execute Wiki.js operations.

    Attributes:
        pages: The PagesManager instance for executing operations.
        config: The AI provider configuration.
        client: The underlying LLM client (OpenAI or Anthropic).
    """

    def __init__(self, config: AIConfig | None = None) -> None:
        self.config = config or AIConfig()
        self.wiki_client = WikiJSClient()
        self.pages = PagesManager(self.wiki_client)
        self.client = self.config.get_client()
        self._pending_confirmations: dict[str, dict] = {}

    def run(self, user_prompt: str) -> str:
        """Process a user prompt and return the AI's response.

        This is the main entry point. It handles the full loop:
        1. Send prompt to LLM
        2. If LLM wants to call tools, execute them and send results back
        3. Repeat until LLM produces a text response

        Args:
            user_prompt: The user's natural language request.

        Returns:
            The AI's text response.
        """
        return self._run_openai(user_prompt)

    def _run_openai(self, user_prompt: str) -> str:
        """Tool-calling loop for OpenAI-compatible APIs.

        Works with all supported providers (openai, openrouter, groq, mistral,
        ollama, ollama-cloud) since they all use the same chat completions API.
        """
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
            )

            msg = response.choices[0].message

            if not msg.tool_calls:
                return msg.content or ""

            messages.append(msg)

            for tool_call in msg.tool_calls:
                result = self._execute_tool(
                    tool_call.function.name,
                    tool_call.function.arguments,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result, default=str),
                    }
                )

    def _execute_tool(self, name: str, arguments_json: str) -> dict[str, Any]:
        """Execute a tool call and return a structured result.

        Args:
            name: The tool/function name.
            arguments_json: JSON string of arguments from the LLM.

        Returns:
            A dict with 'success' and 'data' or 'error' keys.
        """
        try:
            args = json.loads(arguments_json)
        except json.JSONDecodeError as e:
            return {"success": False, "error": f"Invalid JSON arguments: {e}"}

        dispatch = {
            "create_page": self._tool_create_page,
            "fetch_page": self._tool_fetch_page,
            "update_page": self._tool_update_page,
            "delete_page": self._tool_delete_page,
            "list_pages": self._tool_list_pages,
            "search_pages": self._tool_search_pages,
            "move_page": self._tool_move_page,
            "clone_page": self._tool_clone_page,
            "export_page": self._tool_export_page,
            "import_page": self._tool_import_page,
            "view_history": self._tool_view_history,
            "view_revision": self._tool_view_revision,
            "diff_revisions": self._tool_diff_revisions,
            "restore_revision": self._tool_restore_revision,
            "test_connection": self._tool_test_connection,
        }

        handler = dispatch.get(name)
        if not handler:
            return {"success": False, "error": f"Unknown tool: {name}"}

        try:
            result = handler(args)
            if hasattr(result, "model_dump"):
                return {"success": True, "data": result.model_dump()}
            return {"success": True, "data": result}
        except WikiJSError as e:
            return {"success": False, "error": str(e)}
        except Exception as e:
            return {"success": False, "error": f"Unexpected error: {e}"}

    # ── Tool Handlers ─────────────────────────────────────────────────

    def _tool_create_page(self, args: dict) -> Any:
        page = Page(
            path=args["path"],
            title=args["title"],
            content=args["content"],
            description=args.get("description", ""),
            tags=args.get("tags", []),
            isPublished=args.get("isPublished", True),
            isPrivate=args.get("isPrivate", False),
            locale=args.get("locale", "en"),
        )
        return self.pages.create(page)

    def _tool_fetch_page(self, args: dict) -> Any:
        if "page_id" in args and args["page_id"] is not None:
            return self.pages.get_by_id(args["page_id"])
        elif "path" in args and args["path"] is not None:
            return self.pages.get_by_path(args["path"], args.get("locale", "en"))
        return {"error": "Provide either page_id or path"}

    def _tool_update_page(self, args: dict) -> Any:
        page_id = args["page_id"]
        existing = self.pages.get_by_id(page_id)

        if "title" in args and args["title"] is not None:
            existing.title = args["title"]
        if "content" in args and args["content"] is not None:
            existing.content = args["content"]
        if "description" in args and args["description"] is not None:
            existing.description = args["description"]
        if "tags" in args and args["tags"] is not None:
            existing.tags = args["tags"]
        if "isPublished" in args and args["isPublished"] is not None:
            existing.isPublished = args["isPublished"]
        if "isPrivate" in args and args["isPrivate"] is not None:
            existing.isPrivate = args["isPrivate"]

        return self.pages.update(existing)

    def _tool_delete_page(self, args: dict) -> Any:
        self.pages.delete(args["page_id"])
        return {"message": f"Page {args['page_id']} deleted successfully"}

    def _tool_list_pages(self, args: dict) -> Any:
        pages = self.pages.list_all(order_by=args.get("order_by", "TITLE"))
        return {
            "total": len(pages),
            "pages": [
                {
                    "id": p.id,
                    "path": p.path,
                    "title": p.title,
                    "isPublished": p.isPublished,
                    "tags": p.tags,
                }
                for p in pages
            ],
        }

    def _tool_search_pages(self, args: dict) -> Any:
        pages = self.pages.search(args["query"], args.get("locale", "en"))
        return {
            "total": len(pages),
            "results": [
                {"id": p.id, "path": p.path, "title": p.title, "description": p.description}
                for p in pages
            ],
        }

    def _tool_move_page(self, args: dict) -> Any:
        return self.pages.move_or_rename(args["page_id"], args["new_path"])

    def _tool_clone_page(self, args: dict) -> Any:
        return self.pages.clone_page(
            args["source_id"], args["new_path"], args["new_title"]
        )

    def _tool_export_page(self, args: dict) -> Any:
        page = self.pages.get_by_id(args["page_id"])
        filename = args["filename"]

        with open(filename, "w", encoding="utf-8") as f:
            f.write("---\n")
            f.write(f"title: {page.title}\n")
            f.write(f"path: {page.path}\n")
            f.write(f"description: {page.description}\n")
            f.write(f"tags: [{', '.join(page.tags)}]\n")
            f.write(f"published: {page.isPublished}\n")
            f.write(f"private: {page.isPrivate}\n")
            f.write(f"locale: {page.locale}\n")
            f.write("---\n\n")
            f.write(page.content)

        return {"message": f"Exported page {page.id} to {filename}"}

    def _tool_import_page(self, args: dict) -> Any:
        filename = args["filename"]
        with open(filename, "r", encoding="utf-8") as f:
            content = f.read()

        meta: dict[str, str] = {}
        if content.startswith("---"):
            end = content.find("---", 3)
            if end != -1:
                frontmatter = content[3:end].strip()
                for line in frontmatter.splitlines():
                    if ":" in line:
                        key, value = line.split(":", 1)
                        meta[key.strip()] = value.strip()
                content = content[end + 3 :].strip()

        path = args.get("path") or meta.get("path", "")
        title = args.get("title") or meta.get("title", "")
        if not path or not title:
            return {"error": "path and title are required"}

        tags_str = meta.get("tags", "")
        tags = (
            [t.strip() for t in tags_str.strip("[]").split(",") if t.strip()]
            if tags_str
            else []
        )

        page = Page(
            path=path,
            title=title,
            content=content,
            description=meta.get("description", ""),
            locale=meta.get("locale", "en"),
            isPublished=meta.get("published", "true").lower() == "true",
            isPrivate=meta.get("private", "false").lower() == "true",
            tags=tags,
        )
        return self.pages.create(page)

    def _tool_view_history(self, args: dict) -> Any:
        entries, total = self.pages.get_history(
            args["page_id"],
            offset_page=args.get("offset_page", 0),
            offset_size=args.get("offset_size", 100),
        )
        return {
            "total": total,
            "entries": [
                {
                    "versionId": h.versionId,
                    "versionDate": h.versionDate,
                    "authorName": h.authorName,
                    "actionType": h.actionType,
                }
                for h in entries
            ],
        }

    def _tool_view_revision(self, args: dict) -> Any:
        return self.pages.get_version(args["page_id"], args["version_id"])

    def _tool_diff_revisions(self, args: dict) -> Any:
        import difflib

        v1 = self.pages.get_version(args["page_id"], args["version_id_1"])
        v2 = self.pages.get_version(args["page_id"], args["version_id_2"])

        old_lines = v1.content.splitlines(keepends=True)
        new_lines = v2.content.splitlines(keepends=True)
        diff = "".join(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=f"v{v1.versionId}",
                tofile=f"v{v2.versionId}",
            )
        )
        return {
            "version_1": v1.versionId,
            "version_2": v2.versionId,
            "diff": diff or "No differences found",
        }

    def _tool_restore_revision(self, args: dict) -> Any:
        self.pages.restore_version(args["page_id"], args["version_id"])
        return {
            "message": f"Page {args['page_id']} restored to version {args['version_id']}"
        }

    def _tool_test_connection(self, args: dict) -> Any:
        try:
            pages = self.pages.list_all(order_by="CREATED")
            return {
                "status": "connected",
                "url": self.wiki_client.url,
                "total_pages": len(pages),
            }
        except Exception as e:
            return {"status": "failed", "error": str(e)}
```

---

## CLI Entry Point

**`wiki_cli/ai/cli.py`:**

```python
"""Interactive AI chat interface for Wiki.js management.

Flow: pick provider → pick saved key or enter new → fetch models → pick model → chat
"""

from __future__ import annotations

import sys

from wiki_cli import WikiJSError
from wiki_cli.ai.agent import WikiAgent
from wiki_cli.ai.config import (
    AIConfig, PROVIDER_DEFAULTS, fetch_models,
    get_saved_key, save_key, remove_key, list_saved_keys,
)

PROVIDERS = [
    ("openai", "OpenAI"),
    ("openrouter", "OpenRouter"),
    ("groq", "Groq"),
    ("mistral", "Mistral"),
    ("ollama", "Ollama (Local)"),
    ("ollama-cloud", "Ollama Cloud (Remote)"),
]


def _pick_provider() -> str:
    saved = list_saved_keys()
    has_saved = any(p in saved for p, _ in PROVIDERS)

    print("\n  Select a provider:\n")
    for i, (key, label) in enumerate(PROVIDERS, 1):
        marker = " *" if key in saved else ""
        print(f"  {i}. {label}{marker}")
    if has_saved:
        print(f"\n  (* = has saved API key)")
    print()

    while True:
        choice = input("  Provider [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
            return PROVIDERS[int(choice) - 1][0]
        print("  Invalid choice, try again.")


def _enter_api_key(provider: str) -> str:
    if provider == "ollama":
        return "ollama"

    saved = get_saved_key(provider)

    if saved:
        masked = saved[:8] + "..." + saved[-4:] if len(saved) > 12 else saved[:8] + "..."
        print(f"\n  Found saved API key: {masked}\n")
        print(f"  1. Use saved key")
        print(f"  2. Enter new key")
        print(f"  3. Remove saved key\n")

        choice = input("  Choice [1]: ").strip() or "1"
        if choice == "1":
            return saved
        elif choice == "3":
            remove_key(provider)
            print("  -> Saved key removed.")

    label = dict(PROVIDERS).get(provider, provider)
    print(f"\n  Enter your {label} API key:\n")

    while True:
        key = input("  API Key: ").strip()
        if key:
            save_key(provider, key)
            print(f"\n  -> Key saved ({key[:8]}...)")
            return key
        print("  API key is required for this provider.")


def _pick_model(provider: str, api_key: str) -> str:
    print("\n  Fetching available models...\n")
    models = fetch_models(provider, api_key)

    if not models:
        defaults = PROVIDER_DEFAULTS.get(provider, {})
        return defaults.get("default_model", "gpt-4o")

    print(f"  Found {len(models)} models:\n")
    col_width = 40
    for i in range(0, len(models), 2):
        row = models[i : i + 2]
        line = ""
        for j, m in enumerate(row):
            line += f"  {i+j+1:>3}. {m:<{col_width}}"
        print(line)
    print()

    while True:
        choice = input("  Model [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            return models[int(choice) - 1]
        print("  Invalid choice, try again.")


def ai_mode() -> None:
    try:
        provider = _pick_provider()
        api_key = _enter_api_key(provider)
        model = _pick_model(provider, api_key)

        defaults = PROVIDER_DEFAULTS.get(provider, {})
        config = AIConfig(provider=provider, api_key=api_key, model=model, base_url=defaults.get("base_url", ""))
        agent = WikiAgent(config)
    except (WikiJSError, Exception) as exc:
        print(f"\n  Error: {exc}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print("\n  Cancelled.")
        sys.exit(0)

    print(f"\n  Wiki.js AI Assistant | {config.provider} / {config.model}")
    print(f"  Type 'exit' to quit.\n")

    while True:
        try:
            prompt = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        if not prompt or prompt.lower() in ("exit", "quit", "q"):
            if prompt:
                print("Goodbye!")
            break
        try:
            response = agent.run(prompt)
            print(f"\n{response}\n")
        except Exception as exc:
            print(f"\nError: {exc}\n")
```

### Update `cli_main.py`

Add AI mode as menu option 17:

```python
from wiki_cli.ai.cli import ai_mode

MENU = """
========================================
       Wiki.js Manager
========================================
  --- Pages ---
  1. Create Page
  2. Fetch Page
  ...
  16. Test Connection
  17. AI Assistant
  0. Exit
========================================
"""

handlers = {
    ...
    "17": ("AI Assistant", lambda: ai_mode()),
}
```

### Update `pyproject.toml`

```toml
[project.scripts]
wiki-cli = "wiki_cli:main"
wiki-ai = "wiki_cli.ai.cli:ai_mode"
```

---

## Usage Examples

### Interactive Menu

```bash
# Start the traditional CLI menu (now with option 17 for AI)
python -m wiki_cli

# Start AI mode directly
wiki-ai
```

### Model Selection Flow

When you run `wiki-ai` (or select option 17 from the menu), you go through 3 steps:

**First run** — enter API key, it gets saved:

```
============================================
   Wiki.js AI Assistant - Setup
============================================
  Select a provider:

  1. OpenAI
  2. OpenRouter *
  3. Groq
  4. Mistral
  5. Ollama (Local)
  6. Ollama Cloud (Remote)

  (* = has saved API key)

--------------------------------------------
  Provider [1]: 2

  -> OpenRouter

--------------------------------------------
  Found saved API key: sk-or-v1...xyz9

  1. Use saved key
  2. Enter new key
  3. Remove saved key

  Choice [1]: 2

  Enter your OpenRouter API key:

  API Key: sk-or-v1-abc123def456...

  -> Key saved (sk-or-v1...)
--------------------------------------------
  Fetching available models...

  Found 345 models:

    1. ai21/jamba-large-1.7                    2. aion-labs/aion-2.0
    3. aion-labs/aion-3.0                      4. aion-labs/aion-3.0-mini
    ...
  345. zhipu/glm-4-9b-chat

  Model [1]: 73
  -> meta-llama/llama-4-scout:free

  Wiki.js AI Assistant | openrouter / meta-llama/llama-4-scout:free
  Type 'exit' to quit.
>
```

**Next runs** — saved key is reused automatically:

```
  Select a provider:

  1. OpenAI
  2. OpenRouter *       <-- shows saved key indicator

  Provider [1]: 2

  Found saved API key: sk-or-v1...xyz9

  1. Use saved key       <-- just press Enter
  ...
```

### Example Conversations

**Creating a page:**
```
> Create a page called "Getting Started" at path docs/getting-started
  with an introduction to our wiki

# AI calls: create_page(path="docs/getting-started", title="Getting Started", content="# Getting Started\n\nWelcome to our wiki...")
# Response: Created page (id=42): Page created successfully
```

**Searching and updating:**
```
> Find all pages about "authentication" and update the first one's
  description to "Auth guide v2"

# AI calls: search_pages(query="authentication")
# AI calls: update_page(page_id=15, description="Auth guide v2")
# Response: Updated page 15: Page updated successfully
```

**Multi-step operations:**
```
> Show me the history of page 8, then restore version 3

# AI calls: view_history(page_id=8)
# AI shows history table
# AI asks: "Restore to version 3? This will overwrite current content."
# User confirms
# AI calls: restore_revision(page_id=8, version_id=3)
# Response: Page 8 restored to version 3
```

**Bulk operations:**
```
> Export all pages tagged "archive" to files in ./export/

# AI calls: list_pages()
# Filters by tag
# Calls export_page() for each matching page
# Response: Exported 5 pages to ./export/
```

**Natural language content generation:**
```
> Create a page at docs/api/authentication with a guide about
  JWT token authentication best practices

# AI calls: create_page with auto-generated Markdown content
# Response: Created page with detailed JWT authentication guide
```

---

## Credential Storage

API keys are stored locally at:

```
~/.config/wiki-cli/credentials.json
```

File permissions are set to `0600` (owner read/write only). Example:

```json
{
  "openrouter": "sk-or-v1-abc123...",
  "groq": "gsk_def456..."
}
```

- Keys are never committed to git, never sent anywhere other than the provider API, and never logged.
- On first run for a provider, you enter the key and it gets saved automatically.
- On subsequent runs, the saved key is shown and you can reuse it with one keystroke.
- To remove all saved keys: `rm ~/.config/wiki-cli/credentials.json`

---

## Dependencies

All supported providers use the OpenAI-compatible API, so only one dependency is needed:

### Add to `requirements.txt`:

```
openai>=1.0.0
httpx>=0.25.0
```

### Update `pyproject.toml`:

```toml
[project.optional-dependencies]
ai = [
    "openai>=1.0.0",
    "httpx>=0.25.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

Install with:

```bash
pip install -e ".[ai]"
```

---

## Testing

### Unit Tests for Tool Dispatch

```python
# tests/test_ai_tools.py

import pytest
from unittest.mock import MagicMock, patch
from wiki_cli.ai.agent import WikiAgent
from wiki_cli.ai.config import AIConfig


@pytest.fixture
def agent():
    """Create a WikiAgent with mocked dependencies."""
    config = AIConfig(provider="openrouter", api_key="test", model="meta-llama/llama-4-scout:free")
    with patch("wiki_cli.ai.agent.WikiJSClient") as mock_client:
        with patch("wiki_cli.ai.agent.PagesManager") as mock_pages:
            agent = WikiAgent(config)
            agent.pages = mock_pages
            return agent


def test_execute_tool_create_page(agent):
    agent.pages.create.return_value = MagicMock(model_dump=lambda: {"succeeded": True})
    result = agent._execute_tool(
        "create_page",
        '{"path": "test", "title": "Test", "content": "# Hi"}',
    )
    assert result["success"] is True
    agent.pages.create.assert_called_once()


def test_execute_tool_unknown_tool(agent):
    result = agent._execute_tool("nonexistent_tool", "{}")
    assert result["success"] is False
    assert "Unknown tool" in result["error"]
```

### Integration Tests

```python
# tests/test_ai_agent.py

import pytest
from wiki_cli.ai.agent import WikiAgent
from wiki_cli.ai.config import AIConfig


@pytest.mark.integration
def test_agent_search():
    config = AIConfig()
    agent = WikiAgent(config)
    response = agent.run("List all pages in the wiki")
    assert response  # Should return a summary of pages
```

---

## Security Considerations

1. **API Keys**: Never commit `.env` files. Use environment variables or a secrets manager.

2. **Destructive Operations**: The system prompt instructs the AI to confirm before delete/restore. Consider adding a server-side guard:
   ```python
   # In agent.py, require explicit confirmation for destructive tools
   DESTRUCTIVE_TOOLS = {"delete_page", "restore_revision"}

   def _execute_tool(self, name, args):
       if name in DESTRUCTIVE_TOOLS:
           # Check for confirmation flag
           if not args.get("_confirmed"):
               return {
                   "success": False,
                   "requires_confirmation": True,
                   "message": f"Confirm {name} before executing",
               }
   ```

3. **Input Validation**: Pydantic models in `PagesManager` already validate inputs. The AI's tool arguments are parsed through `json.loads()` and passed to these models.

4. **Rate Limiting**: Free tiers have rate limits. Consider adding a daily token budget or request limit in `AIConfig`. OpenRouter and Groq enforce per-key rate limits.

5. **Prompt Injection**: The system prompt locks the AI to Wiki.js operations. For additional safety, validate that tool arguments don't contain unexpected patterns (e.g., SQL injection in page content).

---

## Supported AI Providers

| Provider | Base URL | Free Tier | Tool Calling | Model Examples |
|----------|----------|-----------|--------------|----------------|
| **OpenRouter** | `https://openrouter.ai/api/v1` | Yes (some models) | Yes | `meta-llama/llama-4-scout:free`, `google/gemini-2.0-flash-exp:free` |
| **Groq** | `https://api.groq.com/openai/v1` | Yes (generous) | Yes | `llama-3.3-70b-versatile`, `mixtral-8x7b-32768` |
| **Mistral** | `https://api.mistral.ai/v1` | Yes (limited) | Yes | `mistral-small-latest`, `mistral-tiny-latest` |
| **Ollama (local)** | `http://localhost:11434/v1` | Free forever | Yes | `llama3`, `mistral`, `codellama`, `qwen2.5` |
| **Ollama Cloud** | Your remote server | Depends on host | Yes | Same as Ollama |
| **OpenAI** | `https://api.openai.com/v1` | No | Yes | `gpt-4o`, `gpt-4o-mini` |

### Provider Setup

#### OpenRouter (Recommended for free usage)

```env
AI_PROVIDER=openrouter
AI_API_KEY=sk-or-v1-your-key-here
AI_MODEL=meta-llama/llama-4-scout:free
```

1. Sign up at [openrouter.ai](https://openrouter.ai)
2. Go to Keys → Create Key
3. Many models have free tiers (marked with `:free` suffix)

#### Groq (Fastest inference, free tier)

```env
AI_PROVIDER=groq
AI_API_KEY=gsk_your-key-here
AI_MODEL=llama-3.3-70b-versatile
```

1. Sign up at [console.groq.com](https://console.groq.com)
2. Go to API Keys → Create API Key
3. Free tier includes generous rate limits

#### Mistral

```env
AI_PROVIDER=mistral
AI_API_KEY=your-mistral-key
AI_MODEL=mistral-small-latest
```

1. Sign up at [console.mistral.ai](https://console.mistral.ai)
2. Go to API Keys → Create new key

#### Ollama (Local, 100% free)

```env
AI_PROVIDER=ollama
AI_MODEL=llama3
```

1. Install Ollama: [ollama.ai](https://ollama.ai)
2. Pull a model: `ollama pull llama3`
3. Start the server: `ollama serve`
4. No API key needed — runs entirely on your machine

#### Ollama Cloud (Remote server)

```env
AI_PROVIDER=ollama-cloud
AI_API_KEY=your-key
AI_BASE_URL=https://your-ollama-server.com/v1
AI_MODEL=llama3
```

#### OpenAI

```env
AI_PROVIDER=openai
AI_API_KEY=sk-your-key-here
AI_MODEL=gpt-4o
```

### Which Provider Should I Choose?

| Priority | Provider | Why |
|----------|----------|-----|
| **Free & easy** | OpenRouter | Free tier, 100+ models, no credit card |
| **Fastest responses** | Groq | Sub-second inference, free tier |
| **Full privacy** | Ollama | Runs locally, no data leaves your machine |
| **Best quality** | OpenAI | GPT-4o is the most capable model |
| **Good balance** | Mistral | Good quality, affordable |

---

## Limitations

1. **Large Content**: Very long page content may exceed LLM context limits. The agent summarizes large results.
2. **Complex Workflows**: Multi-step operations (e.g., "clone all pages and update their tags") may require multiple LLM round-trips.
3. **Filesystem Access**: Import/export tools read/write local files. The AI must have filesystem access to the working directory.
4. **Confirmation UX**: Destructive confirmations happen in-band (the AI asks the user). A more robust approach would use a separate confirmation prompt.
5. **Free Tier Limits**: Free models on OpenRouter/Groq have rate limits. For heavy usage, consider upgrading or using multiple providers.
6. **Tool Calling Support**: Not all models support tool calling. Free models on OpenRouter that support it include `meta-llama/llama-4-scout:free` and `google/gemini-2.0-flash-exp:free`.

---

## Future Enhancements

1. **Streaming**: Stream AI responses token-by-token for better UX.
2. **Batch Operations**: Add a `batch_execute` tool that runs multiple operations in sequence.
3. **Memory**: Store conversation history so the AI remembers context across prompts.
4. **Web UI**: Build a web interface using the same `WikiAgent` class.
5. **MCP Server**: Expose `PagesManager` as an MCP (Model Context Protocol) server for integration with Claude Desktop and other AI tools.
