# Simplified README Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rewrite `README.md` as a ~150-line first-time-user manual covering install, first run, 5 common workflows, and 2 reference tables.

**Architecture:** Single-file rewrite. No code changes. Spec outlines the exact section structure, sample content, and reference table rows. Implementer transcribes per spec, verifies line count + section headers + reference accuracy.

**Tech Stack:** Markdown only. No scripts or test framework needed — verification is structural (line count + section presence + content sanity).

## Global Constraints

- Target length: ~150 lines (hard cap at 200).
- Install path: `pip + venv` only — drop `uv` path.
- Audience: first-time user landing on the repo.
- Workflows (5 sections): Interactive menu, AI assistant, Manage wikis, Switch wikis, Remove a wiki.
- Reference tables: Main menu (options 1-17, 0) + AI slash commands.
- Dropped sections: `As a Library`, `Project Structure`, `Features` mega-table, `Testing`, `Dependencies`.
- One commit with message `docs: simplify README to first-time-user manual (~150 lines)`.
- Option numbering in reference table must match current state: `17 = Manage Wikis`, `18 = AI Assistant` (swapped in commit `91fa2ef`).

---

## Task 1: Rewrite README.md

**Files:**
- Modify: `README.md` (full rewrite, replace 387 lines with ~150)

- [ ] **Step 1.1: Verify current README length + record baseline**

Run: `cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && wc -l README.md`
Expected: 387 lines (current baseline). Record this in the report.

- [ ] **Step 1.2: Read the spec for exact structure**

Read: `/home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script/docs/superpowers/specs/2026-08-16-simplify-readme-design.md`

The spec defines the document outline (section headers, target line counts per section, what content goes in each). The reference tables must include the exact slash command and option numbers from the spec.

- [ ] **Step 1.3: Verify current CLI state for accurate samples**

Before writing, confirm the current menu numbering by reading:
```
cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && grep -n "^  [0-9]\+\." wiki_cli/cli_main.py | head -20
```

Expected output (verified during spec self-review): options 1-16, then `17. Manage Wikis`, `18. AI Assistant`, `0. Exit`.

If grep output differs, STOP and report — the reference table is wrong.

Also confirm slash commands by reading `wiki_cli/ai/cli.py` `_cmd_help` body (around line 320-336). The reference table's slash command rows must match the current help output.

- [ ] **Step 1.4: Write the new README.md**

Replace the entire content of `/home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script/README.md` with the following content. Use `write` tool (file is being overwritten completely):

```markdown
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
```

(Note: the triple-backtick fence markers in this plan document use a leading backslash to escape; in the actual README.md they must be written as bare ` ``` ` fences.)

- [ ] **Step 1.5: Verify line count**

Run: `cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && wc -l README.md`
Expected: between 130 and 170 lines (target ~150, hard cap 200).

If over 200, trim. Common culprits: redundant blank lines, overly long table cells.

- [ ] **Step 1.6: Verify all required sections present**

Run:
```
cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && grep -n "^#" README.md
```
Expected headers (in order):
- `# wiki-script`
- `## Installation`
- `## First run`
- `## Usage`
- `### Interactive menu`
- `### AI assistant`
- `### Manage wikis`
- `### Switch wikis`
- `### Remove a wiki`
- `## Reference`
- `### Main menu`
- `### AI slash commands`

If any header missing or out of order, fix.

- [ ] **Step 1.7: Verify removed sections are gone**

Run:
```
cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && grep -in "as a library\|project structure\|pytest\|feature\b\|dependencies" README.md
```
Expected: no matches for `As a Library`, `Project Structure`, `pytest`, `Features` (as a section header), `Dependencies`.

If matches appear, remove those sections.

- [ ] **Step 1.8: Verify option numbering matches current state**

Run:
```
cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && grep -n "Manage Wikis\|AI Assistant" README.md
```
Expected: `Manage Wikis` mentioned as option `17`, `AI Assistant` mentioned as option `18`.

If reversed or wrong number, fix.

- [ ] **Step 1.9: Run full test suite (sanity check — no code changes expected)**

Run: `cd /home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script && uv run pytest tests/ --tb=short -q 2>&1 | tail -5`
Expected: 109 passed (no regressions — README change shouldn't affect tests).

- [ ] **Step 1.10: Commit**

```bash
git add README.md
git commit -m "docs: simplify README to first-time-user manual (~150 lines)"
```

- [ ] **Step 1.11: Write report**

Report file: `/home/nasemul/Documents/SWE/Web Development/Imranslab/wiki-script/.superpowers/sdd/2026-08-16-simplify-readme/task-1-report.md`

Include:
- Baseline line count (from Step 1.1)
- Final line count (from Step 1.5)
- Section header check result (from Step 1.6)
- Removed-section check result (from Step 1.7)
- Option numbering check result (from Step 1.8)
- Test suite result (from Step 1.9)
- Files changed
- Self-review findings
- Any issues or concerns

Reply with ONLY (under 15 lines):
- **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
- Commits created (short SHA + subject)
- One-line summary (e.g., "380 → 152 lines, all checks passed")
- Your concerns, if any
- The report file path

---

## Self-Review

**Spec coverage:**
- Target length ~150 → Task 1 Steps 1.5 (verify), 1.4 (write)
- Install path pip+venv → Task 1 Step 1.4 content
- First run transcript → Task 1 Step 1.4 content
- 5 workflow sections → Task 1 Step 1.4 content + Step 1.6 verification
- Reference tables (menu + slash commands) → Task 1 Step 1.4 content + Step 1.8 verification
- Removed sections absent → Task 1 Step 1.7 verification

**Placeholder scan:** No TBDs. Exact README content provided in Step 1.4.

**Type consistency:** No types involved (markdown only). Reference table option numbers must match current state — Step 1.3 verifies baseline before writing, Step 1.8 verifies after.
