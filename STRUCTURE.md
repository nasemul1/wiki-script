# Project Structure

```
wiki-script/
├── .env.example                          # Environment variable template
├── pyproject.toml                        # Build config, dependencies, entry points
├── requirements.txt                      # Flat dependency list
├── README.md                             # Project documentation
├── AI_INTEGRATION.md                     # AI assistant documentation
├── TEST_PLAN.md                          # Test plan document
├── plan.md                               # Project plan
│
├── wiki_cli/                             # Main package
│   ├── __init__.py                       # Package exports, version
│   ├── __main__.py                       # python -m entry point
│   ├── client.py                         # GraphQL transport (gql + requests)
│   ├── models.py                         # Pydantic data models
│   ├── exceptions.py                     # WikiJSError
│   ├── utils.py                          # CLI helpers, table formatters
│   ├── cli_main.py                       # Main menu loop (17 options)
│   ├── cli_pages.py                      # Page CLI handlers (11 operations)
│   ├── cli_history.py                    # History CLI handlers (4 operations)
│   ├── cli_system.py                     # System CLI handler
│   │
│   ├── pages/                            # Business logic layer
│   │   ├── __init__.py                   # Re-exports PagesManager
│   │   ├── manager.py                    # PagesManager class
│   │   ├── queries.py                    # GraphQL CRUD queries/mutations
│   │   └── history.py                    # GraphQL history queries/mutations
│   │
│   └── ai/                               # AI assistant
│       ├── __init__.py                   # AI package exports
│       ├── config.py                     # Provider config, credential storage
│       ├── agent.py                      # WikiAgent (tool-calling loop)
│       ├── tools.py                      # 16 OpenAI function schemas
│       └── cli.py                        # AI chat UI, slash commands
│
├── tests/                                # Test suite (67 tests)
│   ├── __init__.py
│   ├── conftest.py                       # Shared fixtures (mock_manager, sample data)
│   │
│   ├── test_create_page.py               # Create Page tests
│   ├── create_page/
│   │   ├── __init__.py
│   │   ├── success.py                    # Happy path tests
│   │   ├── validation.py                 # Error handling tests
│   │   └── defaults.py                   # Default value tests
│   │
│   ├── test_fetch_page.py                # Fetch Page tests
│   ├── fetch_page/
│   │   ├── __init__.py
│   │   ├── success.py
│   │   └── validation.py
│   │
│   ├── test_update_page.py               # Update Page tests
│   ├── update_page/
│   │   ├── __init__.py
│   │   ├── success.py
│   │   └── validation.py
│   │
│   ├── test_delete_page.py               # Delete Page tests
│   ├── delete_page/
│   │   ├── __init__.py
│   │   ├── success.py
│   │   └── validation.py
│   │
│   ├── test_list_pages.py                # List Pages tests
│   ├── list_pages/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_search_pages.py              # Search Pages tests
│   ├── search_pages/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_browse_tree.py               # Browse Tree tests
│   ├── browse_tree/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_move_rename.py               # Move/Rename tests
│   ├── move_rename/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_clone_page.py                # Clone Page tests
│   ├── clone_page/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_export_page.py               # Export Page tests
│   ├── export_page/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_import_page.py               # Import Page tests
│   ├── import_page/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_view_history.py              # View History tests
│   ├── view_history/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_view_revision.py             # View Revision tests
│   ├── view_revision/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_diff_revisions.py            # Diff Revisions tests
│   ├── diff_revisions/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_restore_revision.py          # Restore Revision tests
│   ├── restore_revision/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_connection.py                # Connection Test tests
│   ├── connection/
│   │   ├── __init__.py
│   │   └── success.py
│   │
│   ├── test_main_menu.py                 # Main Menu tests
│   └── main_menu/
│       ├── __init__.py
│       └── success.py
│
└── docs/                                 # Documentation
    ├── 01-introduction/
    │   ├── overview.md
    │   ├── features.md
    │   └── use-cases.md
    ├── 02-getting-started/
    │   ├── installation.md
    │   ├── configuration.md
    │   ├── authentication.md
    │   └── quickstart.md
    ├── 03-guides/
    │   ├── basic-usage.md
    │   ├── ai-prompts.md
    │   ├── page-management.md
    │   └── best-practices.md
    ├── 04-commands/
    │   ├── reference.md
    │   └── examples.md
    ├── 05-advanced/
    │   ├── custom-prompts.md
    │   ├── integrations.md
    │   └── automation.md
    ├── 06-faq/
    │   └── troubleshooting.md
    └── 07-resources/
        ├── changelog.md
        └── contributing.md
```

## File Counts

| Directory | Files | Purpose |
|-----------|-------|---------|
| `wiki_cli/` | 14 | Main package source code |
| `wiki_cli/pages/` | 4 | Business logic and GraphQL queries |
| `wiki_cli/ai/` | 5 | AI assistant (agent, tools, config, UI) |
| `tests/` | 35 | Test files and implementations |
| `docs/` | 19 | Documentation |
| Root | 6 | Config, README, dependencies |
| **Total** | **83** | |
