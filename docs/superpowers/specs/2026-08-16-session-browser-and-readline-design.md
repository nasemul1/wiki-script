# Session Browser + ANSI Readline — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Add a `/sessions` slash command that lists all saved wiki sessions, and a `/use [name]` slash command that hot-swaps the current session. Make the slash command picker interactive — arrow keys + Enter to select. Replace plain `input()` calls in the most-used interactive flows with an arrow-key-capable readline so users can navigate typed input with Left/Right/Up/Down.

## Decisions

- **Readline approach:** Lightweight ANSI readline (~150 LOC, zero deps). POSIX-only (`termios` + `tty`). Falls back to plain `input()` on non-TTY (Windows, piped tests).
- **Picker design:** Standalone function `_pick_session()` rendering in alternate screen buffer with cursor positioning.
- **Switch semantics:** Hot-swap current session — saves outgoing, sets `agent.wiki_name`, loads incoming.
- **Exposure:** AI assistant slash commands only (`/sessions`, `/use`, `/use <name>`).
- **Readline scope:** Only `wiki_cli/ai/cli.py` and `wiki_cli/wikis.py` interactive flows get the new readline. Other modules' `input()` calls stay as-is for v1.

## Architecture

### New module: `wiki_cli/ai/readline.py`

```python
def input_with_history(prompt: str, *, history: list[str] | None = None) -> str
```

Single function, drop-in replacement for `input()`. Handles:
- ANSI escape sequences for arrow keys (Up/Down history, Left/Right cursor move, Home/End, Delete).
- Backspace (BS = `\x7f` or `\x08`) — cursor-aware delete.
- Ctrl-C (raises `KeyboardInterrupt`) / Ctrl-D (EOF).
- Echoes input as user types; redraws on cursor movement.
- Plain ASCII mode fallback when `not sys.stdin.isatty()`.

Fallback rule: if stdin isn't a TTY, delegate to plain `input()`. This keeps tests simple — they patch `builtins.input` or `input_with_history` interchangeably.

### `wiki_cli/ai/sessions.py` — add `list_sessions()`

```python
def list_sessions() -> list[dict[str, Any]]
    """Return all saved sessions across all wikis."""
```

Returns list of dicts:
```python
{"wiki": str, "message_count": int, "updated_at": str, "created_at": str}
```

Skips corrupt files silently. Returns `[]` when `SESSIONS_DIR` does not exist.

### `wiki_cli/ai/cli.py` — new commands + picker

#### `_cmd_sessions(agent)`

Lists all saved sessions with marker on currently loaded:

```python
for s in list_sessions():
    marker = f" {G}*{R}" if s["wiki"] == agent.wiki_name else "  "
    rel = _format_relative(s["updated_at"])
    print(f"  {marker} {B}{s['wiki']:<16}{R} {s['message_count']:>4} msgs, last: {rel}")
```

#### `_pick_session(current_wiki: str | None) -> str | None`

Interactive picker. Uses ANSI escape sequences to render in the alternate screen buffer (`\x1b[?1049h` enter / `\x1b[?1049l` exit). Up/Down moves selection highlight. Enter returns selected. Esc / Ctrl-C returns `None`.

Implementation sketch (real impl in code, not in spec):
- Capture terminal raw mode via `tty.setraw`.
- Read keys in a loop:
  - `\x1b[A` / `\x1b[B` → up/down selection
  - `\r` / `\n` → enter
  - `\x1b` → escape (cancel)
  - `\x03` → Ctrl-C (cancel)
- Re-render list with `▶` marker on selected row.
- Restore terminal + screen on exit (try/finally).

#### Dispatch additions

```python
if prompt == "/sessions":
    _cmd_sessions(agent)
    continue

if prompt == "/use":
    picked = _pick_session(agent.wiki_name)
    if picked:
        _swap_session(agent, picked)
    elif picked is None:
        # user cancelled picker — no message
        pass
    continue

if prompt.startswith("/use "):
    target = prompt[len("/use "):].strip()
    if not target:
        picked = _pick_session(agent.wiki_name)
        if picked:
            _swap_session(agent, picked)
    elif has_session(target):
        _swap_session(agent, target)
    else:
        print(f"  {Y}session '{target}' not found{R}\n")
    continue
```

#### `_swap_session(agent, target_wiki: str)` helper

Same save-outgoing / load-incoming pattern as the existing switch/add handlers (Task 3 of session-memory plan):

```python
def _swap_session(agent, target_wiki):
    if agent.wiki_name and agent.wiki_name != target_wiki:
        try:
            save_session(agent.wiki_name, agent.messages)
        except Exception:
            pass
    agent.wiki_name = target_wiki
    session = load_session(target_wiki)
    if session:
        agent.messages = session["messages"]
        agent._warned_at_80pct = False
        print(f"  {G}switched → {target_wiki} ({len(session['messages'])} messages){R}\n")
    else:
        agent.clear_history()
        print(f"  {D}started fresh for {target_wiki}{R}\n")
```

### Readline swap in `wiki_cli/ai/cli.py`

Replace plain `input(prompt)` calls in the user-facing REPL loop with `input_with_history(prompt)`. Specifically the `prompt = input(...)` line at the REPL `while True:` head, and key editor choices in `_cmd_providers` / `_pick_provider` for arrow-key picker.

### Readline swap in `wiki_cli/wikis.py`

Replace `input()` calls in `_prompt_new_profile()` (name, url, api_key) with `input_with_history()`. These are the highest-traffic interactive prompts.

## Error handling

| Case | Behavior |
|---|---|
| Non-TTY (piped, test) | `input_with_history` falls back to plain `input()` |
| Windows | Falls back to plain `input()` (no termios) |
| Ctrl-C during prompt | Raise `KeyboardInterrupt` (existing handler catches) |
| Ctrl-D (empty input) | Raise `EOFError` (existing handler catches) |
| Empty session file | `load_session` returns `None`; `_swap_session` falls back to `clear_history` |
| No sessions exist | `/sessions` prints "no saved sessions" + skip |
| User cancels picker (Esc) | `_pick_session` returns `None`; `/use` no-ops silently |
| Switch to same wiki as current | Save skipped (same name), loads same session (no-op effectively) |

## Testing

### `tests/test_readline.py` (new)

```python
def test_input_with_history_returns_typed_text(monkeypatch):
    """Injects keystrokes via stdin mock, verifies return value."""

def test_input_with_history_handles_backspace(monkeypatch):
    """BS deletes char before cursor."""

def test_input_with_history_handles_arrow_left_right(monkeypatch):
    """Left/Right moves cursor without changing buffer; insert at new position."""

def test_input_with_history_handles_arrow_up_history(monkeypatch):
    """Up cycles through history list."""

def test_input_with_history_falls_back_when_not_tty(monkeypatch):
    """isatty() False → delegates to plain input()."""

def test_input_with_history_ctrl_c_raises(monkeypatch):
    """Ctrl-C raises KeyboardInterrupt."""

def test_input_with_history_ctrl_d_eof_raises(monkeypatch):
    """Empty Ctrl-D raises EOFError; Ctrl-D after content returns buffer."""
```

Testing strategy: use `monkeypatch.setattr(sys.stdin, "isatty", lambda: True)` plus feed bytes via `monkeypatch.setattr(sys.stdin, "read", ...)`. Each test is fully deterministic.

### `tests/test_sessions.py` (extend)

```python
def test_list_sessions_empty(tmp_sessions_dir):
    assert list_sessions() == []

def test_list_sessions_returns_saved(tmp_sessions_dir):
    save_session("work", [{"role": "user", "content": "x"}] * 5)
    save_session("home", [{"role": "user", "content": "y"}] * 3)
    out = list_sessions()
    assert len(out) == 2
    names = {s["wiki"] for s in out}
    assert names == {"work", "home"}

def test_list_sessions_includes_message_count(tmp_sessions_dir):
    save_session("w", [{"role": "user", "content": str(i)} for i in range(7)])
    out = list_sessions()
    assert out[0]["message_count"] == 7

def test_list_sessions_skips_corrupt(tmp_sessions_dir):
    save_session("good", [{"role": "user", "content": "x"}])
    (SESSIONS_DIR / "bad.json").write_text("not json")
    out = list_sessions()
    assert len(out) == 1
    assert out[0]["wiki"] == "good"
```

### `tests/test_ai_cli.py` (extend)

```python
def test_ai_sessions_lists_saved(capsys, tmp_wiki_config, tmp_sessions_dir):
    save_session("work", [{"role": "user", "content": "x"}])
    # Run /sessions dispatch, assert output mentions "work" + "messages"

def test_ai_use_jumps_to_named_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    save_session("work", [{"role": "user", "content": "x"}])
    # /use home  → should error (no home session)

def test_ai_use_with_existing_session_loads_messages(...):
    # Save wiki A session, pretend agent is on A, /use B → loads B's messages

def test_ai_use_saves_outgoing_before_load(...):
    # Verify save_session called for outgoing wiki before load

def test_ai_use_unknown_session_error(capsys, ...):
    # /use ghost → prints "not found" error

def test_ai_pick_session_returns_none_on_esc(...):
    # Mock _pick_session to return None → _swap_session not called, no message
```

Picker tests mock `_pick_session` directly — interactive TTY behavior is hard to test, so we test the dispatch contract, not the cursor mechanics.

## Files touched

- **New:** `wiki_cli/ai/readline.py`
- **Modify:** `wiki_cli/ai/sessions.py` — add `list_sessions()`
- **Modify:** `wiki_cli/ai/cli.py` — new slash commands, `_pick_session`, `_swap_session`, swap input → `input_with_history`
- **Modify:** `wiki_cli/wikis.py` — swap input → `input_with_history` in `_prompt_new_profile`
- **New:** `tests/test_readline.py`
- **Modify:** `tests/test_sessions.py` — add list_sessions tests
- **Modify:** `tests/test_ai_cli.py` — add /sessions + /use tests
- **Modify:** `README.md` — document new commands + readline behavior

## Out of scope (deferred)

- Multi-select session picker
- Session search/filter UI
- Persistent shell history across `wiki-ai` invocations (separate from session persistence)
- Readline swap in `cli_pages.py`, `cli_history.py`, `cli_jira.py`, `cli_main.py`, `utils.py` (only ai/cli.py + wikis.py for v1)
- Bracketed paste mode (advanced paste escaping)
- Mouse support
- History search (Ctrl-R)
- Tab completion
