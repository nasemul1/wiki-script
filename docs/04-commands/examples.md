# Examples

Real-world examples for common tasks.

## CLI Examples

### Set Up Documentation Structure

```bash
wiki-cli
```

```
Option: 1
Path: docs/getting-started
Title: Getting Started
Content: # Getting Started

Welcome to our documentation.

Tags: docs, intro
Published: y
```

```
Option: 1
Path: docs/api/reference
Title: API Reference
Content: # API Reference

Complete API documentation.

Tags: api, reference
Published: y
```

```
Option: 1
Path: docs/guides/deployment
Title: Deployment Guide
Content: # Deployment Guide

How to deploy the application.

Tags: guides, deployment
Published: y
```

### Restructure Your Wiki

Move pages to a new structure:

```
Option: 8
Page ID: 5
New path: docs/guides/setup/installation
```

### Bulk Export

```bash
python -c "
from wiki_cli import WikiJSClient, PagesManager
import os

client = WikiJSClient()
pages = PagesManager(client)

os.makedirs('backup', exist_ok=True)
for p in pages.list_all():
    filename = f\"backup/{p.path.replace('/', '_')}.md\"
    pages.export_to_file(p.id, filename)
    print(f'Exported: {filename}')
"
```

### Review Recent Changes

```
Option: 12
Page ID: 5

VerID  Date                 Author    Action
-----  ----                 ------    ------
  15   2025-01-15 14:30:00  admin     UPDATE
  14   2025-01-14 10:15:00  admin     CREATE
```

```
Option: 14
Page ID: 5
Version 1: 14
Version 2: 15

--- v14
+++ v15
@@ -1,5 +1,8 @@
 # Getting Started

 Welcome to our documentation.
+
+## Installation
+
+Run `pip install wiki-script`.
```

## AI Assistant Examples

### Create and Refine

```
> create a page at docs/api/authentication about JWT tokens with code examples

▸ Creating page  docs/api/authentication
✓ page created (id=42)

The page has been created with sections on JWT structure, token generation,
and API usage examples.
```

```
> add a section about token refresh to that page

▸ Updating page  id=42
✓ page updated

Added a "Token Refresh" section with explanation and code examples.
```

### Organize Pages

```
> list all pages tagged "api"

There are 8 pages tagged "api":
1. docs/api/authentication (id=42)
2. docs/api/endpoints (id=43)
3. docs/api/errors (id=44)
...
```

```
> move page 42 to docs/api/v2/authentication

▸ Moving page  id=42 → docs/api/v2/authentication
✓ page moved

Page 42 has been moved to docs/api/v2/authentication.
```

### Audit Changes

```
> show me the history of page 5

Page 5 has 12 revisions:
- v12: 2025-01-15 by admin (UPDATE)
- v11: 2025-01-14 by admin (UPDATE)
- v10: 2025-01-13 by john (CREATE)
...
```

```
> diff version 10 and version 12 of page 5

The main changes between v10 and v12:
- Added new section on rate limiting
- Updated authentication examples
- Fixed typo in error codes table
```

### Backup and Restore

```
> export page 42 to backup-auth.md

✓ Exported page 42 to backup-auth.md

> restore page 42 to version 8

Are you sure you want to restore page 42 to version 8? (yes/no): yes
✓ Version restored

Page 42 has been restored to version 8.
```

## Python Library Examples

### Create a Page

```python
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
pages = PagesManager(client)

page = Page(
    path="docs/api/authentication",
    title="API Authentication",
    content="""# API Authentication

All API requests require a bearer token.

## Usage

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" https://api.example.com/data
```
""",
    description="How to authenticate API requests",
    tags=["api", "security"],
    locale="en",
    isPublished=True,
    isPrivate=False,
)

response = pages.create(page)
print(f"Created page {response.page.id}")
```

### Search and Update

```python
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Find pages about authentication
results = pages.search("authentication")
for page in results:
    print(f"  {page.id}: {page.path} - {page.title}")

# Update the first result
page = pages.get_by_id(results[0].id)
page.content += "\n\n## Rate Limiting\n\nMax 100 requests per minute."
pages.update(page)
print(f"Updated page {page.id}")
```

### Export All Pages

```python
from wiki_cli import WikiJSClient, PagesManager
import os

client = WikiJSClient()
pages = PagesManager(client)

os.makedirs("wiki-export", exist_ok=True)

for page in pages.list_all(order_by="PATH"):
    filename = f"wiki-export/{page.path.replace('/', '_')}.md"
    pages.export_to_file(page.id, filename)
    print(f"Exported: {page.path} → {filename}")
```

### Custom Script

```python
from wiki_cli import WikiJSClient, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Find all unpublished drafts
all_pages = pages.list_all()
drafts = [p for p in all_pages if not p.isPublished]

print(f"Found {len(drafts)} unpublished pages:")
for page in drafts:
    print(f"  [{page.id}] {page.path} - {page.title}")

# Publish all drafts
for page in drafts:
    page.isPublished = True
    pages.update(page)
    print(f"Published: {page.path}")
```
