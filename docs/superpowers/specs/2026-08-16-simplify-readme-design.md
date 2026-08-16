# Simplified README — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Rewrite `README.md` as a ~150-line first-time-user manual. Cover install + first run + 5 common workflows + 2 reference tables. Drop the "As a Library" section, project structure tree, and testing instructions.

## Decisions

- **Audience:** First-time user landing on the repo. Quickstart path → deeper sections.
- **Length:** ~150 lines (down from 380).
- **Install:** `pip + venv` only (drop `uv` path).
- **Workflows:** All 5 main user paths included: interactive menu, AI assistant, manage wikis, switching wikis, removing wikis.
- **Library section:** Dropped.
- **Project structure / testing:** Dropped from README.

## Architecture

### Document outline (~150 lines)

```
# wiki-script                          (1)
                                      (blank, 1)
Terminal-based Wiki.js manager.        (1)
Manage pages, revisions, and content   (1)
from the CLI — or use natural language (1)
with the AI assistant.                (1)
                                      (blank, 1)
## Installation                        (1)
```bash                                (1)
git clone ...                         (1)
cd wiki-script                        (1)
python3 -m venv .venv                 (1)
source .venv/bin/activate             (1)
pip install -e ".[ai]"                (1)
```                                   (1)
                                      (blank, 1)
## First run                          (1)
[Sample first-launch transcript]      (~10)
                                      (blank, 1)
## Usage                              (1)
### Interactive menu                  (1)
[3-line description + sample]        (~6)
                                      (blank, 1)
### AI assistant                      (1)
[3-line description + sample]        (~6)
                                      (blank, 1)
### Manage wikis                      (1)
[3-line description + sample]        (~6)
                                      (blank, 1)
### Switch wikis                      (1)
[3-line description + sample]        (~6)
                                      (blank, 1)
### Remove a wiki                     (1)
[3-line description + sample]        (~6)
                                      (blank, 1)
## Reference                          (1)
### Main menu                         (1)
[Option table]                       (~22 — 17 rows)
                                      (blank, 1)
### AI slash commands                 (1)
[Command table]                      (~10 — 6-8 rows)
```

Approx total: 1 + 1 + 4 + 1 + 1 + 7 + 1 + 1 + 11 + 1 + 1 + 7 + 1 + 1 + 7 + 1 + 1 + 7 + 1 + 1 + 7 + 1 + 1 + 23 + 1 + 1 + 11 = ~115 lines + blank lines = ~150.

### Section details

#### Installation

```bash
git clone https://github.com/Imranslab/wiki-script.git
cd wiki-script
python3 -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e ".[ai]"
```

Optional `[ai]` extras install `openai` + `httpx` for `wiki-ai`. Drop for CLI-only use.

#### First run (sample transcript)

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

User sees this and knows: clone → install → run → answer prompts → menu appears.

#### Usage workflows (each ~6-8 lines)

1. **Interactive menu** — `wiki-cli`, options 1-17. Brief description + 1-line example (`1` for create, `5` for list).
2. **AI assistant** — `wiki-ai`, natural language. Sample prompt + response.
3. **Manage wikis** — main menu option `17` opens submenu (switch / add / list / remove). Single-line per option.
4. **Switch wikis** — `/switch-wiki` (interactive picker), `/switch-wiki <name>` (jump), `/switch-wiki --new` (force create new profile).
5. **Remove a wiki** — `/remove-wiki <name>` from AI assistant, or main menu `17 → 4`. Both ask to confirm.

#### Reference tables

**Main menu** (one row per option, 17 rows):

| Option | Action |
|---|---|
| 1 | Create a page |
| 2 | Fetch a page |
| ... | ... |
| 16 | Test connection |
| 17 | Manage Wikis (submenu: switch / add / list / remove) |
| 18 | AI Assistant |
| 0 | Exit |

**AI slash commands**:

| Command | Action |
|---|---|
| `/add-wiki` | Add a new wiki profile (auto-switches + clears history) |
| `/switch-wiki` | Switch active wiki (interactive / `<name>` / `--new`) |
| `/wikis` | List saved wiki profiles |
| `/remove-wiki` | Remove a wiki profile (asks to confirm) |
| `/clear` | Clear conversation history |
| `/help` | Show available commands |
| `exit` | Quit |

## Removed sections (deprecated content)

| Removed | Reason |
|---|---|
| `As a Library` code samples | CLI-only audience; library use is edge case. Re-add if requested. |
| `Project Structure` directory tree | Visible in repo itself; adds noise. |
| `Features` mega-table | Collapsed into workflow sections + reference tables. |
| `Testing` instructions | `pytest tests/`. Move to CONTRIBUTING.md if project grows. |
| `Dependencies` list | Visible in `pyproject.toml` / `requirements.txt`. |

## Out of scope (deferred)

- CONTRIBUTING.md (only if project grows beyond solo dev)
- Architecture diagrams
- Per-command deep reference (each command has its own `--help` and `/help`)
- Screenshots / GIFs
- Multi-language translations
