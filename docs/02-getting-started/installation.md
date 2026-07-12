# Installation

## Requirements

- Python 3.10 or higher
- A running Wiki.js instance with GraphQL API enabled
- A Wiki.js API key

## Install from Source

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Install as a Package

```bash
pip install .
```

This creates two commands: `wiki-cli` and `wiki-ai`.

## Install with AI Support

The AI assistant requires additional dependencies:

```bash
pip install -e ".[ai]"
```

Or manually:

```bash
pip install openai>=1.0.0 httpx>=0.25.0
```

## Install for Development

```bash
pip install -e ".[ai,dev]"
```

This installs all dependencies including `pytest` and `pytest-cov`.

## Verify Installation

```bash
# Check the CLI is available
wiki-cli --help

# Check the AI assistant is available
wiki-ai --help

# Or run as a Python module
python -m wiki_cli
```

## Dependencies

### Core

| Package | Version | Purpose |
|---------|---------|---------|
| `gql[requests]` | >=4.0.0 | GraphQL client for Wiki.js API |
| `pydantic` | >=2.0.0 | Data models and validation |
| `python-dotenv` | >=1.0.0 | Load `.env` configuration files |

### AI (optional)

| Package | Version | Purpose |
|---------|---------|---------|
| `openai` | >=1.0.0 | OpenAI-compatible API client (works with all providers) |
| `httpx` | >=0.25.0 | HTTP client for fetching model lists |

### Development (optional)

| Package | Version | Purpose |
|---------|---------|---------|
| `pytest` | >=7.0.0 | Test framework |
| `pytest-cov` | >=4.0.0 | Coverage reporting |
