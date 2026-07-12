# Changelog

All notable changes to wiki-script.

## [0.1.0] - 2025-01-15

### Added

- **CLI Menu** — 17-option interactive menu for all wiki operations
- **Page CRUD** — Create, fetch, update, delete pages
- **Page Organization** — List, search, browse tree, move/rename, clone
- **File I/O** — Export pages to Markdown with frontmatter, import from files
- **Revision History** — View history, view revisions, diff, restore
- **Connection Test** — Verify API connectivity from the menu
- **AI Assistant** — Natural language interface with 16 tool functions
- **Multi-Provider AI** — OpenAI, OpenRouter, Groq, Mistral, Ollama, Ollama Cloud
- **Credential Storage** — Secure local storage of API keys with 0600 permissions
- **Model Discovery** — Live model listing from provider APIs
- **Conversation History** — AI remembers context across messages
- **Activity Logging** — Real-time display of AI tool calls and results
- **Multi-Line Editor** — Open $EDITOR for writing content via /edit command
- **Slash Commands** — /help, /clear, /edit, /providers, /models, /remove-key
- **Persistent Config** — Last-used provider and model saved locally
- **Pydantic Models** — Type-safe data structures for all resources
- **GraphQL Client** — Authenticated transport with retry logic
- **67 Tests** — Comprehensive test suite with mock-based testing
- **Python Library API** — Import and use programmatically

### Technical

- Python 3.10+ required
- Built with `gql`, `pydantic`, `python-dotenv`
- AI uses `openai` SDK (compatible with all providers)
- ANSI terminal output (no external UI dependencies)
- Lazy imports for AI module (keeps startup fast)
