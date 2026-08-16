# Manage Wikis Submenu + Remove Confirmation — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Main menu option 18 becomes a "Manage Wikis" submenu covering switch / add / list / remove. Add explicit confirmation before removing a wiki profile (both UIs). Fix the silent-success bug where `/remove-wiki <unknown>` reported success on a no-op.

## Decisions

- **Menu shape:** Submenu under option 18 (one entry owns all wiki management).
- **Confirm before delete:** Always confirm. Show name + URL. `y/n`.
- **Silent-success fix:** `/remove-wiki <unknown>` raises `WikiJSError` instead of silently succeeding.
- **Remove active profile:** Clear `active_wiki.txt`. If other profiles remain, auto-prompt to switch. If none, clear and prompt to add new on next menu entry.
- **Storage layer:** Unchanged. `remove_wiki()` stays as no-op-on-missing (idempotent storage primitive). Validation happens in the UI layer.

## Architecture

### New module: `wiki_cli/cli_wikis.py`

Pulls wiki-management UI out of `cli_main.py`. Single public function:

```python
def manage_wikis_menu() -> WikiJSClient:
    """Show Manage Wikis submenu. Returns a WikiJSClient (current or freshly built)."""
```

Submenu shape:

```
--- Manage Wikis ---
  1. Switch active wiki
  2. Add new wiki profile
  3. List saved wikis
  4. Remove a wiki profile
  0. Back to main menu
>
```

Behavior per option:

| Choice | Action | Returns |
|---|---|---|
| 1 | `switch_wiki_flow()` — interactive picker or new | rebuilt client |
| 2 | `switch_wiki_flow("--new")` | rebuilt client |
| 3 | `list_wikis()` + active marker — read-only | current client |
| 4 | `_remove_wiki_flow()` — picker + confirm | current client (or new if active removed) |
| 0 | Exit submenu | current client |

Option 4 disabled when `list_wikis()` empty.

### New function: `_remove_wiki_flow() -> WikiJSClient`

```python
def _remove_wiki_flow() -> WikiJSClient:
    """Picker → confirm → remove → handle active-cleared case."""
```

Flow:

```
saved wikis:
  1    work        https://w.work.com/graphql
  2    personal    https://w.home.io/graphql
  3    cancel
> 1

remove 'work' (https://w.work.com/graphql)? [y/n]: y
removed → work
```

Cases:

- **User picks "cancel":** print "cancelled", return current client.
- **User declines (`n`):** print "cancelled", return current client.
- **Profile removed, was not active:** print "removed → <name>", return current client.
- **Profile removed, was active:** clear `active_wiki.txt`. If other profiles remain, call `switch_wiki_flow()` (picker over remaining profiles, or new-profile flow if user picks "add new"). If no profiles remain, print "no saved wikis" and return current client (next switch attempt will prompt for new profile).

### Changes to `wiki_cli/cli_main.py`

- Rename menu entry: `18. Switch Wiki` → `18. Manage Wikis`.
- Handler:

```python
def _manage_wikis() -> None:
    nonlocal client, pages
    client = manage_wikis_menu()
    pages = PagesManager(client)
```

- Handler key: `"18": ("Manage Wikis", _manage_wikis)`.

### Changes to `wiki_cli/ai/cli.py`

Update `_cmd_remove_wiki`:

```python
def _cmd_remove_wiki(agent, arg):
    target = arg.strip() or get_active_wiki_name()
    if not target:
        print(f"  {Y}no wiki specified and no active wiki{R}\n")
        return

    entry = get_wiki(target)
    if not entry:
        print(f"  {Y}wiki '{target}' not found{R}\n")
        return

    confirm = input(f"  remove '{target}' ({entry['url']})? [y/n]: ").strip().lower()
    if confirm != "y":
        print(f"  {D}cancelled{R}\n")
        return

    remove_wiki(target)

    if get_active_wiki_name() == target:
        set_active_wiki(None)
        agent.wiki_client = None
        agent.pages = None
        # Rebuild via switch flow if other profiles remain.
        remaining = list_wikis()
        if remaining:
            new_client = switch_wiki_flow()
            agent.wiki_client = new_client
            agent.pages = PagesManager(new_client)
        else:
            print(f"  {Y}no saved wikis. /switch-wiki to add one.{R}\n")

    print(f"  {G}removed → {target}{R}\n")
```

Also updates help text to note confirm step.

### Validation rules

- Confirm input: accept `y`, `Y`, `yes` (case-insensitive) as confirm. Anything else cancels.
- Empty input cancels.

## Error handling

| Case | Behavior |
|---|---|
| Unknown profile name | Print error, no state change. |
| User cancels (`n`/empty) | Print "cancelled", no state change. |
| Removing active profile | Clear active + rebuild via switch flow if other profiles remain. |
| No remaining profiles after remove | Clear active. User must `/switch-wiki` or use menu 18 next time. |
| Submenu input invalid | Re-prompt like main menu does. |

## Testing

### `tests/test_wikis.py`

Existing 23 tests stay. Add:

- `test_remove_wiki_unknown_name_no_state_change` — verifies `remove_wiki(name)` stays no-op (unchanged behavior).
- `test_remove_wiki_removes_when_present` — verifies removal works.

These test the storage primitive (which keeps no-op-on-missing). The UI-layer confirmation logic is tested in `tests/cli_wikis/` and `tests/main_menu/`.

### `tests/cli_wikis/` (new)

Mirror existing `tests/main_menu/` structure. Test `manage_wikis_menu` and `_remove_wiki_flow`:

- `test_manage_wikis_menu_back_returns_current`
- `test_manage_wikis_menu_list_shows_active_marker`
- `test_manage_wikis_menu_remove_cancels_on_n`
- `test_manage_wikis_menu_remove_succeeds_on_y`
- `test_manage_wikis_menu_remove_active_rebuilds_via_switch`
- `test_manage_wikis_menu_remove_active_no_remaining_prompts_next`
- `test_remove_wiki_flow_unknown_name_no_change`
- `test_remove_wiki_flow_empty_picker`

### `tests/main_menu/success.py`

- Update `test_menu_switch_wiki_rebuilds` → rename `test_menu_manage_wikis_rebuilds`, target option 18, mock `manage_wikis_menu` instead of `switch_wiki_flow`.
- Update existing menu-exit/invalid/dispatch tests for new mocks (`manage_wikis_menu` instead of `switch_wiki_flow`).
- Add `test_menu_option_18_label` — verify "Manage Wikis" appears in menu output.

### `tests/test_ai_cli.py` (new)

Test `_cmd_remove_wiki` behavior:

- `test_ai_remove_wiki_unknown_name_no_change`
- `test_ai_remove_wiki_cancels_on_n`
- `test_ai_remove_wiki_succeeds_on_y`
- `test_ai_remove_wiki_default_target_is_active`

## Files touched

- **New:** `wiki_cli/cli_wikis.py`
- **New:** `tests/cli_wikis/__init__.py`
- **New:** `tests/cli_wikis/success.py`
- **New:** `tests/test_ai_cli.py`
- **Modify:** `wiki_cli/cli_main.py` — option 18 label + handler
- **Modify:** `wiki_cli/ai/cli.py` — `_cmd_remove_wiki` confirmation + unknown-name error
- **Modify:** `tests/conftest.py` — possibly add helper for `manage_wikis_menu` mocks
- **Modify:** `tests/main_menu/success.py` — update mocks for new label + add option 18 label test
- **Modify:** `README.md` — document new submenu + confirm step

## Out of scope (deferred)

- Inline edit (rename a profile)
- Export/import profile bundles
- Per-wiki AI provider config
- Bulk operations
- Keep active after removing all profiles (currently forces reconfigure)
