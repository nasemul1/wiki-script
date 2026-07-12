# E2E Test Plan — wiki-script CLI

## Overview

End-to-end tests for the wiki-script CLI using **pytest**. Each CLI feature is tested individually by simulating user input and verifying the full flow: **prompt → user input → business logic call → output**.

## Architecture

Since the CLI is interactive (`input()` driven, no argparse), tests use:

- **`unittest.mock.patch("wiki_cli.cli_pages.input")`** — to simulate user keystrokes
- **`unittest.mock.MagicMock(spec=PagesManager)`** — to mock the business logic layer
- **`pytest --capture`** (`capsys`) — to capture and verify printed output

Each test calls the handler function directly (e.g., `create_page(manager)`) rather than running the menu loop. This isolates each feature while still testing the full handler flow.

## Test Structure

```
tests/
├── conftest.py              # Shared fixtures: mock manager, sample models, input helper
├── test_create_page.py      # Feature 1:  Create Page
├── test_fetch_page.py       # Feature 2:  Fetch Page
├── test_update_page.py      # Feature 3:  Update Page
├── test_delete_page.py      # Feature 4:  Delete Page
├── test_list_pages.py       # Feature 5:  List Pages
├── test_search_pages.py     # Feature 6:  Search Pages
├── test_browse_tree.py      # Feature 7:  Browse Pages (tree)
├── test_move_rename.py      # Feature 8:  Move/Rename Page
├── test_clone_page.py       # Feature 9:  Clone Page
├── test_export_page.py      # Feature 10: Export Page to File
├── test_import_page.py      # Feature 11: Import Page from File
├── test_view_history.py     # Feature 12: View Page History
├── test_view_revision.py    # Feature 13: View Specific Revision
├── test_diff_revisions.py   # Feature 14: Diff Two Revisions
├── test_restore_revision.py # Feature 15: Restore Revision
├── test_connection.py       # Feature 16: Test Connection
└── test_main_menu.py        # Menu loop dispatch, exit, invalid option, error handling
```

## Shared Fixtures (`conftest.py`)

| Fixture | Purpose |
|---------|---------|
| `mock_manager` | `MagicMock(spec=PagesManager)` — mocked business logic layer |
| `sample_page` | Returns a `Page` model with sensible defaults (id=1, path="docs/intro", title="Intro", content="# Hello", tags=["wiki"]) |
| `sample_page_response` | Returns a `PageResponse(succeeded=True, message="OK", page=<sample_page>)` |
| `sample_pages` | Returns a list of 3 `Page` objects with different paths for list/search tests |
| `input_mock` | Helper: patches `wiki_cli.cli_pages.input` with a given list of strings |

### Example `conftest.py`

```python
from unittest.mock import MagicMock, patch
import pytest
from wiki_cli.models import Page, PageResponse
from wiki_cli.pages import PagesManager


@pytest.fixture
def mock_manager():
    return MagicMock(spec=PagesManager)


@pytest.fixture
def sample_page():
    return Page(
        id=1,
        path="docs/intro",
        title="Introduction",
        content="# Welcome\nThis is the intro page.",
        description="A brief introduction",
        locale="en",
        isPublished=True,
        isPrivate=False,
        tags=["wiki", "docs"],
    )


@pytest.fixture
def sample_page_response(sample_page):
    return PageResponse(
        succeeded=True,
        message="Page created successfully",
        page=sample_page,
    )


@pytest.fixture
def sample_pages():
    return [
        Page(id=1, path="docs/intro", title="Introduction", tags=["wiki"]),
        Page(id=2, path="docs/setup", title="Setup Guide", tags=["wiki", "setup"]),
        Page(id=3, path="projects/app", title="App Overview", tags=["project"]),
    ]


@pytest.fixture
def mock_input():
    """Returns a helper that patches input() with a list of values."""

    def _helper(values):
        return patch("wiki_cli.cli_pages.input", side_effect=iter(values))

    return _helper
```

## Feature-by-Feature Test Cases

---

### Feature 1: Create Page (`test_create_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_create_page_success` | `["test/path", "Test Title", "Hello world", "", "", "en", "n", "y"]` | `manager.create()` called with correct `Page` model; output contains "Created page (id=1)" |
| `test_create_page_with_all_fields` | `["proj/alpha", "Alpha", "Content", "A desc", "tag1,tag2", "en", "y", "y"]` | Tags parsed as `["tag1", "tag2"]`, description set, isPrivate=True, isPublished=True |
| `test_create_page_path_required` | `["", "Title", "content", "", "", "en", "n", "y"]` | Prints "Path is required."; `manager.create()` NOT called |
| `test_create_page_title_required` | `["test/path", "", "content", "", "", "en", "n", "y"]` | Prints "Title is required."; `manager.create()` NOT called |
| `test_create_page_defaults` | `["test/path", "Title", "content", "", "", "", "", ""]` | Empty inputs use defaults: desc="", tags=[], locale="en", private=False, published=True |

---

### Feature 2: Fetch Page (`test_fetch_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_fetch_by_id` | `["1", "1"]` | `manager.get_by_id(1)` called; output contains page path, title, content |
| `test_fetch_by_path` | `["2", "docs/intro", "en"]` | `manager.get_by_path("docs/intro", locale="en")` called |
| `test_fetch_default_choice` | `["", "1"]` | Empty choice defaults to "1" (by ID) |
| `test_fetch_invalid_id` | `["1", "abc"]` | Prints "Invalid ID."; `manager.get_by_id()` NOT called |
| `test_fetch_path_required` | `["2", ""]` | Prints "Path is required."; `manager.get_by_path()` NOT called |

---

### Feature 3: Update Page (`test_update_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_update_replace_content` | `["1", "New Title", "New desc", "1", "New content", "tag1", "y"]` | Content choice "1" replaces content; `manager.update()` called with updated page |
| `test_update_append_content` | `["1", "", "", "2", " appended", "", ""]` | Content choice "2" appends text to existing content |
| `test_update_keep_content` | `["1", "", "", "3", "", "", ""]` | Content choice "3" keeps existing content unchanged |
| `test_update_invalid_id` | `["abc"]` | Prints "Invalid ID."; no manager calls |
| `test_update_with_new_tags` | `["1", "", "", "3", "new1, new2", "", ""]` | Tags updated to `["new1", "new2"]` |

---

### Feature 4: Delete Page (`test_delete_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_delete_success` | `["1", "yes"]` | `manager.delete(1)` called; prints "Deleted page 1." |
| `test_delete_cancelled` | `["1", "no"]` | `manager.delete()` NOT called; prints "Cancelled." |
| `test_delete_invalid_id` | `["abc"]` | Prints "Invalid ID."; no manager calls |

---

### Feature 5: List Pages (`test_list_pages.py`)

| Test | Input Sequence | Mock Return | Verifies |
|------|---------------|-------------|----------|
| `test_list_success` | `["1", "", "q"]` | 3 pages | Prints page table; output contains "Total: 3 page(s)" |
| `test_list_empty` | `["1", ""]` | `[]` | Prints "No pages found." |
| `test_list_filter_tag` | `["1", "setup", "q"]` | 3 pages | Only pages with "setup" tag shown |
| `test_list_filter_no_match` | `["1", "nonexistent", ""]` | 3 pages | Prints "No pages found with tag 'nonexistent'." |
| `test_list_sort_path` | `["2", "", "q"]` | 3 pages | `manager.list_all(order_by="PATH")` called |
| `test_list_pagination` | `["1", "", "", "q"]` | 25 pages | Shows pagination prompt; "next page" works |

---

### Feature 6: Search Pages (`test_search_pages.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_search_success` | `["intro", "", ""]` | `manager.search("intro")` called; results table printed |
| `test_search_empty_query` | `["", ""]` | Prints "Query is required."; `manager.search()` NOT called |
| `test_search_no_results` | `["xyz", "", ""]` | `manager.search()` returns `[]`; prints "No pages found." |
| `test_search_with_locale` | `["intro", "en", ""]` | `manager.search("intro", locale="en")` called |
| `test_search_with_tag_filter` | `["intro", "", "wiki", ""]` | Results filtered to pages containing "wiki" tag |

---

### Feature 7: Browse Tree (`test_browse_tree.py`)

| Test | Input Sequence | Mock Return | Verifies |
|------|---------------|-------------|----------|
| `test_browse_tree_structure` | `[""]` | 3 pages with nested paths | Tree printed with connectors (`├──`, `└──`); root `/` shown |
| `test_browse_empty` | `[]` | `[]` | Prints "No pages found." |
| `test_browse_view_page` | `["1"]` | 1 page + `get_by_id(1)` returns page | Tree printed; then page details shown |
| `test_browse_skip_view` | `[""]` | 1 page | Tree printed; empty input skips page view |

---

### Feature 8: Move/Rename (`test_move_rename.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_move_success` | `["1", "new/path", "New Title", "yes"]` | `manager.update()` called with new path and title |
| `test_move_no_changes` | `["1", "", "", ""]` | Prints "No changes made."; `manager.update()` NOT called |
| `test_move_cancelled` | `["1", "new/path", "", "no"]` | Prints "Cancelled."; `manager.update()` NOT called |
| `test_move_invalid_id` | `["abc"]` | Prints "Invalid ID." |

---

### Feature 9: Clone (`test_clone_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_clone_success` | `["1", "docs/copy", "Copy Title"]` | `manager.clone_page(1, "docs/copy", "Copy Title")` called; prints clone ID |
| `test_clone_empty_path` | `["1", "", ""]` | Prints "Path is required."; `manager.clone_page()` NOT called |
| `test_clone_invalid_id` | `["abc"]` | Prints "Invalid ID." |

---

### Feature 10: Export (`test_export_page.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_export_success` | `["1", ""]` | File written with YAML frontmatter + Markdown content; prints export confirmation |
| `test_export_custom_filename` | `["1", "my_export.md"]` | File written to "my_export.md" |
| `test_export_invalid_id` | `["abc"]` | Prints "Invalid ID." |

---

### Feature 11: Import (`test_import_page.py`)

| Test | Setup | Input Sequence | Verifies |
|------|-------|---------------|----------|
| `test_import_with_frontmatter` | Create temp `.md` file with `---\npath: ...\ntitle: ...\n---\ncontent` | `[""]` (file path only) | `manager.create()` called with extracted metadata |
| `test_import_without_frontmatter` | Create temp `.md` file with plain content | `["", "import/path", "Import Title"]` | `manager.create()` called with prompted path/title |
| `test_import_file_not_found` | — | `["nonexistent.md"]` | Prints "File not found." |
| `test_import_empty_filename` | — | `[""]` | Prints "Filename is required." |

---

### Feature 12: View Page History (`test_view_history.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_view_history_success` | `["1"]` | `manager.get_history(1)` called; history table printed |
| `test_view_history_empty` | `["1"]` | `manager.get_history()` returns `([], 0)`; prints "No history found." |
| `test_view_history_invalid_id` | `["abc"]` | Prints "Invalid ID." |

---

### Feature 13: View Specific Revision (`test_view_revision.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_view_revision_success` | `["1", "5"]` | `manager.get_version(1, 5)` called; version content printed |
| `test_view_revision_invalid_id` | `["abc", "5"]` | Prints "Invalid ID." |
| `test_view_revision_invalid_version` | `["1", "abc"]` | Prints "Invalid version ID." |

---

### Feature 14: Diff Two Revisions (`test_diff_revisions.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_diff_success` | `["1", "3", "5"]` | `manager.get_version()` called twice; diff output printed |
| `test_diff_invalid_id` | `["abc", "3", "5"]` | Prints "Invalid ID." |

---

### Feature 15: Restore Revision (`test_restore_revision.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_restore_success` | `["1", "5", "yes"]` | `manager.restore_version(1, 5)` called; prints success |
| `test_restore_cancelled` | `["1", "5", "no"]` | Prints "Cancelled."; `manager.restore_version()` NOT called |
| `test_restore_invalid_id` | `["abc"]` | Prints "Invalid ID." |

---

### Feature 16: Test Connection (`test_connection.py`)

| Test | Mock Return | Verifies |
|------|-------------|----------|
| `test_connection_success` | List of pages (non-empty) | Prints connection success; shows most recent page |
| `test_connection_no_pages` | `[]` | Prints "Connected but no pages found." |

---

### Menu Loop (`test_main_menu.py`)

| Test | Input Sequence | Verifies |
|------|---------------|----------|
| `test_menu_exit` | `["0"]` | Prints "Goodbye!"; loop exits |
| `test_menu_invalid_option` | `["99", "0"]` | Prints "Invalid option."; then exits |
| `test_menu_dispatches_handler` | `["1", "", ""]` | Dispatches to `create_page` handler (handler called) |
| `test_menu_handles_error` | `["16", "0"]` | Handler raises `WikiJSError` → error printed → continues |
| `test_menu_press_enter_to_continue` | `["16", "", "0"]` | "Press Enter to continue..." prompt shown after handler |

---

## Implementation Order

| Phase | Files | Description |
|-------|-------|-------------|
| 1 | `conftest.py`, `pyproject.toml` | Setup shared fixtures, add pytest dependency |
| 2 | `test_create_page.py` | First feature — validates the test pattern works |
| 3 | `test_fetch_page.py`, `test_search_pages.py` | Read-only features |
| 4 | `test_update_page.py`, `test_delete_page.py` | Write/delete features |
| 5 | `test_list_pages.py`, `test_browse_tree.py` | List features with pagination/tree |
| 6 | `test_move_rename.py`, `test_clone_page.py` | Move/clone features |
| 7 | `test_export_page.py`, `test_import_page.py` | File I/O features |
| 8 | `test_view_history.py`, `test_view_revision.py`, `test_diff_revisions.py`, `test_restore_revision.py` | History features |
| 9 | `test_connection.py`, `test_main_menu.py` | System + menu loop |

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run a specific feature
pytest tests/test_create_page.py -v

# Run with output capture disabled (see prints)
pytest tests/ -v -s

# Run with coverage
pytest tests/ --cov=wiki_cli --cov-report=term-missing
```

## Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
]
```
