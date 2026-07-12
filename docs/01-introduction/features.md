# Features

wiki-script provides comprehensive Wiki.js management through two interfaces: an interactive CLI menu and an AI-powered natural language assistant.

## Page Management

| Feature | CLI Menu | AI Assistant | Description |
|---------|----------|--------------|-------------|
| Create Page | Option 1 | `create_page` | Create a new page with path, title, content, tags, and metadata |
| Fetch Page | Option 2 | `fetch_page` | View a page by ID or path with all its fields |
| Update Page | Option 3 | `update_page` | Edit title, content (replace/append/keep), description, tags, publish status |
| Delete Page | Option 4 | `delete_page` | Permanently remove a page (requires confirmation) |
| List Pages | Option 5 | `list_pages` | View all pages sorted by title, path, created, or updated date |
| Search Pages | Option 6 | `search_pages` | Full-text search across page titles and content |
| Browse Tree | Option 7 | `browse_tree` | Hierarchical tree view of all pages with Unicode box-drawing |
| Move/Rename | Option 8 | `move_page` | Change a page's path or title with diff preview |
| Clone Page | Option 9 | `clone_page` | Duplicate a page to a new path with a new title |
| Export Page | Option 10 | `export_page` | Save a page as Markdown with YAML frontmatter |
| Import Page | Option 11 | `import_page` | Create a page from a Markdown file (auto-parses frontmatter) |

## Revision History

| Feature | CLI Menu | AI Assistant | Description |
|---------|----------|--------------|-------------|
| View History | Option 12 | `view_history` | Browse revision history with pagination |
| View Revision | Option 13 | `view_revision` | Inspect any past version of a page |
| Diff Revisions | Option 14 | `diff_revisions` | Compare two revisions side by side (unified diff) |
| Restore Revision | Option 15 | `restore_revision` | Rollback to any previous version (requires confirmation) |

## System

| Feature | CLI Menu | AI Assistant | Description |
|---------|----------|--------------|-------------|
| Test Connection | Option 16 | `test_connection` | Verify API connectivity and credentials |

## AI Assistant

| Feature | Description |
|---------|-------------|
| Natural language interface | Chat in plain English to manage pages |
| Multi-provider support | OpenAI, OpenRouter, Groq, Mistral, Ollama, Ollama Cloud |
| Live model listing | Models fetched from provider API, not hardcoded |
| Conversation history | AI remembers context across messages |
| Activity logging | Real-time display of tool calls and results |
| Multi-line editor | Open `$EDITOR` for writing content with `/edit` |
| Persistent config | API keys and last-used provider/model saved locally |
| Slash commands | `/help`, `/clear`, `/edit`, `/providers`, `/models`, `/remove-key` |

## CLI Features

| Feature | Description |
|---------|-------------|
| Paginated output | Lists show 20 items per page with next/quit navigation |
| Input validation | All numeric IDs validated before use |
| Confirmation prompts | Destructive operations require explicit confirmation |
| Default values | Optional fields use sensible defaults when left blank |
| Tag filtering | Filter list/search results by tag (case-insensitive) |
| ANSI formatting | Clean, colored terminal output with Unicode box-drawing |

## Technical Features

| Feature | Description |
|---------|-------------|
| GraphQL transport | Handles authentication, retries (3x), and error parsing |
| Pydantic models | Type-safe data structures with field validation |
| Lazy imports | AI module only loaded when selected, keeping startup fast |
| Secure credentials | API keys stored with `0600` file permissions |
| Provider-agnostic AI | All providers use OpenAI-compatible API — single SDK |
| Extensive tests | 67 tests covering all CLI handlers, no network required |
