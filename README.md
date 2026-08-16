# wiki-script

Terminal-based Wiki.js manager. Manage pages, revisions, and content from the CLI — or use natural language with the AI assistant.

## Installation

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[ai]"
```

The `[ai]` extra installs `openai` and `httpx` for `wiki-ai`. Drop it for CLI-only use.

## First run

Launching `wiki-cli` for the first time prompts for a wiki profile (name, URL, API key). It's saved to `~/.config/wiki-cli/wikis.json` (mode `0600`) and used on every subsequent launch.

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

## Usage

### Interactive menu

Run `wiki-cli` and pick an option. Most options are page-level CRUD; `16` tests the connection, `17` manages wiki profiles, `18` opens the AI assistant, `0` exits.

### AI assistant

Run `wiki-ai` for natural-language control:

```text
  provider:  OpenRouter
  model:     meta-llama/llama-4-scout:free

  > list all pages
  > create a page at docs/getting-started with title "Getting Started"
  > what's the diff between revision 1 and 2 of page 7
```

The assistant has access to all page operations, history, search, and tree browsing.

### Manage wikis

From the main menu, option `17` opens a submenu for switching between saved wikis, adding new ones, listing them, and removing them.

### Switch wikis

Inside `wiki-ai`:

| Command | Action |
|---|---|
| `/switch-wiki` | Interactive picker over saved wikis |
| `/switch-wiki <name>` | Jump directly to a named profile |
| `/switch-wiki --new` | Force create a new profile |

After switching, the AI assistant rebuilds its wiki client and clears conversation history.

### Remove a wiki

```text
  > /remove-wiki work
  remove 'work' (https://wiki.work.com/graphql)? [y/n]: y
  removed → work
```

The command confirms before deleting. If the removed profile was active, the assistant prompts you to switch to another or add a new one.

## Reference

### Main menu

| Option | Action |
|---|---|
| 1 | Create a page |
| 2 | Fetch a page |
| 3 | Update a page |
| 4 | Delete a page |
| 5 | List pages |
| 6 | Search pages |
| 7 | Browse pages (tree) |
| 8 | Move/rename a page |
| 9 | Clone a page |
| 10 | Export a page to file |
| 11 | Import a page from file |
| 12 | View page history |
| 13 | View a specific revision |
| 14 | Diff two revisions |
| 15 | Restore a revision |
| 16 | Test connection |
| 17 | Manage Wikis (submenu: switch / add / list / remove) |
| 18 | AI Assistant |
| 0 | Exit |

### AI slash commands

| Command | Action |
|---|---|
| `/add-wiki` | Add a new wiki profile (auto-switches + clears history) |
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `exit` | Quit |
