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
python -m wiki_cli
```

Or after installing:

```bash
wiki-cli
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
├── wiki_cli/                      # Main package
│   ├── __init__.py                # Public API & exports
│   ├── client.py                  # WikiJSClient (gql transport)
│   ├── exceptions.py              # WikiJSError
│   ├── models.py                  # Page, PageResponse, PageHistory, PageVersion
│   ├── utils.py                   # Shared CLI helpers
│   ├── cli_main.py                # Menu loop & handler dispatch
│   ├── cli_pages.py               # Page CRUD handlers
│   ├── cli_history.py             # History/revision handlers
│   ├── cli_system.py              # System handlers
│   └── pages/
│       ├── __init__.py            # Re-exports PagesManager
│       ├── manager.py             # PagesManager class
│       ├── queries.py             # GraphQL CRUD queries/mutations
│       └── history.py             # GraphQL history queries/mutations
├── tests/                         # E2E tests (67 tests)
│   ├── conftest.py                # Shared fixtures
│   ├── test_create_page.py        # Create Page (6 tests)
│   ├── create_page/               # success.py, validation.py, defaults.py
│   ├── test_fetch_page.py         # Fetch Page (5 tests)
│   ├── fetch_page/                # success.py, validation.py
│   ├── test_update_page.py        # Update Page (5 tests)
│   ├── update_page/               # success.py, validation.py
│   ├── test_delete_page.py        # Delete Page (3 tests)
│   ├── delete_page/               # success.py, validation.py
│   ├── test_list_pages.py         # List Pages (5 tests)
│   ├── list_pages/                # success.py
│   ├── test_search_pages.py       # Search Pages (5 tests)
│   ├── search_pages/              # success.py
│   ├── test_browse_tree.py        # Browse Tree (4 tests)
│   ├── browse_tree/               # success.py
│   ├── test_move_rename.py        # Move/Rename (4 tests)
│   ├── move_rename/               # success.py
│   ├── test_clone_page.py         # Clone Page (3 tests)
│   ├── clone_page/                # success.py
│   ├── test_export_page.py        # Export Page (3 tests)
│   ├── export_page/               # success.py
│   ├── test_import_page.py        # Import Page (4 tests)
│   ├── import_page/               # success.py
│   ├── test_view_history.py       # View History (3 tests)
│   ├── view_history/              # success.py
│   ├── test_view_revision.py      # View Revision (3 tests)
│   ├── view_revision/             # success.py
│   ├── test_diff_revisions.py     # Diff Revisions (4 tests)
│   ├── diff_revisions/            # success.py
│   ├── test_restore_revision.py   # Restore Revision (4 tests)
│   ├── restore_revision/          # success.py
│   ├── test_connection.py         # Test Connection (2 tests)
│   ├── connection/                # success.py
│   ├── test_main_menu.py          # Main Menu (4 tests)
│   └── main_menu/                 # success.py
├── pyproject.toml
├── requirements.txt
├── .env.example
├── README.md
├── TEST_PLAN.md
└── plan.md
```

## Dependencies

- Python 3.10+
- gql[requests] — GraphQL client
- pydantic — Data validation
- python-dotenv — Environment variables

## Testing

Install dev dependencies:

```bash
pip install -e ".[dev]"
```

Run all tests:

```bash
pytest tests/ -v
```

Run a specific feature:

```bash
pytest tests/test_create_page.py -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=wiki_cli --cov-report=term-missing
```

### Test Structure

Each feature has a modular test layout:

```
tests/
├── test_create_page.py        # Test file (calls functions below)
├── create_page/
│   ├── success.py             # Happy path tests
│   ├── validation.py          # Error handling tests
│   └── defaults.py            # Default value tests
```

- **`success.py`** — Feature works correctly with valid inputs
- **`validation.py`** — Invalid/missing inputs are rejected
- **`defaults.py`** — Default values applied when fields left blank
