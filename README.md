# wiki-script

Terminal-based Wiki.js manager. Manage pages and revisions entirely from the CLI.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install .
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

## Usage

### Interactive Menu

```bash
python main.py
```

```
=========================================
       Wiki.js Manager
=========================================
  --- Pages ---
  1. Create Page
  2. Fetch Page
  3. Update Page
  4. Delete Page
  5. List Pages
  6. Search Pages
  7. Browse Pages (tree)
  8. Move/Rename Page
  9. Clone Page
  10. Export Page to File
  11. Import Page from File

  --- History ---
  12. View Page History
  13. View Specific Revision
  14. Diff Two Revisions
  15. Restore Revision

  --- System ---
  16. Test Connection
  0. Exit
=========================================
```

### Standalone Scripts

Each operation is a standalone script. Run with `--help` for options.

```bash
# Create a page
python scripts/create_page.py "projects/alpha/overview" "Project Alpha" "# Hello World" \
    --description "Overview page" --tags "project,alpha"

# Fetch a page
python scripts/fetch_page.py --id 15
python scripts/fetch_page.py --path projects/alpha/overview

# Update a page
python scripts/update_page.py --id 15 --title "New Title" --published --no-private

# Delete a page
python scripts/delete_page.py 15
```

### As a Library

```python
from wiki_script import WikiJSClient, Page, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Create
page = Page(path="docs/intro", title="Intro", content="# Hi", description="Intro page")
resp = pages.create(page)

# Fetch
fetched = pages.get_by_id(resp.page.id)

# Search
results = pages.search("intro")

# Update
fetched.content += "\n\nUpdated."
pages.update(fetched)

# Move/Rename
pages.move_or_rename(resp.page.id, "docs/introduction")

# Clone
clone_resp = pages.clone_page(resp.page.id, "docs/intro-copy", "Intro Copy")

# History
history, total = pages.get_history(resp.page.id)
version = pages.get_version(resp.page.id, history[0].versionId)
pages.restore_version(resp.page.id, history[0].versionId)

# Export/Import (file I/O)

# Delete
pages.delete(resp.page.id)
```

## Features

### Pages
- **CRUD**: Create, read, update, delete pages
- **Search**: Full-text search across pages
- **Browse**: Tree view of page hierarchy
- **Move/Rename**: Change page path or title
- **Clone**: Duplicate a page to a new path
- **Export**: Save page as Markdown with YAML frontmatter
- **Import**: Create page from Markdown file

### History
- **View History**: Browse revision history with pagination
- **View Revision**: Inspect any past version
- **Diff**: Compare two revisions side by side
- **Restore**: Rollback to any previous version

### System
- **Connection Test**: Verify API connectivity

## Project Structure

```
wiki-script/
├── main.py                    # Interactive terminal menu
├── scripts/                   # Standalone CLI scripts
│   ├── create_page.py
│   ├── fetch_page.py
│   ├── update_page.py
│   └── delete_page.py
├── wiki_script/               # Core library
│   ├── __init__.py
│   ├── exceptions.py          # WikiJSError
│   ├── models.py              # Page, PageHistory, PageVersion (Pydantic)
│   ├── wiki_client.py         # WikiJSClient (gql transport)
│   └── operations/
│       ├── __init__.py
│       └── pages.py           # PagesManager (GraphQL CRUD + history)
├── requirements.txt
├── pyproject.toml
├── .env.example
└── plan.md
```

## Dependencies

- Python 3.10+
- gql[requests] — GraphQL client
- pydantic — Data validation
- python-dotenv — Environment variables
