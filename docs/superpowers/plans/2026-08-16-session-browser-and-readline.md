# Session Browser + ANSI Readline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `/sessions` (list) and `/use [name]` (hot-swap with arrow-key picker) slash commands to `wiki-ai`. Replace plain `input()` calls in `wiki_cli/ai/cli.py` and `wiki_cli/wikis.py` with an arrow-key-capable readline.

**Architecture:** New `wiki_cli/ai/readline.py` owns ANSI readline (POSIX `termios` + `tty`, fallback to plain `input()` on non-TTY). `wiki_cli/ai/sessions.py` gains `list_sessions()`. `wiki_cli/ai/cli.py` gains `_cmd_sessions`, `_pick_session`, `_swap_session` helpers + slash command dispatch. `wiki_cli/wikis.py` swaps `input()` → `input_with_history()` in `_prompt_new_profile()`.

**Tech Stack:** Python 3.10+, `termios`, `tty`, `pytest` with `monkeypatch`.

## Global Constraints

- POSIX-only termios code; non-TTY environments (Windows, piped tests) fall back to plain `input()`.
- Zero new dependencies (lightweight ANSI readline).
- Sessions persist at `~/.config/wiki-cli/sessions/<wiki-name>.json` (mode 0600) — unchanged from prior plan.
- `list_sessions()` skips corrupt files silently.
- `/sessions` and `/use` are AI assistant slash commands only — no main menu integration for v1.
- `/use` with no args opens the picker; `/use <name>` jumps directly; unknown name prints yellow error.
- Hot-swap semantics: save outgoing session before loading incoming.
- ANSI codes for picker: `\x1b[?1049h`/`\x1b[?1049l` alternate screen buffer, `\x1b[A`/`\x1b[B` up/down, `\r` enter, `\x1b` escape, `\x03` Ctrl-C.
- Tests use `monkeypatch.setattr(sys.stdin, ...)` for keystroke injection.

---

## Task 1: `list_sessions()` in sessions module

**Files:**
- Modify: `wiki_cli/ai/sessions.py`
- Modify: `tests/test_sessions.py` (add tests)

**Interfaces this task produces:**
```python
def list_sessions() -> list[dict[str, Any]]
    # Returns [{"wiki": str, "message_count": int, "updated_at": str, "created_at": str}, ...]
```

- [ ] **Step 1.1: Write failing tests**

Append to `tests/test_sessions.py`:

```python
def test_list_sessions_empty(tmp_sessions_dir):
    from wiki_cli.ai.sessions import list_sessions
    assert list_sessions() == []


def test_list_sessions_returns_saved(tmp_sessions_dir):
    from wiki_cli.ai.sessions import list_sessions
    save_session("work", [{"role": "user", "content": str(i)} for i in range(5)])
    save_session("home", [{"role": "user", "content": "y"}] * 3)
    out = list_sessions()
    assert len(out) == 2
    names = {s["wiki"] for s in out}
    assert names == {"work", "home"}


def test_list_sessions_includes_message_count(tmp_sessions_dir):
    from wiki_cli.ai.sessions import list_sessions
    save_session("w", [{"role": "user", "content": str(i)} for i in range(7)])
    out = list_sessions()
    assert len(out) == 1
    assert out[0]["message_count"] == 7
    assert out[0]["wiki"] == "w"


def test_list_sessions_skips_corrupt(tmp_sessions_dir):
    from wiki_cli.ai.sessions import list_sessions
    save_session("good", [{"role": "user", "content": "x"}])
    (sessions.SESSIONS_DIR / "bad.json").write_text("not json")
    out = list_sessions()
    assert len(out) == 1
    assert out[0]["wiki"] == "good"


def test_list_sessions_includes_timestamps(tmp_sessions_dir):
    from wiki_cli.ai.sessions import list_sessions
    save_session("w", [{"role": "user", "content": "x"}])
    out = list_sessions()
    assert out[0]["updated_at"]
    assert out[0]["created_at"]


def test_list_sessions_missing_dir_returns_empty(tmp_sessions_dir):
    from wiki_cli.ai.sessions import SESSIONS_DIR, list_sessions
    import shutil
    shutil.rmtree(SESSIONS_DIR)
    assert list_sessions() == []
```

- [ ] **Step 1.2: Run tests — verify RED**

Run: `uv run pytest tests/test_sessions.py -v -k "list_sessions"`
Expected: FAIL with `ImportError: cannot import name 'list_sessions'`.

- [ ] **Step 1.3: Add `list_sessions()` to `wiki_cli/ai/sessions.py`**

Append after `delete_session`:

```python
def list_sessions() -> list[dict[str, Any]]:
    """Return all saved sessions across all wikis.

    Skips corrupt files silently. Returns [] if SESSIONS_DIR does not exist.
    """
    if not SESSIONS_DIR.exists():
        return []
    out: list[dict[str, Any]] = []
    for path in SESSIONS_DIR.glob("*.json"):
        session = load_session(path.stem)
        if session is None:
            continue
        out.append(
            {
                "wiki": session.get("wiki", path.stem),
                "message_count": len(session.get("messages", [])),
                "updated_at": session.get("updated_at", ""),
                "created_at": session.get("created_at", ""),
            }
        )
    return out
```

- [ ] **Step 1.4: Run tests — verify GREEN**

Run: `uv run pytest tests/test_sessions.py -v`
Expected: all pass (existing 11 + 6 new = 17).

- [ ] **Step 1.5: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 257 + 6 = 263 pass.

- [ ] **Step 1.6: Commit**

```bash
git add wiki_cli/ai/sessions.py tests/test_sessions.py
git commit -m "feat(ai): list_sessions() helper for browsing all saved sessions"
```

---

## Task 2: ANSI readline module

**Files:**
- Create: `wiki_cli/ai/readline.py`
- Create: `tests/test_readline.py`

**Interfaces this task produces:**
```python
def input_with_history(prompt: str, *, history: list[str] | None = None) -> str
    # Drop-in replacement for input() with arrow-key cursor movement + history.
    # Falls back to plain input() on non-TTY (Windows, piped tests).
```

- [ ] **Step 2.1: Write failing tests**

Create `tests/test_readline.py`:

```python
"""Tests for ANSI readline wrapper."""

import sys
from unittest.mock import patch

import pytest

from wiki_cli.ai.readline import input_with_history


def _fake_stdin_isatty(tty=True):
    return lambda: tty


def _bytes_iter(*chunks):
    """Build a stdin mock that returns successive byte chunks per .read() call."""
    iterator = iter(chunks)

    def read(n=1):
        try:
            return next(iterator)
        except StopIteration:
            return ""

    return read


def test_input_with_history_returns_typed_text(monkeypatch):
    """Injects keystrokes via stdin mock, verifies return value."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)

    chars = ["h", "i", "\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios") as mock_t, patch(
        "wiki_cli.ai.readline.tty"
    ) as mock_tty:
        mock_t.tcgetattr.return_value = "fake"
        mock_tty.setraw.return_value = None
        result = input_with_history("> ")
    assert result == "hi"


def test_input_with_history_handles_backspace(monkeypatch):
    """BS deletes char before cursor."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["a", "b", "\x7f", "c", "\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "ac"


def test_input_with_history_arrow_left_right(monkeypatch):
    """Arrow keys don't change buffer, but cursor position moves."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["a", "b", "c", "\x1b", "[", "D", "X", "\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "abXc"


def test_input_with_history_arrow_up_history(monkeypatch):
    """Up arrow retrieves previous history entry."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ", history=["prev_line"])
    assert result == ""


def test_input_with_history_falls_back_when_not_tty(monkeypatch):
    """isatty() False delegates to plain input()."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(False))
    monkeypatch.setattr("builtins.input", lambda prompt="": "fallback_value")
    result = input_with_history("> ")
    assert result == "fallback_value"


def test_input_with_history_ctrl_c_raises_keyboard_interrupt(monkeypatch):
    """Ctrl-C raises KeyboardInterrupt."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["\x03"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        with pytest.raises(KeyboardInterrupt):
            input_with_history("> ")


def test_input_with_history_ctrl_d_empty_raises_eof(monkeypatch):
    """Ctrl-D on empty buffer raises EOFError."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["\x04"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        with pytest.raises(EOFError):
            input_with_history("> ")


def test_input_with_history_ctrl_d_after_content_returns_buffer(monkeypatch):
    """Ctrl-D after content returns buffer (no EOF)."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["x", "\x04"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: chars.pop(0) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "x"
```

- [ ] **Step 2.2: Run tests — verify RED**

Run: `uv run pytest tests/test_readline.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'wiki_cli.ai.readline'`.

- [ ] **Step 2.3: Implement `wiki_cli/ai/readline.py`**

```python
"""Lightweight ANSI readline for arrow-key cursor movement + history.

Drop-in replacement for input() that supports:
- Left/Right arrow keys to move cursor within the input line
- Up/Down arrow keys to cycle through history
- Home/End to jump to start/end of line
- Backspace (BS / DEL) to delete char before cursor
- Ctrl-C raises KeyboardInterrupt, Ctrl-D raises EOFError on empty buffer
- ANSI escape sequence parsing for the above

POSIX-only (uses termios + tty). On non-TTY (Windows, piped tests),
falls back to plain input().
"""

from __future__ import annotations

import sys


def _fallback(prompt: str) -> str:
    return input(prompt)


def input_with_history(prompt: str, *, history: list[str] | None = None) -> str:
    """Read a line of input with arrow-key cursor movement and history.

    Falls back to plain input() when stdin is not a TTY (e.g., pipes, tests).
    """
    if not sys.stdin.isatty():
        return _fallback(prompt)

    import termios
    import tty

    sys.stdout.write(prompt)
    sys.stdout.flush()

    buf: list[str] = []
    pos = 0
    hist = list(history or [])
    hist_idx = len(hist)

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)

        def refresh() -> None:
            """Redraw the current line from cursor position."""
            sys.stdout.write(f"\r{prompt}\x1b[K")
            sys.stdout.write("".join(buf))
            if pos < len(buf):
                sys.stdout.write(f"\x1b[{len(buf) - pos}D")
            sys.stdout.flush()

        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                break
            elif ch == "\x1b":
                seq = sys.stdin.read(2)
                if seq == "[A":
                    if hist_idx > 0:
                        hist_idx -= 1
                        buf = list(hist[hist_idx])
                        pos = len(buf)
                        refresh()
                elif seq == "[B":
                    if hist_idx < len(hist) - 1:
                        hist_idx += 1
                        buf = list(hist[hist_idx])
                        pos = len(buf)
                        refresh()
                    elif hist_idx == len(hist) - 1:
                        hist_idx = len(hist)
                        buf = []
                        pos = 0
                        refresh()
                elif seq == "[C":
                    if pos < len(buf):
                        sys.stdout.write("\x1b[C")
                        sys.stdout.flush()
                        pos += 1
                elif seq == "[D":
                    if pos > 0:
                        sys.stdout.write("\x1b[D")
                        sys.stdout.flush()
                        pos -= 1
                elif seq == "[H":
                    while pos > 0:
                        sys.stdout.write("\x1b[D")
                        pos -= 1
                    sys.stdout.flush()
                elif seq == "[F":
                    while pos < len(buf):
                        sys.stdout.write("\x1b[C")
                        pos += 1
                    sys.stdout.flush()
                elif seq == "[3":
                    extra = sys.stdin.read(1)
                    if extra == "~" and pos < len(buf):
                        del buf[pos]
                        refresh()
            elif ch in ("\x7f", "\x08"):
                if pos > 0:
                    del buf[pos - 1]
                    pos -= 1
                    refresh()
            elif ch == "\x03":
                raise KeyboardInterrupt
            elif ch == "\x04":
                if not buf:
                    raise EOFError
            elif ch.isprintable() or ch == " ":
                buf.insert(pos, ch)
                pos += 1
                sys.stdout.write("".join(buf[pos - 1:]))
                if pos < len(buf):
                    sys.stdout.write("\x1b[K")
                sys.stdout.flush()

    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    return "".join(buf)
```

- [ ] **Step 2.4: Run tests — verify GREEN**

Run: `uv run pytest tests/test_readline.py -v`
Expected: 8/8 pass.

- [ ] **Step 2.5: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 263 + 8 = 271 pass.

- [ ] **Step 2.6: Commit**

```bash
git add wiki_cli/ai/readline.py tests/test_readline.py
git commit -m "feat(ai): lightweight ANSI readline with arrow keys + history"
```

---

## Task 3: `/sessions` + `/use` + picker

**Files:**
- Modify: `wiki_cli/ai/cli.py`
- Modify: `tests/ai_cli/success.py` (add tests)
- Modify: `tests/test_ai_cli.py` (add wrappers)

**Interfaces this task produces:**
```python
def _cmd_sessions(agent: WikiAgent) -> None
def _pick_session(current_wiki: str | None = None) -> str | None
def _swap_session(agent: WikiAgent, target_wiki: str) -> None
```

- [ ] **Step 3.1: Write failing tests**

Append to `tests/ai_cli/success.py`:

```python
def test_ai_sessions_lists_saved(capsys, tmp_wiki_config, tmp_sessions_dir):
    """`/sessions` lists all saved sessions."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import save_session

    save_session("work", [{"role": "user", "content": "x"}])
    save_session("home", [{"role": "user", "content": "y"}, {"role": "user", "content": "z"}])

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    with patch(INPUT_PATCH, side_effect=iter(["/sessions", "exit"])):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            mock_agent = MagicMock()
                            mock_agent.wiki_name = "work"
                            mock_agent_cls.return_value = mock_agent
                            ai_mode()
    out = capsys.readouterr().out
    assert "work" in out
    assert "home" in out


def test_ai_use_jumps_to_named_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    """`/use <name>` hot-swaps to that wiki's session."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import save_session
    from wiki_cli.wikis import set_active_wiki

    save_session("home", [{"role": "user", "content": "home msg"}])
    save_session("work", [{"role": "user", "content": "x"}])
    set_active_wiki("work")

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    with patch(INPUT_PATCH, side_effect=iter(["/use home", "exit"])):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            mock_agent = MagicMock()
                            mock_agent.wiki_name = "work"
                            mock_agent.messages = [{"role": "system", "content": "s"}]
                            mock_agent_cls.return_value = mock_agent
                            ai_mode()
    assert mock_agent.wiki_name == "home"


def test_ai_use_with_no_arg_calls_picker(capsys, tmp_wiki_config, tmp_sessions_dir):
    """`/use` (no arg) calls _pick_session."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    with patch(INPUT_PATCH, side_effect=iter(["/use", "exit"])):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            mock_agent = MagicMock()
                            mock_agent.wiki_name = "work"
                            mock_agent_cls.return_value = mock_agent
                            with patch(
                                "wiki_cli.ai.cli._pick_session", return_value="home"
                            ) as mock_pick:
                                ai_mode()
    mock_pick.assert_called_once_with("work")


def test_ai_use_unknown_session_error(capsys, tmp_wiki_config, tmp_sessions_dir):
    """`/use ghost` prints error, no state change."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    with patch(INPUT_PATCH, side_effect=iter(["/use ghost", "exit"])):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            mock_agent = MagicMock()
                            mock_agent.wiki_name = "work"
                            mock_agent.messages = [{"role": "system", "content": "s"}]
                            mock_agent_cls.return_value = mock_agent
                            ai_mode()
    out = capsys.readouterr().out
    assert "not found" in out.lower()
    assert mock_agent.wiki_name == "work"


def test_ai_swap_session_saves_outgoing(tmp_wiki_config, tmp_sessions_dir):
    """_swap_session saves outgoing before loading incoming."""
    from wiki_cli.ai.cli import _swap_session
    from wiki_cli.ai.sessions import load_session, save_session

    agent = MagicMock()
    agent.wiki_name = "work"
    agent.messages = [{"role": "user", "content": "work content"}]
    agent._warned_at_80pct = True

    save_session("home", [{"role": "user", "content": "home prior"}])

    _swap_session(agent, "home")

    saved_work = load_session("work")
    assert saved_work["messages"] == agent.messages
    assert agent.messages[0]["content"] == "home prior"
    assert agent._warned_at_80pct is False
```

Append wrappers to `tests/test_ai_cli.py`:

```python
from ai_cli.success import test_ai_sessions_lists_saved as _sessions_list
from ai_cli.success import test_ai_use_jumps_to_named_session as _use_named
from ai_cli.success import test_ai_use_with_no_arg_calls_picker as _use_picker
from ai_cli.success import test_ai_use_unknown_session_error as _use_unknown
from ai_cli.success import test_ai_swap_session_saves_outgoing as _swap


def test_ai_sessions_lists_saved(capsys, tmp_wiki_config, tmp_sessions_dir):
    _sessions_list(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_use_jumps_to_named_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _use_named(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_use_with_no_arg_calls_picker(capsys, tmp_wiki_config, tmp_sessions_dir):
    _use_picker(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_use_unknown_session_error(capsys, tmp_wiki_config, tmp_sessions_dir):
    _use_unknown(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_swap_session_saves_outgoing(capsys, tmp_wiki_config, tmp_sessions_dir):
    _swap(capsys, tmp_wiki_config, tmp_sessions_dir)
```

- [ ] **Step 3.2: Run tests — verify RED**

Run: `uv run pytest tests/test_ai_cli.py -v -k "sessions or use or swap"`
Expected: FAIL with `ImportError` for `_cmd_sessions` / `_pick_session` / `_swap_session`.

- [ ] **Step 3.3: Implement helpers + dispatch in `wiki_cli/ai/cli.py`**

**Edit 1** — Add `list_sessions` import. Find the existing `from wiki_cli.ai.sessions import (...)` block and add `list_sessions`:

```python
from wiki_cli.ai.sessions import (
    delete_session,
    has_session,
    list_sessions,
    load_session,
    save_session,
)
```

**Edit 2** — Add `_cmd_sessions`, `_pick_session`, `_swap_session` functions. Insert after `_cmd_add_wiki` (search for that function's end):

```python
def _cmd_sessions(agent: WikiAgent) -> None:
    """List all saved wiki sessions."""
    sessions = list_sessions()
    if not sessions:
        print(f"  {D}no saved sessions{R}\n")
        return

    print(f"  {D}saved sessions:{R}")
    for s in sessions:
        marker = f" {G}*{R}" if s["wiki"] == agent.wiki_name else "  "
        rel = _format_relative(s["updated_at"])
        print(
            f"  {marker} {B}{s['wiki']:<16}{R} {s['message_count']:>4} msgs, last: {rel}"
        )
    print()


def _swap_session(agent: WikiAgent, target_wiki: str) -> None:
    """Hot-swap agent to use target_wiki's session. Saves outgoing first."""
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
        print(
            f"  {G}switched → {target_wiki} ({len(session['messages'])} messages){R}\n"
        )
    else:
        agent.clear_history()
        print(f"  {D}started fresh for {target_wiki}{R}\n")


def _pick_session(current_wiki: str | None = None) -> str | None:
    """Interactive picker. Arrow keys + Enter. Returns selected wiki name or None."""
    sessions = list_sessions()
    if not sessions:
        return None

    def sort_key(s):
        is_current = s["wiki"] != current_wiki
        return (is_current, s["updated_at"])

    sessions = sorted(sessions, key=sort_key, reverse=False)

    if not sys.stdin.isatty():
        return None

    import termios
    import tty

    selected = 0

    def render() -> None:
        sys.stdout.write("\x1b[?1049h")
        sys.stdout.write("\x1b[H")
        sys.stdout.write(f"  {B}Select a session (up/down + Enter, Esc to cancel){R}\n\n")
        for i, s in enumerate(sessions):
            marker = ">" if i == selected else " "
            rel = _format_relative(s["updated_at"])
            sys.stdout.write(
                f"  {marker} {s['wiki']:<16} {s['message_count']:>4} msgs, last: {rel}\n"
            )
        sys.stdout.flush()

    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        render()
        while True:
            ch = sys.stdin.read(1)
            if ch in ("\r", "\n"):
                sys.stdout.write("\x1b[?1049l")
                sys.stdout.flush()
                return sessions[selected]["wiki"]
            elif ch == "\x1b":
                seq = sys.stdin.read(2)
                if seq == "[A":
                    selected = max(0, selected - 1)
                elif seq == "[B":
                    selected = min(len(sessions) - 1, selected + 1)
                else:
                    sys.stdout.write("\x1b[?1049l")
                    sys.stdout.flush()
                    return None
                render()
            elif ch == "\x03":
                sys.stdout.write("\x1b[?1049l")
                sys.stdout.flush()
                return None
            elif ch == "\x04":
                sys.stdout.write("\x1b[?1049l")
                sys.stdout.flush()
                return None
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        sys.stdout.write("\x1b[?1049l")
        sys.stdout.flush()
```

**Edit 3** — Add `/sessions` + `/use` dispatch. Find the existing `/wikis` dispatch block and add before it:

```python
        if prompt == "/sessions":
            _cmd_sessions(agent)
            continue

        if prompt == "/use":
            picked = _pick_session(agent.wiki_name)
            if picked:
                _swap_session(agent, picked)
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

- [ ] **Step 3.4: Run tests — verify GREEN**

Run: `uv run pytest tests/test_ai_cli.py -v -k "sessions or use or swap"`
Expected: 5 pass.

- [ ] **Step 3.5: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 271 + 5 = 276 pass.

- [ ] **Step 3.6: Commit**

```bash
git add wiki_cli/ai/cli.py tests/ai_cli/success.py tests/test_ai_cli.py
git commit -m "feat(ai): /sessions list + /use hot-swap with arrow-key picker"
```

---

## Task 4: Readline swap in wikis.py + cli.py

**Files:**
- Modify: `wiki_cli/wikis.py`
- Modify: `wiki_cli/ai/cli.py`

- [ ] **Step 4.1: Swap `input()` → `input_with_history()` in `_prompt_new_profile` and `_read_api_key`**

Find the `_prompt_new_profile` function in `wiki_cli/wikis.py` (around line 127). Replace the three `input(...)` calls:

```python
        name = input("  name: ").strip()
```

→

```python
        from wiki_cli.ai.readline import input_with_history
        name = input_with_history("  name: ").strip()
```

```python
        url = input("  url: ").strip()
```

→

```python
        url = input_with_history("  url: ").strip()
```

Update `_read_api_key` (around line 127):

```python
def _read_api_key() -> str:
    """Prompt for an API key. Try getpass first (hides echo); fall back to
    plain input() so users can still paste."""
    try:
        return getpass.getpass("  api key: ").strip()
    except (OSError, EOFError):
        print("  (echo enabled — no tty for hidden input)")
        return input("  api key: ").strip()
```

→

```python
def _read_api_key() -> str:
    """Prompt for an API key. Try getpass first (hides echo); fall back to
    readline input() so users can still paste + edit."""
    try:
        return getpass.getpass("  api key: ").strip()
    except (OSError, EOFError):
        from wiki_cli.ai.readline import input_with_history
        print("  (echo enabled — no tty for hidden input)")
        return input_with_history("  api key: ").strip()
```

- [ ] **Step 4.2: Swap `input()` → `input_with_history()` in `wiki_cli/ai/cli.py` REPL loop + provider picker**

Find the REPL input read (search for `prompt = input(f"  {C}>{R} "`)):

```python
            prompt = input(f"  {C}>{R} ").strip()
```

→

```python
            from wiki_cli.ai.readline import input_with_history
            prompt = input_with_history(f"  {C}>{R} ").strip()
```

Find the input calls inside `_pick_provider` (search for `choice = input(f"  {C}>{R} "`)):

```python
            choice = input(f"  {C}>{R} ").strip() or "1"
```

→

```python
            from wiki_cli.ai.readline import input_with_history
            choice = input_with_history(f"  {C}>{R} ").strip() or "1"
```

Apply the same swap to the other ~6 `input(...)` calls in `cli.py` (model picker, api key prompt, etc.). Each gets a lazy `from wiki_cli.ai.readline import input_with_history` line.

- [ ] **Step 4.3: Run tests — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 276 pass.

- [ ] **Step 4.4: Commit**

```bash
git add wiki_cli/wikis.py wiki_cli/ai/cli.py
git commit -m "refactor(ai): use input_with_history in interactive prompts"
```

---

## Task 5: README update

**Files:**
- Modify: `README.md`

- [ ] **Step 5.1: Update README — add /sessions + /use + arrow-key input**

Find the existing "Session memory" subsection (added in the prior session-memory plan). After that subsection, add:

```markdown
### Browse and switch sessions

- `/sessions` — list all saved wiki sessions with message count + last activity.
- `/use` — interactive picker with arrow keys + Enter to select a session.
- `/use <name>` — jump directly to a named session.

Use `/use` to switch between wikis mid-conversation without restarting. The current session is saved first, then the selected one loads.

### Arrow-key input

Prompts in `wiki-ai` and the wiki profile setup now support arrow-key cursor movement (Left/Right/Home/End), backspace, history (Up/Down), and Ctrl-C/Ctrl-D. Pastes and edits behave like a standard terminal.
```

- [ ] **Step 5.2: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 276 pass (docs only).

- [ ] **Step 5.3: Commit**

```bash
git add README.md
git commit -m "docs: /sessions + /use + arrow-key input"
```

---

## Self-Review

**Spec coverage:**
- `list_sessions()` → Task 1
- `input_with_history()` readline → Task 2
- `/sessions` + `/use` + `_pick_session` + `_swap_session` → Task 3
- Readline swap in `wikis.py` + `cli.py` → Task 4
- README updates → Task 5

**Placeholder scan:** No TBDs. Exact code for each task.

**Type consistency:**
- `list_sessions() -> list[dict[str, Any]]` defined Task 1, used Task 3.
- `input_with_history(prompt, *, history=None) -> str` defined Task 2, used Task 4.
- `_cmd_sessions(agent)` + `_pick_session(current_wiki)` + `_swap_session(agent, target_wiki)` all defined and used in Task 3.
- `_format_relative(timestamp)` already exists from prior session-memory plan, used in Task 3.
