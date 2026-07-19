# Jira Connector — Complete Process & Implementation Plan

## Task Reference

- **Task ID**: TASK-20260715-008
- **Initiative**: LILAC-CONNECTORS-V1
- **Connector**: Jira (read-only)
- **Owner**: Nasimul
- **Reviewer**: Naveed
- **Status**: Doing

---

## 1. Feasibility Assessment

### Can this feature be added to wiki-script?

**Yes.** The project has clean, replicable patterns that make a Jira connector feasible.

### What the task assumes vs what exists

| Task Assumption | Reality | Impact |
|-----------------|---------|--------|
| Shared connector platform exists | No | Must build Jira as standalone subpackage |
| BaseConnector contract exists | No | Use concrete class, no ABC needed |
| Connector registry exists | No | Add to existing menu system |
| GitHub connector foundation exists | No | Jira becomes the first multi-source connector |
| `plan.md` exists | No | Architecture decisions documented here instead |
| `wiki_platform/` package exists | No | Add under existing `wiki_cli/` |

### Why it still works

The existing architecture has a clean 3-layer pattern:

```
CLI handlers → Manager → Client → External API
```

This pattern can be replicated for Jira without touching existing Wiki.js code:

```
cli_jira.py → JiraManager → JiraClient → Jira REST API
```

---

## 2. Current Architecture (What We're Working With)

### Layer diagram

```
┌─────────────────────────────────────────────────────┐
│                    CLI Layer                         │
│  cli_main.py (menu) → cli_pages.py / cli_history.py │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 Business Logic Layer                 │
│              pages/manager.py (PagesManager)         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                  Transport Layer                     │
│             client.py (WikiJSClient)                 │
│              gql + GraphQL over HTTP                 │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│                 External Service                     │
│                  Wiki.js GraphQL API                 │
└─────────────────────────────────────────────────────┘
```

### Key files to understand

| File | Lines | Role |
|------|-------|------|
| `wiki_cli/client.py` | 82 | GraphQL transport, auth, error wrapping |
| `wiki_cli/pages/manager.py` | 262 | All page operations, response parsing |
| `wiki_cli/models.py` | 63 | Pydantic data models |
| `wiki_cli/exceptions.py` | 23 | Single error class |
| `wiki_cli/cli_main.py` | 118 | Menu loop, handler dispatch |
| `wiki_cli/cli_pages.py` | 389 | CLI handlers (input → manager call → print) |
| `wiki_cli/ai/tools.py` | 393 | 17 AI tool schemas |
| `wiki_cli/ai/agent.py` | 581 | Tool dispatch, LLM loop |
| `pyproject.toml` | 38 | Dependencies, entry points |

### Patterns to reuse

1. **Client class** — Simple wrapper around API, reads env vars, raises custom errors
2. **Manager class** — Typed methods that build requests, execute, parse into Pydantic models
3. **Pydantic models** — All data structures validated with Pydantic v2
4. **CLI handlers** — Standalone functions taking a manager, using `input()` and `print()`
5. **Menu dispatch** — Dict mapping menu choices to `(label, handler)` tuples
6. **AI tools** — JSON schema dicts + handler methods in agent
7. **Tests** — `unittest.mock.patch("builtins.input")` + `MagicMock(spec=Manager)`

---

## 3. Implementation Plan

### Phase 1: Foundation (Day 1–2)

#### 3.1 Add Jira dependencies

```toml
# pyproject.toml — add optional dependency group
[project.optional-dependencies]
jira = [
    "jira>=3.5.0",
]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```

**Decision: Use `jira` Python library (JIRA-001)**
- Most maintained Jira client
- Handles pagination, auth, error mapping
- Supports Jira Cloud and Server
- Alternative: direct REST API with `httpx` (more control, more code)

#### 3.2 Add environment variables

```env
# .env.example — add Jira section
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here

JIRA_SERVER=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your_api_token_here
JIRA_PROJECT_ALLOWLIST=PROJ1,PROJ2,PROJ3
JIRA_TIMEOUT=30
JIRA_MAX_RESULTS=50
```

**Decision: API token auth (JIRA-002)**
- Simplest for read-only operations
- Least-privilege: read-only scopes
- No OAuth complexity needed for Phase 1

#### 3.3 Create Jira subpackage structure

```
wiki_cli/jira/
├── __init__.py          # Export JiraManager, models
├── client.py            # JiraClient — low-level API wrapper
├── manager.py           # JiraManager — business logic
├── models.py            # Pydantic models for Jira entities
├── auth.py              # Authentication handling
├── jql.py               # JQL safety controls
└── errors.py            # Jira-specific error types
```

### Phase 2: Core Implementation (Day 2–4)

#### 3.4 Jira models (`wiki_cli/jira/models.py`)

```python
from pydantic import BaseModel
from datetime import datetime

class JiraProject(BaseModel):
    key: str
    name: str
    description: str | None = None
    lead: str | None = None
    project_type: str | None = None

class JiraIssue(BaseModel):
    key: str
    summary: str
    description: str | None = None
    status: str
    priority: str
    issue_type: str
    labels: list[str] = []
    assignee: str | None = None
    reporter: str | None = None
    created: datetime
    updated: datetime

class JiraComment(BaseModel):
    id: str
    author: str
    body: str
    created: datetime
    updated: datetime | None = None

class JiraChangelogEntry(BaseModel):
    id: str
    author: str
    created: datetime
    field: str
    from_value: str | None = None
    to_value: str | None = None

class JiraTransition(BaseModel):
    id: str
    name: str
    to_status: str
```

#### 3.5 Jira client (`wiki_cli/jira/client.py`)

```python
import os
from jira import JIRA
from wiki_cli.exceptions import WikiJSError

class JiraClient:
    def __init__(self, server: str | None = None, email: str | None = None,
                 api_token: str | None = None, timeout: int = 30):
        self.server = server or os.getenv("JIRA_SERVER", "")
        self.email = email or os.getenv("JIRA_EMAIL", "")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", "")
        self.timeout = timeout

        if not all([self.server, self.email, self.api_token]):
            raise WikiJSError("Jira credentials not configured. Set JIRA_SERVER, JIRA_EMAIL, JIRA_API_TOKEN in .env")

        self._client = JIRA(server=self.server, basic_auth=(self.email, self.api_token))

    def test_connection(self) -> dict:
        """Verify connectivity and return server info."""
        myself = self._client.myself()
        return {"user": myself["displayName"], "email": myself["emailAddress"]}

    def list_projects(self) -> list[dict]:
        return [p.raw for p in self._client.projects()]

    def get_project(self, key: str) -> dict:
        return self._client.project(key).raw

    def search_issues(self, jql: str, max_results: int = 50) -> list[dict]:
        issues = self._client.search_issues(jql, maxResults=max_results)
        return [i.raw for i in issues]

    def get_issue(self, issue_key: str) -> dict:
        return self._client.issue(issue_key).raw

    def get_comments(self, issue_key: str) -> list[dict]:
        issue = self._client.issue(issue_key)
        return [c.raw for c in issue.fields.comment.comments]

    def get_changelog(self, issue_key: str) -> list[dict]:
        issue = self._client.issue(issue_key, expand="changelog")
        return [h.raw for h in issue.fields.changelog.histories]

    def get_transitions(self, issue_key: str) -> list[dict]:
        return self._client.transitions(issue_key)
```

#### 3.6 JQL safety controls (`wiki_cli/jira/jql.py`)

**Decision: Hybrid approach (JIRA-004) — template + validation**

```python
class JQLValidator:
    """Validate and sanitize JQL queries."""

    FORBIDDEN_KEYWORDS = {"DROP", "DELETE", "UPDATE", "INSERT", "EXEC", "EXECUTE"}
    FORBIDDEN_PATTERNS = ["UNION", "OR 1=1", "--", ";", "/*"]

    def validate(self, jql: str) -> str:
        """Validate JQL string, raise on injection attempts."""
        upper = jql.upper()
        for keyword in self.FORBIDDEN_KEYWORDS:
            if keyword in upper:
                raise ValueError(f"Forbidden keyword in JQL: {keyword}")
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in jql.lower():
                raise ValueError(f"Forbidden pattern in JQL: {pattern}")
        return jql

    def build_search_query(self, project: str = None, status: str = None,
                           assignee: str = None, priority: str = None,
                           issue_type: str = None) -> str:
        """Build JQL from safe template parameters."""
        parts = []
        if project:
            parts.append(f'project = "{project}"')
        if status:
            parts.append(f'status = "{status}"')
        if assignee:
            parts.append(f'assignee = "{assignee}"')
        if priority:
            parts.append(f'priority = "{priority}"')
        if issue_type:
            parts.append(f'issuetype = "{issue_type}"')
        return " AND ".join(parts) if parts else "order by created DESC"
```

#### 3.7 Jira manager (`wiki_cli/jira/manager.py`)

```python
from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.models import JiraProject, JiraIssue, JiraComment, JiraChangelogEntry, JiraTransition
from wiki_cli.jira.jql import JQLValidator

class JiraManager:
    def __init__(self, client: JiraClient, allowed_projects: list[str] | None = None):
        self.client = client
        self.allowed_projects = allowed_projects or []
        self.validator = JQLValidator()

    def test_connection(self) -> dict:
        return self.client.test_connection()

    def list_projects(self) -> list[JiraProject]:
        projects = self.client.list_projects()
        result = []
        for p in projects:
            proj = JiraProject(
                key=p["key"],
                name=p["name"],
                description=p.get("description"),
                lead=p.get("lead", {}).get("displayName") if p.get("lead") else None,
                project_type=p.get("projectTypeKey"),
            )
            if not self.allowed_projects or proj.key in self.allowed_projects:
                result.append(proj)
        return result

    def search_issues(self, jql: str = None, **filters) -> list[JiraIssue]:
        if jql is None:
            jql = self.validator.build_search_query(**filters)
        else:
            jql = self.validator.validate(jql)
        raw = self.client.search_issues(jql)
        return [self._parse_issue(i) for i in raw]

    def get_issue(self, issue_key: str) -> JiraIssue:
        raw = self.client.get_issue(issue_key)
        return self._parse_issue(raw)

    def get_comments(self, issue_key: str) -> list[JiraComment]:
        raw = self.client.get_comments(issue_key)
        return [JiraComment(
            id=str(c["id"]),
            author=c["author"]["displayName"],
            body=c["body"],
            created=c["created"],
            updated=c.get("updated"),
        ) for c in raw]

    def get_changelog(self, issue_key: str) -> list[JiraChangelogEntry]:
        raw = self.client.get_changelog(issue_key)
        entries = []
        for history in raw:
            for item in history.get("items", []):
                entries.append(JiraChangelogEntry(
                    id=str(history["id"]),
                    author=history["author"]["displayName"],
                    created=history["created"],
                    field=item["field"],
                    from_value=item.get("fromString"),
                    to_value=item.get("toString"),
                ))
        return entries

    def get_transitions(self, issue_key: str) -> list[JiraTransition]:
        raw = self.client.get_transitions(issue_key)
        return [JiraTransition(
            id=t["id"],
            name=t["name"],
            to_status=t["to"]["name"],
        ) for t in raw]

    def _parse_issue(self, raw: dict) -> JiraIssue:
        fields = raw.get("fields", {})
        return JiraIssue(
            key=raw["key"],
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            status=fields.get("status", {}).get("name", "Unknown"),
            priority=fields.get("priority", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
            labels=fields.get("labels", []),
            assignee=fields.get("assignee", {}).get("displayName") if fields.get("assignee") else None,
            reporter=fields.get("reporter", {}).get("displayName") if fields.get("reporter") else None,
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
        )
```

### Phase 3: CLI Integration (Day 4–5)

#### 3.8 Create CLI handlers (`wiki_cli/cli_jira.py`)

Follow exact pattern from `cli_pages.py`:

```python
from wiki_cli.jira.manager import JiraManager

def test_jira_connection(jira: JiraManager):
    result = jira.test_connection()
    print(f"Connected as: {result['user']} ({result['email']})")

def list_jira_projects(jira: JiraManager):
    projects = jira.list_projects()
    if not projects:
        print("No accessible projects.")
        return
    print(f"\n{'Key':<10} {'Name':<30} {'Type':<15}")
    print("-" * 55)
    for p in projects:
        print(f"{p.key:<10} {p.name:<30} {p.project_type or 'N/A':<15}")

def search_jira_issues(jira: JiraManager):
    print("Search options:")
    print("  1. By project")
    print("  2. By assignee")
    print("  3. By status")
    print("  4. Custom JQL")
    choice = input("Select: ").strip()
    # ... build search based on choice
    issues = jira.search_issues(...)
    # ... display results

def get_jira_issue(jira: JiraManager):
    key = input("Issue key (e.g., PROJ-123): ").strip()
    issue = jira.get_issue(key)
    # ... display issue details

def view_issue_comments(jira: JiraManager):
    key = input("Issue key: ").strip()
    comments = jira.get_comments(key)
    # ... display comments

def view_issue_changelog(jira: JiraManager):
    key = input("Issue key: ").strip()
    changelog = jira.get_changelog(key)
    # ... display changelog

def view_issue_transitions(jira: JiraManager):
    key = input("Issue key: ").strip()
    transitions = jira.get_transitions(key)
    # ... display available transitions
```

#### 3.9 Update main menu (`wiki_cli/cli_main.py`)

Add Jira section to the menu:

```python
MENU = """
========================================
       Wiki.js Manager
========================================
  --- Pages ---
  1. Create Page
  ...
  16. Test Connection

  --- Jira ---
  17. Jira: Test Connection
  18. Jira: List Projects
  19. Jira: Search Issues
  20. Jira: Get Issue Details
  21. Jira: View Issue Comments
  22. Jira: View Issue Changelog
  23. Jira: View Available Transitions

  --- AI ---
  24. AI Assistant
  0. Exit
========================================
"""
```

#### 3.10 Update exports (`wiki_cli/__init__.py`)

```python
from wiki_cli.jira.manager import JiraManager
from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.models import JiraProject, JiraIssue, JiraComment, JiraChangelogEntry, JiraTransition
```

### Phase 4: AI Integration (Day 5–6)

#### 3.11 Add Jira tools to AI (`wiki_cli/ai/tools.py`)

Append to `TOOLS` list:

```python
{
    "type": "function",
    "function": {
        "name": "jira_test_connection",
        "description": "Test Jira connection and return user info",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_list_projects",
        "description": "List accessible Jira projects",
        "parameters": {"type": "object", "properties": {}, "required": []}
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_search_issues",
        "description": "Search Jira issues using JQL or filters",
        "parameters": {
            "type": "object",
            "properties": {
                "jql": {"type": "string", "description": "Raw JQL query (optional)"},
                "project": {"type": "string", "description": "Project key filter"},
                "status": {"type": "string", "description": "Status filter"},
                "assignee": {"type": "string", "description": "Assignee filter"},
                "priority": {"type": "string", "description": "Priority filter"},
            },
            "required": []
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_get_issue",
        "description": "Get detailed information about a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key (e.g., PROJ-123)"}
            },
            "required": ["issue_key"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_get_comments",
        "description": "Get comments for a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key"}
            },
            "required": ["issue_key"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_get_changelog",
        "description": "Get changelog/history for a Jira issue",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key"}
            },
            "required": ["issue_key"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "jira_get_transitions",
        "description": "Get available transitions for a Jira issue (read-only)",
        "parameters": {
            "type": "object",
            "properties": {
                "issue_key": {"type": "string", "description": "Issue key"}
            },
            "required": ["issue_key"]
        }
    }
},
```

#### 3.12 Add Jira tool handlers (`wiki_cli/ai/agent.py`)

Add to `TOOL_LABELS` dict:

```python
"jira_test_connection": "Jira: Test Connection",
"jira_list_projects": "Jira: List Projects",
"jira_search_issues": "Jira: Search Issues",
"jira_get_issue": "Jira: Get Issue",
"jira_get_comments": "Jira: Get Comments",
"jira_get_changelog": "Jira: Get Changelog",
"jira_get_transitions": "Jira: Get Transitions",
```

Add to `_execute_tool` dispatch dict:

```python
"jira_test_connection": self._tool_jira_test_connection,
"jira_list_projects": self._tool_jira_list_projects,
"jira_search_issues": self._tool_jira_search_issues,
"jira_get_issue": self._tool_jira_get_issue,
"jira_get_comments": self._tool_jira_get_comments,
"jira_get_changelog": self._tool_jira_get_changelog,
"jira_get_transitions": self._tool_jira_get_transitions,
```

Add handler methods:

```python
def _tool_jira_test_connection(self) -> dict:
    return self.jira_manager.test_connection()

def _tool_jira_list_projects(self) -> dict:
    projects = self.jira_manager.list_projects()
    return [p.model_dump() for p in projects]

def _tool_jira_search_issues(self, jql: str = None, **filters) -> dict:
    issues = self.jira_manager.search_issues(jql=jql, **filters)
    return [i.model_dump() for i in issues]

def _tool_jira_get_issue(self, issue_key: str) -> dict:
    issue = self.jira_manager.get_issue(issue_key)
    return issue.model_dump()

def _tool_jira_get_comments(self, issue_key: str) -> dict:
    comments = self.jira_manager.get_comments(issue_key)
    return [c.model_dump() for c in comments]

def _tool_jira_get_changelog(self, issue_key: str) -> dict:
    changelog = self.jira_manager.get_changelog(issue_key)
    return [e.model_dump() for e in changelog]

def _tool_jira_get_transitions(self, issue_key: str) -> dict:
    transitions = self.jira_manager.get_transitions(issue_key)
    return [t.model_dump() for t in transitions]
```

Update `WikiAgent.__init__` to create JiraManager:

```python
def __init__(self, config: AIConfig | None = None):
    # ... existing Wiki.js setup ...
    try:
        from wiki_cli.jira.client import JiraClient
        from wiki_cli.jira.manager import JiraManager
        jira_client = JiraClient()
        self.jira_manager = JiraManager(jira_client)
    except Exception:
        self.jira_manager = None  # Jira not configured
```

### Phase 5: Testing (Day 6–8)

#### 3.13 Test structure

```
tests/
├── test_jira_connection.py         # Connection test
├── test_jira_projects.py           # Project listing
├── test_jira_search.py             # Issue search
├── test_jira_issue.py              # Issue retrieval
├── test_jira_comments.py           # Comment retrieval
├── test_jira_changelog.py          # Changelog retrieval
├── test_jira_transitions.py        # Transition inspection
├── test_jql_safety.py              # JQL injection prevention
├── jira_mocks/                     # Mock API responses
│   ├── projects.json
│   ├── issue.json
│   ├── search.json
│   ├── comments.json
│   ├── changelog.json
│   └── transitions.json
└── conftest.py                     # Add Jira fixtures
```

#### 3.14 Key test cases

| Category | Test | What it validates |
|----------|------|-------------------|
| Unit | JQL injection blocked | `'; DROP TABLE --` rejected |
| Unit | JQL template safe | `build_search_query()` produces valid JQL |
| Unit | Allowlist enforced | Non-allowed projects filtered out |
| Unit | Model validation | Invalid Jira data rejected by Pydantic |
| Unit | Connection missing creds | WikiJSError raised on missing config |
| Mocked | Successful search | Mock JIRA client returns parsed issues |
| Mocked | Auth failure | Mock raises authentication error |
| Mocked | Rate limit | Mock returns 429 status |
| Mocked | Timeout | Mock raises timeout exception |
| Mocked | Project not found | Mock raises NotFoundError |
| Security | Secret not in logs | Assert `JIRA_API_TOKEN` not in any log output |
| Security | Unauthorized project rejected | Project not in allowlist returns empty |
| Contract | Response schema | All responses match Pydantic models |
| Integration | Live connection | Connect to approved test instance |

### Phase 6: Documentation (Day 8–9)

#### 3.15 Documentation files

| File | Content |
|------|---------|
| `docs/jira-connector.md` | Architecture, modules, operations |
| `docs/jira-setup.md` | Installation, config, env vars |
| `docs/jira-operations.md` | All supported operations with examples |
| `docs/jql-safety.md` | JQL validation rules, injection prevention |
| `docs/jira-troubleshooting.md` | Common issues and fixes |
| Updated `README.md` | Add Jira section to features and usage |

### Phase 7: Review & Handoff (Day 9–10)

#### 3.16 Review checklist

- [ ] All 7 Jira operations work via CLI
- [ ] All 7 Jira operations work via AI assistant
- [ ] JQL injection attempts are blocked
- [ ] Unauthorized projects are rejected
- [ ] No credentials in logs
- [ ] Unit tests pass (>90% coverage)
- [ ] Documentation complete
- [ ] Live demonstration with test instance
- [ ] Naveed review completed

---

## 4. Architecture Decisions

| ID | Question | Decision | Rationale |
|----|----------|----------|-----------|
| JIRA-001 | Client library | `jira` Python library | Most maintained, handles pagination/auth/error mapping |
| JIRA-002 | Authentication | API token (basic auth) | Simplest for read-only, least-privilege |
| JIRA-003 | Cloud vs self-hosted | Cloud first, self-hosted later | Current requirement, `jira` library supports both |
| JIRA-004 | JQL safety | Hybrid (template + validation) | Flexible search + injection protection |
| JIRA-005 | Pagination | Jira native (`startAt`/`maxResults`) | Built into `jira` library |
| JIRA-006 | Identity mapping | Configurable lookup table | JSON file mapping Jira users to Lilac employees |

---

## 5. Files to Create

| File | Purpose |
|------|---------|
| `wiki_cli/jira/__init__.py` | Subpackage exports |
| `wiki_cli/jira/client.py` | JiraClient — REST API wrapper |
| `wiki_cli/jira/manager.py` | JiraManager — business logic |
| `wiki_cli/jira/models.py` | Pydantic models (Project, Issue, Comment, Changelog, Transition) |
| `wiki_cli/jira/jql.py` | JQL validation and safe query building |
| `wiki_cli/cli_jira.py` | CLI handlers for Jira operations |
| `docs/jira-connector.md` | Architecture documentation |
| `docs/jira-setup.md` | Setup and configuration guide |
| `docs/jira-operations.md` | Operations reference |
| `docs/jql-safety.md` | JQL security documentation |
| `docs/jira-troubleshooting.md` | Troubleshooting guide |
| `tests/test_jira_*.py` | Test files (7 modules) |
| `tests/jira_mocks/*.json` | Mock API responses (6 files) |

## 6. Files to Modify

| File | Change |
|------|--------|
| `pyproject.toml` | Add `jira` optional dependency group |
| `requirements.txt` | Add `jira>=3.5.0` |
| `.env.example` | Add Jira environment variables |
| `wiki_cli/__init__.py` | Add Jira exports |
| `wiki_cli/cli_main.py` | Add Jira menu section and handlers |
| `wiki_cli/ai/tools.py` | Add 7 Jira tool schemas |
| `wiki_cli/ai/agent.py` | Add Jira tool handlers and manager init |
| `tests/conftest.py` | Add Jira fixtures |
| `README.md` | Add Jira documentation section |

---

## 6. Security Controls

| Control | Implementation |
|---------|---------------|
| Least-privilege | Read-only API token, no write scopes |
| Credential storage | Environment variables only |
| Secret redaction | Filter `JIRA_API_TOKEN` from all log output |
| Project allowlist | Configurable, enforced in `JiraManager.list_projects()` |
| JQL injection | `JQLValidator` blocks forbidden keywords/patterns |
| TLS required | `jira` library uses HTTPS by default |
| No mutations | Only read operations implemented |

---

## 7. Error Handling

| Error Code | Condition | HTTP Status |
|------------|-----------|-------------|
| `AUTHENTICATION_FAILED` | Invalid credentials | 401 |
| `RATE_LIMITED` | Too many requests | 429 |
| `RESOURCE_NOT_FOUND` | Project/issue doesn't exist | 404 |
| `NETWORK_TIMEOUT` | Request timeout | 408 |
| `PROVIDER_ERROR` | Malformed response | 500 |
| `CONFIGURATION_ERROR` | Missing env vars | N/A |
| `VALIDATION_ERROR` | Invalid JQL | N/A |

---

## 8. Timeline

| Phase | Duration | Deliverables |
|-------|----------|-------------|
| Phase 1: Foundation | 2 days | Dependencies, env vars, subpackage structure |
| Phase 2: Core | 3 days | Models, client, manager, JQL safety |
| Phase 3: CLI | 2 days | CLI handlers, menu integration |
| Phase 4: AI | 2 days | Tool schemas, agent handlers |
| Phase 5: Testing | 3 days | Unit, mock, security, contract tests |
| Phase 6: Documentation | 2 days | All docs, README update |
| Phase 7: Review | 1 day | Demo, review, handoff |
| **Total** | **~15 days** | Complete read-only Jira connector |

---

## 9. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| JQL injection | Medium | High | Template + validation + audit |
| Breaking Wiki.js CLI | Low | High | Separate subpackage, no changes to existing logic |
| Credential leakage | Low | Critical | Env vars + redaction |
| Rate limiting | High | Medium | Proactive checking + graceful degradation |
| Missing test instance | Low | High | Secure before Phase 5 |

---

## 10. Acceptance Criteria Mapping

| Criterion | How It's Met |
|-----------|-------------|
| AC1: Discoverable in registry | Added to menu as section "Jira" |
| AC2: UNCONFIGURED when missing | `JiraClient.__init__` raises on missing env vars |
| AC3: AUTHENTICATION_FAILED | `jira` library raises on 401 |
| AC4: Health check with quota | `test_connection()` returns user + server info |
| AC5: Only approved projects | Allowlist enforced in `list_projects()` |
| AC6: Unauthorized project rejected | Filtered by allowlist |
| AC7: JQL validation | `JQLValidator.validate()` |
| AC8: Invalid JQL returns VALIDATION_ERROR | Caught before API call |
| AC9: Pagination | `jira` library handles `startAt`/`maxResults` |
| AC10: Timeout after 30s | Configurable `JIRA_TIMEOUT` |
| AC11: Rate limit handling | Check `Retry-After` header |
| AC12: Normalized results | Pydantic models with timestamps |
| AC13: No credentials in logs | Redaction filter |
| AC14: No mutations | Only read operations |
| AC15: Unit tests >90% | 7 test modules + mocks |
| AC16: Contract tests | Pydantic model validation |
| AC17: Integration test | Approved test instance |
| AC18: Documentation complete | 5 doc files + README update |
| AC19: Owner demonstration | Live demo with test instance |
| AC20: Reviewer approval | Naveed sign-off |
| AC21: DoD satisfied | All items checked |
