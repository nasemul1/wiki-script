# wiki-script

Terminal-based Wiki.js manager with Jira integration. Manage pages, revisions, and content entirely from the CLI — query Jira issues and projects — or use natural language with the AI assistant.

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

For Jira integration:

```bash
pip install -e ".[jira]"
```

For all extras:

```bash
pip install -e ".[ai,jira]"
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### Wiki.js

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

### Jira (optional)

```env
JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token_here
JIRA_PROJECT_ALLOWLIST=PROJ1,PROJ2,PROJ3
JIRA_TIMEOUT=30
JIRA_MAX_RESULTS=50
```

- **JIRA_SERVER** — Your Jira instance URL
- **JIRA_EMAIL** — Your Jira account email
- **JIRA_API_TOKEN** — API token from Jira (Profile > Personal Access Tokens)
- **JIRA_PROJECT_ALLOWLIST** — Comma-separated project keys to access (leave empty for all)
- **JIRA_TIMEOUT** — Request timeout in seconds (default 30)
- **JIRA_MAX_RESULTS** — Max issues per search (default 50)

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

  --- Jira ---
  16. Jira: Test Connection
  17. Jira: List Projects
  18. Jira: Get Project Details
  19. Jira: Search Issues
  20. Jira: Get Issue Details
  21. Jira: View Issue Comments
  22. Jira: View Issue Changelog
  23. Jira: View Available Transitions

  --- System ---
  24. Test Wiki.js Connection

  --- AI ---
  25. AI Assistant
  0. Exit
========================================
```

Select an option by entering the number.

### Jira Usage

Jira is lazy-initialized — it only connects when you select a Jira option (16–23). If credentials are missing, you'll see an error message with setup instructions.

**Example workflows:**

```
# Test connection
> 16

# List all accessible projects
> 17

# Search issues by filter
> 19
Search by:  1. Filter (safe)  2. Raw JQL
> 1
Project key: PROJ1
Status: In Progress
Assignee: Nasimul

# Get full issue details
> 20
Issue key: PROJ1-42

# View issue changelog
> 22
Issue key: PROJ1-42
```

### AI Assistant

Start the AI assistant directly:

```bash
wiki-ai
```

Or from the main menu, select option 25.

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

Once configured, use natural language for both Wiki.js and Jira:

```
  provider:  OpenRouter
  model:     meta-llama/llama-4-scout:free

  > list all pages
  > create a page at docs/getting-started with title "Getting Started"
  > search for pages about "api"
  > show issues assigned to Nasimul in project PROJ1
  > what are the high priority bugs in PROJ2
  > show the changelog for PROJ1-42
  > what transitions are available for PROJ1-42
  > show blockers in project PROJ1
```

#### AI Commands

| Command | Description |
|---------|-------------|
| `/providers` | Switch AI provider |
| `/models` | Switch model |
| `/remove-key` | Remove saved API key |
| `/help` | Show available commands |
| `exit` | Quit |

### As a Library

#### Wiki.js

```python
from wiki_cli import WikiJSClient, PagesManager, Page

client = WikiJSClient()
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

# Connection test
pages.test_connection()
```

#### Jira

```python
from wiki_cli.jira import JiraClient, JiraManager

client = JiraClient()
jira = JiraManager(client)

# Test connection
user = jira.test_connection()
print(f"Connected as: {user['displayName']}")

# List projects
projects = jira.list_projects()
for p in projects:
    print(f"{p.key}: {p.name}")

# Search issues
issues = jira.search_issues(project="PROJ1", status="In Progress")
for i in issues:
    print(f"{i.key}: {i.summary} [{i.status}]")

# Search with raw JQL (validated for safety)
issues = jira.search_issues(jql='project = PROJ1 AND priority = "High"')

# Get issue details
issue = jira.get_issue("PROJ1-42")
print(f"{issue.key}: {issue.summary}")
print(f"Status: {issue.status}, Priority: {issue.priority}")
print(f"Assignee: {issue.assignee}, Reporter: {issue.reporter}")

# Get comments
comments = jira.get_comments("PROJ1-42")
for c in comments:
    print(f"{c.author}: {c.body[:80]}")

# Get changelog
changelog = jira.get_changelog("PROJ1-42")
for entry in changelog:
    print(f"{entry.field}: {entry.from_value} -> {entry.to_value}")

# Get available transitions
transitions = jira.get_transitions("PROJ1-42")
for t in transitions:
    print(f"{t.name} -> {t.to_status}")
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

### Jira (Read-only)

| Feature | Description |
|---------|-------------|
| **Test Connection** | Verify Jira API connectivity and return user info |
| **List Projects** | List accessible projects (filtered by allowlist) |
| **Get Project** | Retrieve project metadata by key |
| **Search Issues** | Search using filters or validated JQL queries |
| **Get Issue** | Full issue details: status, priority, assignee, labels |
| **Get Comments** | View comment thread on an issue |
| **Get Changelog** | View history of field changes on an issue |
| **Get Transitions** | Inspect available workflow transitions (read-only) |

### System

| Feature | Description |
|---------|-------------|
| **Test Connection** | Verify Wiki.js API connectivity and credentials |

### AI Assistant

| Feature | Description |
|---------|-------------|
| **Natural language** | Manage pages and query Jira using plain English |
| **Multi-provider** | Switch between OpenRouter, Groq, OpenAI, Mistral, Ollama |
| **Live model list** | Models fetched from provider API, not hardcoded |
| **Persistent config** | API keys and last-used provider/model saved locally |
| **24 tools** | AI can perform all Wiki.js + Jira operations |

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
│   ├── cli_jira.py                # Jira CLI handlers
│   ├── cli_system.py              # System handlers
│   ├── pages/
│   │   ├── __init__.py            # Re-exports PagesManager
│   │   ├── manager.py             # PagesManager class
│   │   ├── queries.py             # GraphQL CRUD queries/mutations
│   │   └── history.py             # GraphQL history queries/mutations
│   ├── jira/
│   │   ├── __init__.py            # Jira exports
│   │   ├── client.py              # JiraClient (REST API wrapper)
│   │   ├── manager.py             # JiraManager (business logic)
│   │   ├── models.py              # JiraProject, JiraIssue, JiraComment, etc.
│   │   ├── auth.py                # Authentication handling
│   │   ├── jql.py                 # JQL validation & safe query building
│   │   └── errors.py              # Jira-specific error types
│   └── ai/
│       ├── __init__.py            # AI package exports
│       ├── config.py              # Provider config, API key storage
│       ├── tools.py               # Tool schemas for LLM function calling
│       ├── agent.py               # WikiAgent (tool dispatch, LLM loop)
│       └── cli.py                 # AI assistant terminal UI
├── tests/                         # 215 tests
│   ├── conftest.py                # Shared fixtures
│   ├── test_jql_safety.py         # JQL injection tests (38)
│   ├── test_jira_models.py        # Jira model tests (16)
│   ├── test_jira_config.py        # Config & auth tests (10)
│   ├── test_jira_manager.py       # Manager operation tests (18)
│   ├── test_jira_client.py        # Client tests (14)
│   ├── test_jira_cli.py           # CLI handler tests (16)
│   ├── test_jira_ai_tools.py      # AI tool dispatch tests (19)
│   └── ... (Wiki.js tests)
├── pyproject.toml
├── requirements.txt
├── .env.example
└── README.md
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

**Jira (optional):**
- `jira` — Jira REST API client

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

Run Jira-specific tests:

```bash
pytest tests/test_jql_safety.py tests/test_jira_*.py -v
```

Run a specific test file:

```bash
pytest tests/test_jira_manager.py -v
```

Run with coverage:

```bash
pytest tests/ -v --cov=wiki_cli --cov-report=term-missing
```

### Test Breakdown

| Category | Tests |
|----------|-------|
| Wiki.js (existing) | 67 |
| JQL safety & injection | 38 |
| Jira models | 16 |
| Jira config & auth | 10 |
| Jira manager | 18 |
| Jira client | 14 |
| Jira CLI handlers | 16 |
| Jira AI tools | 19 |
| **Total** | **215** |

## Security

- **JQL injection prevention** — All JQL queries are validated against forbidden keywords and patterns
- **Project allowlisting** — Only approved projects are accessible
- **Credential safety** — API tokens stored in `.env` (gitignored) or `~/.config/wiki-cli/credentials.json` (permissions `0600`)
- **Read-only by design** — Jira connector cannot create, edit, or delete issues
- **No secrets in logs** — Credentials are never printed or logged
