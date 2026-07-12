# Command Reference

Complete reference for all CLI menu options and AI assistant commands.

## CLI Menu Options (`wiki-cli`)

### Pages

| Option | Command | Description |
|--------|---------|-------------|
| 1 | Create Page | Create a new wiki page |
| 2 | Fetch Page | View a page by ID or path |
| 3 | Update Page | Edit page content, title, tags, or metadata |
| 4 | Delete Page | Permanently remove a page |
| 5 | List Pages | View all pages with sorting and filtering |
| 6 | Search Pages | Full-text search across pages |
| 7 | Browse Tree | Hierarchical tree view of all pages |
| 8 | Move/Rename | Change a page's path or title |
| 9 | Clone Page | Duplicate a page to a new path |
| 10 | Export Page | Save a page as Markdown with frontmatter |
| 11 | Import Page | Create a page from a Markdown file |

### History

| Option | Command | Description |
|--------|---------|-------------|
| 12 | View History | Browse revision history with pagination |
| 13 | View Revision | Inspect a specific version |
| 14 | Diff Revisions | Compare two versions side by side |
| 15 | Restore Revision | Rollback to a previous version |

### System

| Option | Command | Description |
|--------|---------|-------------|
| 16 | Test Connection | Verify API connectivity |

### Other

| Option | Command | Description |
|--------|---------|-------------|
| 17 | AI Assistant | Launch the AI chat interface |
| 0 | Exit | Quit the application |

## CLI Input Prompts

### Create Page (Option 1)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Path | Yes | — | URL path (e.g. `docs/intro`) |
| Title | Yes | — | Page title |
| Content | No | `""` | Markdown body (multi-line) |
| Description | No | `""` | Short description |
| Tags | No | `[]` | Comma-separated tags |
| Locale | No | `"en"` | Language code |
| Private | No | `n` | `y` or `n` |
| Published | No | `y` | `y` or `n` |

### Fetch Page (Option 2)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Choice | No | `1` | `1` = by ID, `2` = by path |
| Page ID | Yes* | — | Numeric page ID |
| Path | Yes* | — | Page path |
| Locale | No | `"en"` | Language code (path only) |

### Update Page (Option 3)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| New title | No | current | Leave blank to keep |
| New description | No | current | Leave blank to keep |
| Content option | No | `3` | `1`=Replace, `2`=Append, `3`=Keep |
| Content | If 1 or 2 | — | New/append content |
| Tags | No | current | Comma-separated |
| Published | No | current | `y` or `n` |

### Delete Page (Option 4)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| Confirm | Yes | — | Must type `yes` |

### List Pages (Option 5)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Sort | No | `1` | `1`=Title, `2`=Path, `3`=Created, `4`=Updated |
| Filter tag | No | none | Case-insensitive tag filter |

### Search Pages (Option 6)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Query | Yes | — | Search text |
| Locale | No | any | Language filter |
| Filter tag | No | none | Case-insensitive tag filter |

### Browse Tree (Option 7)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| View page ID | No | skip | Enter ID to view details |

### Move/Rename (Option 8)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| New path | No | current | Leave blank to keep |
| New title | No | current | Leave blank to keep |
| Confirm | Yes | — | `yes` or `no` |

### Clone Page (Option 9)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Source ID | Yes | — | Numeric page ID |
| New path | Yes | — | Target path |
| New title | No | source title | Custom title |

### Export Page (Option 10)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| Filename | No | `{path}.md` | Output filename |

### Import Page (Option 11)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Filename | Yes | — | Markdown file path |
| Path | If no frontmatter | — | Page path |
| Title | If no frontmatter | — | Page title |

### View History (Option 12)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |

### View Revision (Option 13)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| Version ID | Yes | — | Numeric version ID |

### Diff Revisions (Option 14)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| Version 1 | Yes | — | Older version ID |
| Version 2 | Yes | — | Newer version ID |

### Restore Revision (Option 15)

| Prompt | Required | Default | Description |
|--------|----------|---------|-------------|
| Page ID | Yes | — | Numeric page ID |
| Version ID | Yes | — | Version to restore |
| Confirm | Yes | — | Must type `yes` |

## AI Assistant Commands (`wiki-ai`)

### Slash Commands

| Command | Description |
|---------|-------------|
| `/edit` | Open `$EDITOR` for multi-line input |
| `/clear` | Clear conversation history |
| `/providers` | Switch AI provider (re-runs setup) |
| `/models` | Switch AI model |
| `/remove-key` | Remove saved API key for current provider |
| `/help` | Show available commands |
| `exit` | Quit the assistant |

### AI Tool Functions

These are called automatically by the LLM when you use natural language:

| Tool | Parameters | Description |
|------|-----------|-------------|
| `create_page` | path, title, content, description?, tags?, isPublished?, isPrivate?, locale? | Create a page |
| `fetch_page` | page_id? or path?, locale? | Fetch a page |
| `update_page` | page_id, title?, content?, description?, tags?, isPublished?, isPrivate? | Update a page |
| `delete_page` | page_id | Delete a page |
| `list_pages` | order_by? (TITLE, PATH, CREATED, UPDATED) | List all pages |
| `search_pages` | query, locale? | Search pages |
| `browse_tree` | — | Build page tree |
| `move_page` | page_id, new_path | Move/rename a page |
| `clone_page` | source_id, new_path, new_title | Clone a page |
| `export_page` | page_id, filename | Export to file |
| `import_page` | filename, path?, title? | Import from file |
| `view_history` | page_id, offset_page?, offset_size? | View revision history |
| `view_revision` | page_id, version_id | View a specific version |
| `diff_revisions` | page_id, version_id_1, version_id_2 | Diff two versions |
| `restore_revision` | page_id, version_id | Restore a version |
| `test_connection` | — | Test API connection |

## Python Library API

### WikiJSClient

```python
from wiki_cli import WikiJSClient

client = WikiJSClient()  # reads from env
client = WikiJSClient(url="...", api_key="...")  # explicit
```

### PagesManager Methods

```python
from wiki_cli import PagesManager

pages = PagesManager(client)

# CRUD
page = pages.create(Page(...))
page = pages.get_by_id(5)
page = pages.get_by_path("docs/intro")
response = pages.update(page)
pages.delete(5)

# List & Search
all_pages = pages.list_all(order_by="TITLE")
results = pages.search("query")

# Organization
pages.move_or_rename(5, "new/path")
pages.clone_page(5, "new/path", "New Title")

# History
entries, total = pages.get_history(5)
version = pages.get_version(5, 10)
pages.restore_version(5, 10)

# File I/O
pages.export_to_file(5, "export.md")
pages.import_from_file("import.md", "new/path")

# System
pages.test_connection()
```
