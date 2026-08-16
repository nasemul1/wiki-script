# Session Memory + 100k Context Window — Design

**Date:** 2026-08-16
**Status:** Approved (pending user spec review)

## Goal

Persist AI assistant conversation history to disk on a per-wiki basis so users can resume sessions across `wiki-ai` invocations. Bump `MAX_CONTEXT_TOKENS` from 50k to 100k with a soft warning when the active session approaches the cap.

## Decisions

- **Session identity:** One rolling session per wiki profile. Each profile owns at most one saved session.
- **Save trigger:** After every AI response + on wiki switch/add + on Ctrl-C / EOF.
- **Resume behavior:** Always auto-resume on `wiki-ai` start. Print a banner line showing message count + relative timestamp.
- **Token cap:** 100k soft cap. Warn once when accumulated tokens cross 80% of cap.
- **Storage location:** `~/.config/wiki-cli/sessions/<wiki-name>.json`, mode `0600`.

## Architecture

### New module: `wiki_cli/ai/sessions.py`

Owns disk persistence for per-wiki session history.

```python
SESSIONS_DIR: Path        # ~/.config/wiki-cli/sessions
SESSION_FILE_MODE: int     # 0o600

def load_session(wiki_name: str) -> dict | None
    # Returns {"messages": [...], "updated_at": str, "created_at": str} or None.
    # Returns None if file missing OR corrupt JSON.

def save_session(wiki_name: str, messages: list[dict]) -> None
    # Atomic write: tmp file in same dir + os.replace.
    # Updates updated_at. Preserves created_at if file existed, else sets now.

def delete_session(wiki_name: str) -> None
    # Removes the session file. No-op if missing.

def has_session(wiki_name: str) -> bool
    # Cheap file-exists check for startup.
```

Atomic write pattern:
```python
tmp = SESSIONS_DIR / f".{wiki_name}.json.tmp"
tmp.write_text(json.dumps(data, indent=2) + "\n")
tmp.chmod(0o600)
os.replace(tmp, SESSIONS_DIR / f"{wiki_name}.json")
```

### `wiki_cli/ai/agent.py` changes

**Constant:**
```python
MAX_CONTEXT_TOKENS = 100_000
```

**New constructor parameter:**
```python
def __init__(
    self,
    config: AIConfig | None = None,
    wiki_client: WikiJSClient | None = None,
    wiki_name: str | None = None,
) -> None:
    ...
    self.wiki_name = wiki_name  # session key for disk persistence
    self._warned_at_80pct = False
```

**New behavior:**

1. After every successful assistant response in `_run_openai`, call `save_session(self.wiki_name, self.messages)`.
2. `clear_history()` also calls `delete_session(self.wiki_name)`.
3. In `_trim_history`, when estimated tokens cross 80% of `MAX_CONTEXT_TOKENS` AND `self._warned_at_80pct` is False, print a one-time warning to stderr and set the flag.

Warning format:
```
⚠ context approaching 100k limit (~85k tokens). Older messages will be trimmed.
```

The flag prevents re-warning on every subsequent message.

### `wiki_cli/ai/cli.py` changes

**Startup (in `ai_mode`):**

After agent construction, attempt to load the session:

```python
if agent.wiki_name and has_session(agent.wiki_name):
    session = load_session(agent.wiki_name)
    if session:
        agent.messages = session["messages"]
        agent._warned_at_80pct = False
        print(f"  {D}resumed previous session ({len(session['messages'])} messages, last: {format_relative(session['updated_at'])}){R}\n")
```

`format_relative(timestamp: str) -> str` produces strings like `"2 hours ago"`, `"just now"`, `"3 days ago"`. Implementation can use simple elapsed-time math (no external deps).

`wiki_name` is set on the agent based on `get_active_wiki_name()` (already imported in `cli.py`).

**Switch wiki handlers** (`_cmd_switch_wiki`, `_cmd_add_wiki`):

Before mutating `agent.wiki_client` + `agent.pages`, save the outgoing session:
```python
if agent.wiki_name:
    save_session(agent.wiki_name, agent.messages)
```

After mutating, update `agent.wiki_name` to the new active name. Then attempt to load the incoming session:
```python
if has_session(agent.wiki_name):
    session = load_session(agent.wiki_name)
    if session:
        agent.messages = session["messages"]
        agent._warned_at_80pct = False
        print(f"  {D}resumed previous session for '{agent.wiki_name}' ({len(session['messages'])} messages){R}\n")
    else:
        agent.clear_history()
else:
    agent.clear_history()
```

**`/clear` slash command:**

```python
if prompt == "/clear":
    if agent.wiki_name:
        delete_session(agent.wiki_name)
    agent.clear_history()
    print(f"  {G}history cleared{R}\n")
    continue
```

(Extends the existing `/clear` dispatch — current code just calls `agent.clear_history()`.)

### Atomic save flow

After each `_run_openai` call where the assistant produced a final text response or completed tool calls, save. Saves also fire on switch/add. Order doesn't matter — last write wins.

A torn write (process killed mid-write) leaves either the old file intact (atomic `os.replace`) or no file at all (if the kill happens before `os.replace`). Worst-case loss: the most recent assistant turn.

### Resume edge cases

| Case | Behavior |
|---|---|
| First run, no session file | Fresh start. No banner. |
| Session file exists, JSON valid | Resume. Banner shows count + relative time. |
| Session file exists, JSON corrupt | Treat as missing. Log warning, start fresh. Don't delete (user may want to recover manually). |
| Session file exists, wiki no longer in wikis.json | Resume anyway. User can `/clear` or `/switch-wiki` to abandon. |
| Save fires while wiki_name is None | No-op. Don't write to disk without a key. |

## Error handling

| Case | Behavior |
|---|---|
| Disk full during save | Log to stderr, continue. Session is best-effort persistence, not a hard requirement. |
| Permission denied on sessions dir | Same as disk full — log + continue. |
| Session file exists but unreadable | Treat as missing (None). Don't delete. |
| Session JSON has wrong structure (missing `messages`) | Treat as missing. |
| Wiki name contains characters that fail filesystem (shouldn't happen — validated at save) | Sanitize: replace `/`, `\`, `..` with `_`. Defensive layer. |

## Testing

### `tests/test_sessions.py` (new)

```python
def test_save_load_roundtrip(tmp_sessions_dir):
    msgs = [{"role": "user", "content": "hi"}]
    save_session("work", msgs)
    loaded = load_session("work")
    assert loaded["messages"] == msgs
    assert "updated_at" in loaded

def test_load_missing_returns_none(tmp_sessions_dir):
    assert load_session("ghost") is None

def test_delete_session_removes_file(tmp_sessions_dir):
    save_session("a", [{"role": "user", "content": "x"}])
    delete_session("a")
    assert not has_session("a")

def test_save_session_file_mode_0600(tmp_sessions_dir):
    save_session("w", [{"role": "user", "content": "x"}])
    import stat
    assert stat.S_IMODE((SESSIONS_DIR / "w.json").stat().st_mode) == 0o600

def test_save_atomic_writes_to_temp_then_replace(tmp_sessions_dir):
    # First save creates a file
    save_session("w", [{"role": "user", "content": "v1"}])
    # Subsequent save replaces atomically — old file still readable as v1 until replace
    save_session("w", [{"role": "user", "content": "v2"}])
    assert load_session("w")["messages"] == [{"role": "user", "content": "v2"}]

def test_load_corrupt_json_returns_none(tmp_sessions_dir):
    (SESSIONS_DIR / "bad.json").write_text("{garbage")
    assert load_session("bad") is None

def test_has_session(tmp_sessions_dir):
    assert not has_session("x")
    save_session("x", [{"role": "user", "content": "x"}])
    assert has_session("x")
```

### `tests/test_ai_cli.py` additions

```python
def test_ai_saves_session_after_response(capsys, tmp_wiki_config, tmp_sessions_dir):
    """Each completed response writes to disk."""
    from wiki_cli.ai.cli import _save_session, has_session
    # Setup wiki + agent, simulate one run cycle, verify file exists

def test_ai_resumes_session_on_startup(capsys, tmp_wiki_config, tmp_sessions_dir):
    """Pre-populate session, verify agent.messages restored."""
    save_session(wiki_name, pre_existing_messages)
    # Launch ai_mode, verify banner printed + messages loaded

def test_ai_clear_wipes_session_file(capsys, tmp_wiki_config, tmp_sessions_dir):
    """/clear deletes the session file."""
    save_session(wiki_name, messages)
    # Type /clear, verify file gone

def test_ai_warning_on_80pct_context(capsys, tmp_wiki_config, tmp_sessions_dir):
    """When token estimate crosses 80%, warning prints once."""
```

### Agent tests (new `tests/test_agent.py` or extend existing)

```python
def test_trim_threshold_emits_warning_once(capsys):
    agent = WikiAgent(...)
    # Force _estimate_tokens above 80k by injecting large messages
    # First call: warning emitted
    # Second call: no warning
```

### Conftest fixture

Add `tmp_sessions_dir` fixture to `tests/conftest.py`:

```python
@pytest.fixture
def tmp_sessions_dir(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    monkeypatch.setattr(sessions_module, "SESSIONS_DIR", sessions_dir)
    return sessions_dir
```

## Files touched

- **New:** `wiki_cli/ai/sessions.py` — load/save/delete/has_session + SESSIONS_DIR constant
- **Modify:** `wiki_cli/ai/agent.py` — bump token cap, save on response, clear also wipes disk, warning logic
- **Modify:** `wiki_cli/ai/cli.py` — startup resume, switch/add save+load, `/clear` wipes disk
- **New:** `tests/test_sessions.py`
- **Modify:** `tests/conftest.py` — add `tmp_sessions_dir` fixture
- **Modify:** `tests/test_ai_cli.py` — extend with session tests
- **Modify:** `README.md` — note sessions feature + 100k token cap

## Out of scope (deferred)

- Multiple named sessions per wiki (one rolling per wiki — chosen)
- Search across past sessions
- Session import/export to share between users
- Per-provider model-specific context caps (just soft 100k with warning)
- Encryption at rest beyond file permissions (0600 only)
- Migration of any existing in-memory history to disk (none exists today)