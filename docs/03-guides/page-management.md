# Page Management

Deep dive into creating, organizing, and maintaining wiki pages.

## Page Structure

Every Wiki.js page has these fields:

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `path` | Yes | — | URL path (e.g. `docs/intro`) |
| `title` | Yes | — | Display title |
| `content` | No | `""` | Page body in Markdown |
| `description` | No | `""` | Short description for SEO |
| `tags` | No | `[]` | Categorization tags |
| `editor` | No | `"markdown"` | Editor type |
| `locale` | No | `"en"` | Language code |
| `isPublished` | No | `True` | Whether page is live |
| `isPrivate` | No | `False` | Whether page is private |

## Path Conventions

Paths determine the URL structure:

```
docs/intro           → your-wiki.com/docs/intro
docs/api/v2/auth     → your-wiki.com/docs/api/v2/auth
getting-started      → your-wiki.com/getting-started
```

**Best practices:**
- Use lowercase with hyphens: `my-page`, not `My_Page` or `MyPage`
- Use slashes for hierarchy: `docs/api/auth`
- Keep paths descriptive but concise
- Avoid spaces and special characters

## Creating Pages

### Via CLI

```
wiki-cli → Option 1
```

### Via AI

```
> create a page at docs/api/authentication about user auth tokens
```

### Via Python

```python
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
pages = PagesManager(client)

page = Page(
    path="docs/api/authentication",
    title="Authentication",
    content="# Authentication\n\nUse API tokens for auth.",
    description="API authentication guide",
    tags=["api", "security"],
    locale="en",
    isPublished=True,
    isPrivate=False,
)
response = pages.create(page)
print(f"Created page {response.page.id}")
```

## Updating Pages

### Content Options

When updating via CLI, you have three content options:

1. **Replace** — overwrite the entire content
2. **Append** — add new content after existing content
3. **Keep** — don't change the content

### Partial Updates

The AI and Python API support partial updates — only specify the fields you want to change:

```python
page = pages.get_by_id(5)
page.title = "New Title"
pages.update(page)
# Only title is changed; content, description, etc. remain the same
```

### Via AI

```
> update page 5 title to "New Title"
> change page 3 description to "Updated description"
> add tags "important" and "review" to page 8
> mark page 12 as unpublished
```

## Organizing Pages

### Tree Structure

Pages are organized hierarchically by path:

```
/ (root)
├── docs/
│   ├── getting-started (id=1)
│   ├── api/
│   │   ├── reference (id=2)
│   │   └── authentication (id=3)
│   └── faq (id=4)
├── guides/
│   ├── installation (id=5)
│   └── configuration (id=6)
```

### Moving Pages

Moving a page changes its path:

```
wiki-cli → Option 8
```

```
> move page 5 to guides/setup/installation
```

### Cloning Pages

Cloning creates a copy at a new path:

```
wiki-cli → Option 9
```

```
> clone page 3 to docs/api/v2/authentication with title "Auth v2"
```

### Tags

Tags help organize and filter pages:

```python
page = pages.get_by_id(5)
page.tags = ["api", "v2", "authentication"]
pages.update(page)
```

Filter by tag in list/search:

```
wiki-cli → Option 5 → Filter by tag: api
```

```
> list all pages tagged "api"
```

## Import and Export

### Export Format

Pages export as Markdown with YAML frontmatter:

```yaml
---
title: Authentication
path: docs/api/authentication
description: API authentication guide
tags: [api, security]
published: true
private: false
locale: en
---

# Authentication

Use API tokens for auth.
```

### Import Rules

1. If the file has YAML frontmatter, `path` and `title` are extracted from it
2. If no frontmatter, you're prompted for path and title
3. Tags in frontmatter format `[tag1, tag2]` are parsed automatically
4. The rest of the file becomes the page content

### Bulk Operations

Export all pages, edit them locally, then import:

```bash
# Export via CLI (repeat for each page)
wiki-cli → Option 10

# Or programmatically
python -c "
from wiki_cli import WikiJSClient, PagesManager
client = WikiJSClient()
pages = PagesManager(client)
for p in pages.list_all():
    pages.export_to_file(p.id, f'backup/{p.path.replace(\"/\", \"_\")}.md')
"
```

## Page Lifecycle

```
Create → Edit → Publish → Review → Update → (Archive | Delete)
                        ↗
              Import ──┘
```

1. **Create** — new page with content
2. **Edit** — update content, metadata, tags
3. **Publish** — set `isPublished = True`
4. **Review** — check history, diff changes
5. **Update** — revise content
6. **Archive** — set `isPublished = False` (unpublish)
7. **Delete** — permanently remove
