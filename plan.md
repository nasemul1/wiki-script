# Wiki-Script Terminal Manager — Implementation Plan

## Context

This document is the single source of truth for the wiki-script project. Any AI agent
working on this project MUST read this file first to understand the current state, known
bugs, planned features, and implementation rules.

---

## 1. Project Overview

**Goal:** Build a full-featured terminal-based Wiki.js manager. Users should be able to
manage pages, assets, and revisions entirely from the CLI — like a Linux file manager
but for a Wiki.js instance.

**Tech stack:**
- Python 3.10+
- `gql[requests]` for GraphQL
- `pydantic` v2 for data models
- `python-dotenv` for env config
- `requests` for REST uploads (asset upload endpoint)

**Wiki.js version:** 2.x (GraphQL API at `/graphql`, REST upload at `/u`)

---

## 2. Current Project Structure

```
wiki-script/
├── main.py                        # Interactive terminal menu (entry point)
├── scripts/                       # Standalone CLI scripts
│   ├── create_page.py
│   ├── fetch_page.py
│   ├── update_page.py
│   ├── delete_page.py
│   └── upload_asset.py
├── wiki_script/                   # Core library (importable)
│   ├── __init__.py                # Exports: WikiJSClient, WikiJSError, Page, Asset, PageResponse, PagesManager, AssetsManager
│   ├── exceptions.py              # WikiJSError(message, errors)
│   ├── models.py                  # Page, PageResponse, Asset (Pydantic BaseModel)
│   ├── wiki_client.py             # WikiJSClient — gql transport, execute()
│   └── operations/
│       ├── __init__.py            # Exports: PagesManager, AssetsManager
│       ├── pages.py               # PagesManager — CRUD + list
│       └── assets.py              # AssetsManager — upload only
├── .env                           # WIKIJS_URL, WIKIJS_API_KEY
├── .env.example
├── requirements.txt               # gql[requests], python-dotenv, pydantic, requests
├── README.md
└── plan.md                        # THIS FILE
```

---

## 3. Current Features in main.py

| # | Feature | Status |
|---|---------|--------|
| 1 | Create Page | Working |
| 2 | Fetch Page (by ID or path) | **BROKEN** — see Bug #1 |
| 3 | Update Page | Working |
| 4 | Delete Page | Working |
| 5 | Upload Asset | Working |
| 6 | List All Pages | Working |
| 0 | Exit | Working |

---

## 4. Known Bugs (Must Fix First)

### Bug #1: Fetch by path parser key mismatch (CRITICAL)
- **File:** `wiki_script/operations/pages.py`
- **Query:** `_GET_PAGE_BY_PATH` uses `singleByPath(path: $path, locale: $locale)`
- **Problem:** `_parse_single_page()` looks for `result["pages"]["single"]` but the
  response key is `"singleByPath"`
- **Fix:** Change `_parse_single_page` to accept a custom key, or add a separate
  `_parse_single_by_path` that reads `result["pages"]["singleByPath"]`

### Bug #2: argparse `type=bool` is broken
- **File:** `scripts/update_page.py` line 28
- **Problem:** `parser.add_argument("--published", type=bool, ...)` — `bool("False")`
  returns `True`. Any non-empty string is truthy.
- **Fix:** Use `action="store_true"` / `action="store_false"` or a custom type function

### Bug #3: Unused import in create_page.py
- **File:** `scripts/create_page.py` line 15
- **Problem:** `AssetsManager` is imported but never used
- **Fix:** Remove the import

### Bug #4: fetch_page.py ID=0 treated as falsy
- **File:** `scripts/fetch_page.py` line 32
- **Problem:** `if args.id:` is `False` when `--id 0` is passed
- **Fix:** Use `if args.id is not None:`

### Bug #5: Upload response not parsed
- **File:** `wiki_script/operations/assets.py` line 90
- **Problem:** `upload()` returns `Asset(filename=..., folder=...)` but never parses
  the response JSON to get `id`, `mime`, `fileSize`
- **Fix:** Parse `response.json()` and populate all Asset fields

### Bug #6: Hardcoded MIME type
- **File:** `wiki_script/operations/assets.py` line 69
- **Problem:** Always sends `"application/octet-stream"` regardless of actual file type
- **Fix:** Use `mimetypes.guess_type()` to detect the MIME type

---

## 5. GraphQL API Reference (Wiki.js 2.x)

### Queries Available

```graphql
# List all pages (returns [String] tags, NOT objects)
query { pages { list(orderBy: TITLE|PATH|CREATED|UPDATED) { id path title description isPublished isPrivate locale tags } } }

# Fetch single page by ID (returns [PageTag] tags with subfields)
query { pages { single(id: $id) { id path title description content editor isPublished isPrivate locale tags { tag } } } }

# Fetch single page by path (returns [PageTag] tags with subfields) — requires admin
query { pages { singleByPath(path: $path, locale: $locale) { id path title description content editor isPublished isPrivate locale tags { tag } } } }

# Search pages
query { pages { search(query: $query, locale: $locale) { results { id path title description locale } suggestions totalHits } } }

# Page history / revisions
query { pages { history(id: $id, limit: $limit, offset: $offset) { id pageId createdAt authorId { email } title description } } }

# Fetch specific revision
query { pages { revision(id: $revisionId) { id content title description createdAt tags { tag } } } }
```

### Mutations Available

```graphql
# Create page
mutation { pages { create(path: $path, title: $title, content: $content, description: $desc, editor: "markdown", isPrivate: $priv, isPublished: $pub, locale: $locale, tags: $tags) { responseResult { succeeded message } page { id path title } } } }

# Update page
mutation { pages { update(id: $id, content: $content, description: $desc, editor: "markdown", isPrivate: $priv, isPublished: $pub, tags: $tags, title: $title) { responseResult { succeeded message } page { id path title } } } }

# Delete page
mutation { pages { delete(id: $id) { responseResult { succeeded message } } } }
```

### Important Notes on Tags
- `pages.list` returns `tags` as `[String]` — plain strings, no subfields
- `pages.single` and `pages.singleByPath` return `tags` as `[PageTag]` — needs `{ tag }` subfield selection
- `pages.search` returns `tags` as `[String]`

### Asset REST Endpoint
- Upload: `POST /u` with multipart form data, field `mediaUpload` for file + metadata JSON
- No GraphQL mutations for assets — must use REST

---

## 6. Features to Implement

### Phase 1: Core Fixes + Search + Pagination + Tree View

#### 1.1 Fix all bugs listed in Section 4

#### 1.2 Search Pages
- Add `_SEARCH_PAGES` query to `pages.py`
- Add `search(query, locale)` method to `PagesManager`
- Add `search_pages()` handler to `main.py`
- Menu option: search by keyword, filter by tag, filter by locale
- Display results in a table (ID, path, title, description)
- Limit results with pagination for large result sets

#### 1.3 Pagination for List
- Modify `list_all()` to accept `limit` and `offset` params
- Add interactive pagination in `main.py` — show N pages at a time, press Enter for next
- Display "Showing X-Y of Z total" header

#### 1.4 Tree View (Browse Pages)
- Use `pages.list` to get all pages, then build a tree from paths
- Display as indented tree:
  ```
  / (root)
  ├── projects/
  │   ├── alpha/
  │   │   ├── overview (id=15)
  │   │   └── setup (id=16)
  │   └── beta/
  │       └── readme (id=17)
  └── docs/
      ├── getting-started (id=20)
      └── api (id=21)
  ```
- Allow selecting a page from the tree to view/edit/delete it
- For 1000+ pages, lazy-load or filter as user types

### Phase 2: Asset Management

#### 2.1 List Assets
- Research Wiki.js asset listing API (likely GraphQL `assets { list }`)
- Add `_LIST_ASSETS` query to `assets.py`
- Add `list_all(folder_id)` method to `AssetsManager`
- Display in table: ID, filename, folder, MIME type, size

#### 2.2 Download Asset
- Research Wiki.js asset download endpoint (likely REST `/u/{id}`)
- Add `download(asset_id, save_path)` method
- Stream download for large files

#### 2.3 Delete Asset
- Research Wiki.js asset delete mutation
- Add `delete(asset_id)` method with confirmation prompt

#### 2.4 Asset Folder Management
- Research folder listing/creation API
- Add list/create/delete folder operations

### Phase 3: Page History

#### 3.1 View Revision History
- Add `_PAGE_HISTORY` query
- Add `get_history(page_id, limit, offset)` method to `PagesManager`
- Display: revision ID, date, author, title change summary

#### 3.2 View Specific Revision
- Add `_GET_REVISION` query
- Add `get_revision(revision_id)` method
- Display full page content at that revision

#### 3.3 Diff Between Revisions
- Fetch two revisions, compute diff
- Use Python `difflib` for unified diff output
- Color-code additions/deletions in terminal

#### 3.4 Restore Revision
- Fetch old revision content
- Update page with that content via `pages.update`
- Add confirmation prompt

### Phase 4: Quality of Life

#### 4.1 Move/Rename Page
- Use `pages.update` to change the path field
- Confirm with user showing old → new path

#### 4.2 Clone Page
- Fetch source page, create new with modified path/title
- Prompt for new path

#### 4.3 Export to File
- Fetch page content, write to local `.md` file
- Support exporting multiple pages

#### 4.4 Import from File
- Read local `.md` file
- Create page with content from file
- Prompt for path, title, tags

#### 4.5 Tag Filtering
- Add `--tags` filter to list and search
- Use GraphQL `list` with local filtering if API doesn't support server-side tag filter

### Phase 5: Packaging & Polish

#### 5.1 Add pyproject.toml
- Define `[project]` metadata
- Add `[project.scripts]` entry point: `wiki-cli = "main:main"`
- Make it installable with `pip install .`

#### 5.2 Update README
- Fix script paths (scripts/ directory)
- Document all new features
- Add usage examples for each feature

#### 5.3 Add Connection Test
- Menu option to test API connection
- Print server version, user info, page count

---

## 7. Implementation Rules

### Code Style
- Follow existing code conventions (see current files for reference)
- Use type hints everywhere (Python 3.10+ `X | Y` syntax)
- Use Pydantic for all data models
- Handle errors with `WikiJSError`, print to stderr, exit code 1
- No comments unless user asks for them
- Keep functions focused and short

### File Organization
- GraphQL queries go in `wiki_script/operations/` as module-level constants
- New operations modules go in `wiki_script/operations/` (e.g., `history.py`)
- Menu handlers go in `main.py` as standalone functions
- Shared UI helpers (table printing, pagination) go in a new `wiki_script/ui.py`

### Main Menu Pattern
Each feature follows this pattern in main.py:
```python
def feature_name(pages: PagesManager) -> None:
    # 1. Collect input from user
    # 2. Call pages.method() or assets.method()
    # 3. Print result
    # 4. Handle WikiJSError

# In handlers dict:
"7": ("Feature Name", lambda: feature_name(pages)),
```

### Testing Approach
- No formal test framework yet — verify manually with `python main.py`
- After implementing a feature, run `python -c "import ast; ast.parse(open('file.py').read())"` to check syntax
- Test each feature against a real Wiki.js instance

---

## 8. Current Menu (main.py)

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

  --- Assets ---
  16. Upload Asset
  17. List Assets
  18. Download Asset
  19. Delete Asset
  20. List Folders
  21. Create Folder

  --- System ---
  22. Test Connection
  0. Exit
=========================================
```

## 9. Target Menu (after all phases)

```
=========================================
       Wiki.js Manager
=========================================
  --- Pages ---
  1.  Create Page
  2.  Fetch Page (by ID/path)
  3.  Update Page
  4.  Delete Page
  5.  List Pages (paginated)
  6.  Search Pages
  7.  Browse Pages (tree view)
  8.  Page History
  9.  Move/Rename Page
  10. Clone Page
  11. Export Page to File
  12. Import Page from File

  --- Assets ---
  13. Upload Asset
  14. List Assets
  15. Download Asset
  16. Delete Asset
  17. Manage Asset Folders

  --- System ---
  18. Test Connection
  0.  Exit
=========================================
```

---

## 10. Environment Variables

```env
WIKIJS_URL=https://your-wiki-instance.com/graphql
WIKIJS_API_KEY=your_api_key_here
```

Both are loaded from `.env` via `python-dotenv`. The `WikiJSClient` raises `WikiJSError`
if either is missing.

---

## 11. Dependencies

```
gql[requests]>=4.0.0
python-dotenv>=1.0.0
pydantic>=2.0.0
requests>=2.28.0
```

No new dependencies needed for planned features (difflib is stdlib, mimetypes is stdlib).

---

## 12. Implementation Order

```
Phase 1:  Fix bugs → Search → Pagination → Tree View
Phase 2:  List Assets → Download Asset → Delete Asset → Folder Management
Phase 3:  View History → View Revision → Diff → Restore
Phase 4:  Move/Rename → Clone → Export → Import → Tag Filter
Phase 5:  pyproject.toml → Update README → Connection Test
```

Each phase should be completed and verified before moving to the next.
