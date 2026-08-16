# wiki-script

Terminal-based Wiki.js manager. Manage pages, revisions, and content entirely from the CLI — or use natural language with the AI assistant.

## Installation

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Or install as a package:

```bash
pip install .
```

For AI assistant support:

```bash
pip install -e ".[ai]"
```

## Configuration

Wiki.js credentials are managed through named profiles — no `.env` required.

**First-time setup:** Run the AI assistant (`wiki-ai`) or main menu (`wiki-cli`) and use `/switch-wiki` (or menu option 18). You'll be prompted for a profile name, URL, and API key.

**Stored at:**
- `~/.config/wiki-cli/wikis.json` — all profiles (mode `0600`)
- `~/.config/wiki-cli/active_wiki.txt` — currently active profile (mode `0600`)

**Switching wikis:**
- From the AI assistant: `/switch-wiki` (interactive), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create)
- From the main menu: option `18. Manage Wikis` (submenu with switch / add / list / remove)
- List profiles: `/wikis` or main menu option `18 → 3`
- Remove a profile: `/remove-wiki [name]` or main menu option `18 → 4` (both ask to confirm)

## Usage

### Interactive Menu

```bash
python -m wiki_cli
```

Or after installing:

```bash
wiki-cli
```

You'll see the main menu:

```
========================================
       Wiki.js Manager
========================================
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

  --- AI ---
  17. AI Assistant
  0. Exit
========================================
```

Select an option by entering the number.

### AI Assistant

Start the AI assistant directly:

```bash
wiki-ai
```

Or from the main menu, select option 17.

On first run, you'll set up your AI provider:

```
  saved providers:
    1    OpenRouter
    2    Groq
    3    add new

  >

  available providers:

    1    OpenAI
    2    OpenRouter
    3    Groq
    4    Mistral
    5    Ollama (Local)
    6    Ollama Cloud (Remote)

  >
```

Supported providers:
- **OpenRouter** — Access to hundreds of models (free tier available)
- **Groq** — Fast inference (Llama, Mixtral)
- **OpenAI** — GPT-4o, GPT-4, etc.
- **Mistral** — Mistral models
- **Ollama (Local)** — Run models locally
- **Ollama Cloud (Remote)** — Remote Ollama instances

API keys are saved to `~/.config/wiki-cli/credentials.json` (permissions `0600`). On subsequent runs, it skips provider selection and goes straight to chat.

Once configured, use natural language:

```
  provider:  OpenRouter
  model:     meta-llama/llama-4-scout:free

  > list all pages
  > create a page at docs/getting-started with title "Getting Started"
  > search for pages about "api"
  > update page 5 title to "New Title"
  > show the history of page 3
  > delete page 12
  > what's the diff between revision 1 and 2 of page 7
```

#### AI Commands

| Command | Description |
|---------|-------------|
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
| `/providers` | Switch AI provider |
| `/models` | Switch model |
| `/remove-key` | Remove saved API key |
| `/help` | Show available commands |
| `exit` | Quit |

### As a Library

```python
from wiki_cli import WikiJSClient, get_active_client, PagesManager, Page

client = get_active_client()
pages = PagesManager(client)

# Create a page
page = Page(path="docs/intro", title="Introduction", content="# Hello")
resp = pages.create(page)
print(f"Created page {resp.page.id}")

# Fetch by ID
fetched = pages.get_by_id(resp.page.id)

# Fetch by path
fetched = pages.get_by_path("docs/intro")

# Update
fetched.content += "\n\nMore content here."
pages.update(fetched)

# Search
results = pages.search("intro")

# List all pages
all_pages = pages.list_all()

# Move/Rename
pages.move_or_rename(resp.page.id, "docs/new-intro")

# Clone
clone = pages.clone_page(resp.page.id, "docs/clone", "Cloned Page")

# History
history, total = pages.get_history(resp.page.id)
version = pages.get_version(resp.page.id, history[0].versionId)
pages.restore_version(resp.page.id, history[0].versionId)

# Delete
pages.delete(resp.page.id)

# Export to file
pages.export_to_file(resp.page.id, "export.md")

# Import from file
pages.import_from_file("import.md", "docs/imported")

# Connection test
pages.test_connection()
```

## Features

### Pages

| Feature | Description |
|---------|-------------|
| **Create** | Create a new page with path, title, and content |
| **Fetch** | View a page by ID or path |
| **Update** | Edit page title, content, description, path, or tags |
| **Delete** | Remove a page permanently |
| **List** | View all pages sorted by title, ID, or creation date |
| **Search** | Full-text search across page titles and content |
| **Browse** | Hierarchical tree view of all pages |
| **Move/Rename** | Change a page's path or title |
| **Clone** | Duplicate a page to a new path |
| **Export** | Save a page as Markdown with YAML frontmatter |
| **Import** | Create a page from a Markdown file |

### History

| Feature | Description |
|---------|-------------|
| **View History** | Browse revision history with pagination |
| **View Revision** | Inspect any past version of a page |
| **Diff** | Compare two revisions side by side |
| **Restore** | Rollback to any previous version |

### System

| Feature | Description |
|---------|-------------|
| **Test Connection** | Verify Wiki.js API connectivity and credentials |

### AI Assistant

| Feature | Description |
|---------|-------------|
| **Natural language** | Manage pages using plain English prompts |
| **Multi-provider** | Switch between OpenRouter, Groq, OpenAI, Mistral, Ollama |
| **Live model list** | Models fetched from provider API, not hardcoded |
| **Persistent config** | API keys and last-used provider/model saved locally |
| **16 tools** | AI can perform all page operations, history, search, and more |

## Project Structure

```
wiki-script/
├── wiki_cli/                      # Main package
│   ├── __init__.py                # Public API & exports
│   ├── client.py                  # WikiJSClient (GraphQL transport)
│   ├── exceptions.py              # WikiJSError
│   ├── models.py                  # Page, PageResponse, PageHistory, PageVersion
│   ├── utils.py                   # Shared CLI helpers
│   ├── cli_main.py                # Menu loop & handler dispatch
│   ├── cli_pages.py               # Page CRUD handlers
│   ├── cli_history.py             # History/revision handlers
│   ├── cli_system.py              # System handlers
│   ├── pages/
│   │   ├── __init__.py            # Re-exports PagesManager
│   │   ├── manager.py             # PagesManager class
│   │   ├── queries.py             # GraphQL CRUD queries/mutations
│   │   └── history.py             # GraphQL history queries/mutations
│   └── ai/
│       ├── __init__.py            # AI package exports
│       ├── config.py              # Provider config, API key storage
│       ├── tools.py               # Tool schemas for LLM function calling
│       ├── agent.py               # WikiAgent (tool dispatch, LLM loop)
│       └── cli.py                 # AI assistant terminal UI
├── tests/                         # 67 tests
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
├── AI_INTEGRATION.md              # AI assistant documentation
├── README.md
├── TEST_PLAN.md
└── plan.md
```

## Dependencies

**Core:**
- Python 3.10+
- `gql[requests]` — GraphQL client
- `pydantic` — Data validation
- `python-dotenv` — Environment variables

**AI (optional):**
- `openai` — OpenAI-compatible API client (works with all providers)
- `httpx` — HTTP client for model listing

**Dev:**
- `pytest` — Test framework
- `pytest-cov` — Coverage reporting

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
