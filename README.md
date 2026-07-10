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
python cli.py
```

### As a Library

```python
from wiki_cli import WikiJSClient, Page, PagesManager

client = WikiJSClient()
pages = PagesManager(client)

# Create
page = Page(path="docs/intro", title="Intro", content="# Hi")
resp = pages.create(page)

# Fetch
fetched = pages.get_by_id(resp.page.id)

# Search
results = pages.search("intro")

# Update
fetched.content += "\n\nUpdated."
pages.update(fetched)

# History
history, total = pages.get_history(resp.page.id)
version = pages.get_version(resp.page.id, history[0].versionId)
pages.restore_version(resp.page.id, history[0].versionId)

# Delete
pages.delete(resp.page.id)
```

## Running Tests

```bash
# TBD
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
├── .env.example
├── README.md
└── plan.md
```

## Dependencies

- Python 3.10+
- gql[requests] — GraphQL client
- pydantic — Data validation
- python-dotenv — Environment variables
