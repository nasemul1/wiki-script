# Graph Report - .  (2026-07-11)

## Corpus Check
- Corpus is ~4,734 words - fits in a single context window. You may not need a graph.

## Summary
- 106 nodes · 273 edges · 10 communities (8 shown, 2 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 12 edges (avg confidence: 0.62)
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- CLI Commands & Utilities
- Architecture & Dependencies
- Page History & Versioning
- Page CRUD Operations
- Pages Package Structure
- Error Handling & Recovery
- Client & System Setup
- Package Initialization
- GraphQL Execution
- Project Root

## God Nodes (most connected - your core abstractions)
1. `PagesManager` - 46 edges
2. `main()` - 21 edges
3. `WikiJSError` - 20 edges
4. `Page` - 20 edges
5. `Implementation Plan` - 16 edges
6. `WikiJSClient` - 13 edges
7. `PageResponse` - 11 edges
8. `input_with_default()` - 11 edges
9. `PageHistory` - 9 edges
10. `PageVersion` - 7 edges

## Surprising Connections (you probably didn't know these)
- `Export/Import` --conceptually_related_to--> `CRUD Operations`  [INFERRED]
  README.md → plan.md
- `README Documentation` --conceptually_related_to--> `Implementation Plan`  [INFERRED]
  README.md → plan.md
- `Implementation Plan` --references--> `python-dotenv`  [EXTRACTED]
  plan.md → requirements.txt
- `PageHistory Model` --uses--> `pydantic`  [EXTRACTED]
  plan.md → requirements.txt
- `PageResponse Model` --uses--> `pydantic`  [EXTRACTED]
  plan.md → requirements.txt

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Wiki-Script Core Architecture** — layered_architecture, wikiclient_class, pagesmanager_class, page_model, graphql_api [EXTRACTED 0.95]
- **External Dependencies** — gql_library, pydantic_library, dotenv_library, requirements_txt [EXTRACTED 1.00]
- **Page Operations** — crud_operations, history_revision, export_import, pagesmanager_class [INFERRED 0.85]

## Communities (10 total, 2 thin omitted)

### Community 0 - "CLI Commands & Utilities"
Cohesion: 0.27
Nodes (21): diff_two_revisions(), restore_revision(), view_specific_revision(), main(), browse_tree(), clone_page(), create_page(), delete_page() (+13 more)

### Community 1 - "Architecture & Dependencies"
Cohesion: 0.20
Nodes (21): CLI Interactive Menu, CRUD Operations, python-dotenv, Export/Import, gql[requests], GraphQL API, History/Revision Management, Layered Architecture Pattern (+13 more)

### Community 2 - "Page History & Versioning"
Cohesion: 0.18
Nodes (10): BaseModel, History-related menu handlers., view_page_history(), PageHistory, PageVersion, Data models for Wiki.js resources., Represents a single entry in a page's revision history., Represents a specific version/snapshot of a page. (+2 more)

### Community 3 - "Page CRUD Operations"
Cohesion: 0.26
Nodes (4): Page, PageResponse, Response wrapper from page mutations., Represents a Wiki.js page.

### Community 4 - "Pages Package Structure"
Cohesion: 0.25
Nodes (4): GraphQL queries and mutations for page history and versioning., Page operations for Wiki.js., PagesManager — handles all page operations against the Wiki.js GraphQL API., GraphQL queries and mutations for page CRUD operations.

### Community 5 - "Error Handling & Recovery"
Cohesion: 0.29
Nodes (3): Exception, Base exception for all Wiki.js API errors.      Attributes:         message: Hum, WikiJSError

### Community 6 - "Client & System Setup"
Cohesion: 0.33
Nodes (4): System-related menu handlers., test_connection(), Manages the gql client, authentication, and query execution for Wiki.js.      At, WikiJSClient

### Community 7 - "Package Initialization"
Cohesion: 0.40
Nodes (3): Core Wiki.js GraphQL client using the gql library., Custom exceptions for Wiki.js client operations., Wiki.js automation toolkit for managing pages via GraphQL.

## Knowledge Gaps
- **1 isolated node(s):** `wiki-script`
  These have ≤1 connection - possible missing edges or undocumented components.
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `PagesManager` connect `CLI Commands & Utilities` to `Page History & Versioning`, `Page CRUD Operations`, `Pages Package Structure`, `Error Handling & Recovery`, `Client & System Setup`, `Package Initialization`?**
  _High betweenness centrality (0.272) - this node is a cross-community bridge._
- **Why does `WikiJSError` connect `Error Handling & Recovery` to `CLI Commands & Utilities`, `Page History & Versioning`, `Page CRUD Operations`, `Pages Package Structure`, `Client & System Setup`, `Package Initialization`, `GraphQL Execution`?**
  _High betweenness centrality (0.110) - this node is a cross-community bridge._
- **Why does `Page` connect `Page CRUD Operations` to `CLI Commands & Utilities`, `Page History & Versioning`, `Pages Package Structure`, `Package Initialization`?**
  _High betweenness centrality (0.054) - this node is a cross-community bridge._
- **Are the 6 inferred relationships involving `PagesManager` (e.g. with `WikiJSClient` and `WikiJSError`) actually correct?**
  _`PagesManager` has 6 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `WikiJSError` (e.g. with `WikiJSClient` and `PagesManager`) actually correct?**
  _`WikiJSError` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `wiki-script`, `Wiki.js automation toolkit for managing pages via GraphQL.`, `Allow running as: python -m wiki_cli` to the rest of the system?**
  _22 weakly-connected nodes found - possible documentation gaps or missing edges._