# wiki-script

A terminal-based Wiki.js manager with two ways to drive it: an interactive numbered menu for direct control, and an AI assistant (`wiki-ai`) that understands plain English. Manage pages, revisions, search, history, exports, and multiple Wiki.js instances — all from your shell.

## What it does

- **Pages** — create, fetch, update, delete, list, search, browse tree, move/rename, clone, export to file, import from file.
- **History** — view page history, inspect any revision, diff two revisions, restore a previous revision.
- **System** — test the connection, switch between multiple Wiki.js instances.
- **AI** — natural-language control over everything above, powered by OpenAI-compatible providers (OpenRouter, Groq, OpenAI, Mistral, Ollama).

## Prerequisites

- **Python 3.10 or newer.** Check with `python3 --version`.
- **A Wiki.js instance** with a GraphQL endpoint and an API key. In Wiki.js admin: *GraphQL API → API Access → Create API Key*. The endpoint URL is usually `https://your-wiki.example.com/graphql`.
- **An internet connection** to your Wiki.js server (the CLI talks to it over HTTPS).
- An **LLM provider API key** (only required if you want to use `wiki-ai`). OpenRouter has a free tier that's the easiest to start with.

## Installation

### macOS / Linux

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[ai]"
```

### Windows (PowerShell)

```powershell
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[ai]"
```

The `[ai]` extra pulls in `openai` and `httpx` for the AI assistant. Drop it (`pip install -e .`) if you only want the CLI.

Verify the install:

```bash
wiki-cli --help      # main menu entry point
wiki-ai --help       # AI assistant entry point
```

If you get `command not found`, your virtual environment isn't active. Run `source .venv/bin/activate` again.

## First run

The first time you launch `wiki-cli`, it has no saved wiki profile to connect to, so it prompts you for one:

```text
$ wiki-cli
No active wiki configured.
  no saved wikis
  name: main
  url: https://your-wiki.example.com/graphql
  api key: ********

  saved → active: main

========================================
       Wiki.js Manager
========================================
  --- Pages ---
  1. Create Page
  ...
```

Three prompts:

| Prompt | What to enter |
|---|---|
| `name` | A short label you'll use to refer to this wiki. No spaces. Example: `work`, `personal`, `docs-prod`. |
| `url` | The full GraphQL endpoint URL. Must start with `http://` or `https://`. Example: `https://wiki.example.com/graphql`. |
| `api key` | The API key from your Wiki.js admin panel. |

These are saved to `~/.config/wiki-cli/wikis.json` with file permissions `0600` (owner read/write only). The selected profile is recorded in `~/.config/wiki-cli/active_wiki.txt`.

You can launch `wiki-ai` the same way — it also bootstraps a wiki profile on first run, then prompts you to pick an LLM provider.

## Configuration

Everything lives under `~/.config/wiki-cli/`:

```
~/.config/wiki-cli/
├── wikis.json         # all saved profiles (mode 0600)
└── active_wiki.txt    # name of the currently active profile (mode 0600)
```

There's also `credentials.json` in the same directory, used by `wiki-ai` to store LLM provider API keys (also `0600`).

To back up or migrate your config, copy that whole directory.

## Usage — Interactive menu

`wiki-cli` shows a numbered menu. Type the number and press Enter.

### Annotated walkthrough

```text
$ wiki-cli
... (banner + menu) ...
Select an option: 5
--- List Pages ---

 1. Getting Started         (id=3)
 2. API Reference           (id=7)
 3. Architecture Overview   (id=12)

Press Enter to continue...
Select an option: 2
--- Fetch Page ---

Enter page ID or path: 3
Title:    Getting Started
Path:     docs/getting-started
Author:   admin
Tags:     docs, intro
...

Press Enter to continue...
Select an option: 0
Goodbye!
```

### What each option does

| Option | Action |
|---|---|
| 1 | Create a page (path, title, content, optional description/tags) |
| 2 | Fetch a page by ID or path |
| 3 | Update a page (title, content, description, tags, publish state) |
| 4 | Delete a page (asks for confirmation) |
| 5 | List all pages |
| 6 | Search pages by full-text query |
| 7 | Browse pages as a tree |
| 8 | Move or rename a page |
| 9 | Clone a page to a new path |
| 10 | Export a page to a Markdown file with YAML frontmatter |
| 11 | Import a page from a Markdown file |
| 12 | View page history (paginated revisions) |
| 13 | View a specific revision |
| 14 | Diff two revisions side by side |
| 15 | Restore a page to a previous revision |
| 16 | Test the GraphQL connection (lists a few pages, shows reachable) |
| 17 | Manage Wikis — submenu for switching, adding, listing, removing wiki profiles |
| 18 | Open the AI assistant |
| 0 | Exit |

## Usage — AI assistant

`wiki-ai` launches a natural-language REPL. Type any sentence; the assistant picks tools and executes.

### Annotated walkthrough

```text
$ wiki-ai
  wiki-ai  Wiki.js AI Assistant
  type /help for commands

  no saved wikis. let's configure one.
  ...
  (wiki profile + LLM provider setup) ...

  provider:  OpenRouter
  model:     meta-llama/llama-4-scout:free

  > list all pages
  ▸ Listing pages
  ✓ 12 pages found

  > create a page at docs/onboarding with title "Team Onboarding"
  ▸ Creating page
  ✓ page created (id=47)

  > /clear
  history cleared

  > exit
```

### Slash commands

| Command | Action |
|---|---|
| `/add-wiki` | Add a new wiki profile. Prompts for name/URL/api-key, saves it, switches to it, clears conversation history. |
| `/switch-wiki` | Interactive picker over saved wikis. |
| `/switch-wiki <name>` | Jump directly to a named profile. |
| `/switch-wiki --new` | Force the "add new profile" flow. |
| `/wikis` | List all saved wiki profiles with the active one marked. |
| `/remove-wiki [name]` | Remove a profile (asks to confirm). Defaults to the active profile. |
| `/clear` | Clear conversation history. |
| `/help` | Show available commands. |
| `exit` | Quit the AI assistant. |

### LLM providers

The AI assistant works with any OpenAI-compatible API. On first run you pick a provider and enter an API key:

| Provider | Notes |
|---|---|
| OpenRouter | Recommended. Free tier available. Hundreds of models. |
| Groq | Fast inference. Good for Llama / Mixtral. |
| OpenAI | GPT-4o, GPT-4, etc. |
| Mistral | Mistral models. |
| Ollama (Local) | Run models on your machine. |
| Ollama Cloud (Remote) | Remote Ollama instances. |

API keys are saved to `~/.config/wiki-cli/credentials.json` (mode `0600`).

## Multi-wiki management

You can store any number of Wiki.js profiles (work, personal, staging, prod — whatever) and switch between them without re-entering credentials.

### Add a wiki

From `wiki-ai`:

```text
> /add-wiki
name: staging
url: https://wiki.staging.example.com/graphql
api key: ********
saved → active: staging (history cleared)
```

From the main menu, select `17` (Manage Wikis) → `2` (Add new wiki profile).

### Switch wikis

| Where | How |
|---|---|
| `wiki-ai` | `/switch-wiki` (picker), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force new) |
| Main menu | `17` (Manage Wikis) → `1` (Switch active wiki) |

After switching from the AI assistant, conversation history is cleared and the new wiki becomes the default for all subsequent tool calls.

### List wikis

| Where | How |
|---|---|
| `wiki-ai` | `/wikis` |
| Main menu | `17` → `3` (List saved wikis) |

### Remove a wiki

| Where | How |
|---|---|
| `wiki-ai` | `/remove-wiki <name>` — asks to confirm |
| Main menu | `17` → `4` (Remove a wiki profile) — asks to confirm |

If you remove the active profile, the AI assistant prompts you to switch to another profile or add a new one. The main menu prints a hint and the next switch attempt will trigger the new-profile flow.

## Common recipes

### Create a page (CLI)

Select `1` from the main menu. You'll be prompted for path, title, content, optional description/tags. Markdown content is supported.

### Create a page (AI)

```text
> create a page at docs/onboarding with title "Team Onboarding" — include a welcome section and a checklist
```

### Find a page by path

CLI option `2`, type the path. Example: `docs/getting-started`.

### Search across all pages

CLI option `6`, type a query. Example: `authentication`.

### Update a page's content

CLI option `3`, type the page ID. You'll be shown current title/content; type `y` to edit, then enter new values.

### Clone a page to a new path

CLI option `9`, type source ID and new path. Useful for templating — clone then update.

### Export a page to a Markdown file

CLI option `10`, type the page ID and a filename. Output is Markdown with YAML frontmatter (title, path, tags, etc.).

### Import a page from a Markdown file

CLI option `11`, type the filename and a target path. The frontmatter is parsed and used; the body becomes the page content.

### Restore a page to a previous revision

CLI option `12` to view history, note the revision ID, then option `15` to restore.

## Troubleshooting

### `command not found: wiki-cli`

Your virtual environment isn't active. Run `source .venv/bin/activate` (macOS/Linux) or `.\.venv\Scripts\Activate.ps1` (Windows). Your shell prompt should show `(.venv)`.

### "No active wiki configured."

You haven't saved a wiki profile yet. Run `/switch-wiki --new` (in `wiki-ai`) or option `17` → `2` (in `wiki-cli`) to add one.

### Stuck at the API key prompt / can't paste

The prompt reads via plain `input()` so paste works in any terminal. If your terminal isn't accepting paste, check for a bracketed-paste-mode setting or a custom input handler.

### GraphQL 404 / connection failed

Your URL is probably wrong. Wiki.js GraphQL endpoints are typically at `/graphql`. If your wiki is at `https://wiki.example.com`, the GraphQL URL is `https://wiki.example.com/graphql` — not just the bare host.

### "401 Unauthorized" / "403 Forbidden"

Your API key is wrong, or it doesn't have permission for the operation. Check the key in Wiki.js admin (*GraphQL API → API Access*) and make sure it's not expired or scoped.

### "Cannot import name X" after updating

A new version of `wiki-script` may have changed the API. Reinstall:

```bash
cd wiki-script
git pull
source .venv/bin/activate
pip install -e ".[ai]" --upgrade
```

### Switching wikis didn't change my data

The AI assistant clears conversation history after a switch. If you switched from the main menu but `wiki-ai` still shows old data, exit and restart `wiki-ai` so it picks up the new active profile.

## Where data lives

```
~/.config/wiki-cli/
├── wikis.json         # wiki profiles (mode 0600)
├── active_wiki.txt    # name of currently active wiki (mode 0600)
└── credentials.json   # LLM provider API keys (mode 0600)
```

Backup = copy the directory. Migrate to another machine = copy + paste.

## Development

Tests:

```bash
source .venv/bin/activate
pytest tests/ -v
```

The project uses `pytest` + `pytest-cov`. Each feature has a dedicated test file under `tests/` with a `success.py` and `validation.py` companion for happy-path and error-path coverage.

## Contributing

Issues and pull requests are welcome on the [GitHub repo](https://github.com/Imranslab/wiki-script). For non-trivial changes, open an issue first to discuss the approach.

## License

MIT. See `pyproject.toml` for details.
