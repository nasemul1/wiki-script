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
    {
        "type": "function",
        "function": {
            "name": "browse_tree",
            "description": "Show all pages as a hierarchical tree based on their path segments. Useful for seeing the wiki structure.",
            "parameters": {
                "type": "object",
                "properties": {},
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
            "name": "move_pages",
            "description": "Move multiple pages at once. Each move specifies a page ID and new path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "moves": {
                        "type": "array",
                        "description": "List of moves to perform",
                        "items": {
                            "type": "object",
                            "properties": {
                                "page_id": {
                                    "type": "integer",
                                    "description": "Page ID to move",
                                },
                                "new_path": {
                                    "type": "string",
                                    "description": "New path for the page",
                                },
                            },
                            "required": ["page_id", "new_path"],
                        },
                    },
                },
                "required": ["moves"],
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
