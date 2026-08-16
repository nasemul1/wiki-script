# Session Memory + 100k Context Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Persist AI assistant conversation history per-wiki profile so users can resume sessions across `wiki-ai` invocations. Bump the context window from 50k to 100k tokens with a soft warning at 80% capacity.

**Architecture:** New `wiki_cli/ai/sessions.py` module owns disk persistence (atomic temp+rename writes, JSON, mode 0600). `WikiAgent` gains `wiki_name` param + save hook + warning flag. `ai_mode()` resumes on startup and propagates wiki_name through switch/add handlers. Tests use a `tmp_sessions_dir` fixture that monkeypatches the `SESSIONS_DIR` constant.

**Tech Stack:** Python 3.10+, `json`, `os.replace`, `pathlib`, `pytest` with `tmp_path` + `monkeypatch`.

## Global Constraints

- Storage: `~/.config/wiki-cli/sessions/<wiki-name>.json` (mode 0600).
- `MAX_CONTEXT_TOKENS = 100_000` (hardcoded constant).
- One rolling session per wiki. Auto-resume on `wiki-ai` start.
- Save trigger: after every AI response in `run()`, on wiki switch/add path, on `/clear` (delete).
- Save fails are non-fatal — log to stderr, continue.
- Atomic write: temp file in same dir + `os.replace` (no torn writes).
- JSON schema: `{"wiki": str, "messages": list, "updated_at": str, "created_at": str}`.
- File mode 0600 enforced on session files.
- Tests use `tmp_sessions_dir` fixture (`wiki_cli.ai.sessions.SESSIONS_DIR` redirected to `tmp_path`).
- ANSI codes: `R = "\033[0m"` reset, `D = "\033[2m"` dim, `Y = "\033[33m"` yellow, `G = "\033[32m"` green.

---

## Task 1: Sessions module

**Files:**
- Create: `wiki_cli/ai/sessions.py`
- Create: `tests/test_sessions.py`
- Modify: `tests/conftest.py` (add `tmp_sessions_dir` fixture)

**Interfaces this task produces:**
```python
# wiki_cli/ai/sessions.py
SESSIONS_DIR: Path
SESSION_FILE_MODE: int   # 0o600

def load_session(wiki_name: str) -> dict | None
def save_session(wiki_name: str, messages: list[dict]) -> None
def delete_session(wiki_name: str) -> None
def has_session(wiki_name: str) -> bool
```

- [ ] **Step 1.1: Add `tmp_sessions_dir` fixture to `tests/conftest.py`**

Append to `tests/conftest.py`:

```python
import pytest
from wiki_cli import ai

# (existing imports stay)


@pytest.fixture
def tmp_sessions_dir(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    monkeypatch.setattr(ai.sessions, "SESSIONS_DIR", sessions_dir)
    return sessions_dir
```

- [ ] **Step 1.2: Write failing tests**

Create `tests/test_sessions.py`:

```python
"""Tests for wiki_cli.ai.sessions persistence layer."""

import json
import stat

from wiki_cli.ai import sessions
from wiki_cli.ai.sessions import (
    delete_session,
    has_session,
    load_session,
    save_session,
)


def test_save_load_roundtrip(tmp_sessions_dir):
    msgs = [{"role": "user", "content": "hi"}]
    save_session("work", msgs)
    loaded = load_session("work")
    assert loaded is not None
    assert loaded["messages"] == msgs
    assert "updated_at" in loaded
    assert "created_at" in loaded
    assert loaded["wiki"] == "work"


def test_load_missing_returns_none(tmp_sessions_dir):
    assert load_session("ghost") is None


def test_delete_session_removes_file(tmp_sessions_dir):
    save_session("a", [{"role": "user", "content": "x"}])
    assert has_session("a")
    delete_session("a")
    assert not has_session("a")


def test_delete_session_missing_is_noop(tmp_sessions_dir):
    delete_session("ghost")  # no raise


def test_has_session(tmp_sessions_dir):
    assert not has_session("x")
    save_session("x", [{"role": "user", "content": "x"}])
    assert has_session("x")


def test_save_session_file_mode_0600(tmp_sessions_dir):
    save_session("w", [{"role": "user", "content": "x"}])
    path = sessions.SESSIONS_DIR / "w.json"
    assert path.exists()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_save_preserves_created_at(tmp_sessions_dir):
    save_session("w", [{"role": "user", "content": "v1"}])
    first = load_session("w")
    save_session("w", [{"role": "user", "content": "v2"}])
    second = load_session("w")
    assert second["created_at"] == first["created_at"]
    assert second["updated_at"] >= first["updated_at"]


def test_save_updates_updated_at(tmp_sessions_dir):
    save_session("w", [{"role": "user", "content": "v1"}])
    first = load_session("w")
    save_session("w", [{"role": "user", "content": "v2"}])
    second = load_session("w")
    assert second["updated_at"] >= first["updated_at"]


def test_load_corrupt_json_returns_none(tmp_sessions_dir):
    (sessions.SESSIONS_DIR / "bad.json").write_text("{garbage")
    assert load_session("bad") is None


def test_load_missing_messages_key_returns_none(tmp_sessions_dir):
    (sessions.SESSIONS_DIR / "broken.json").write_text(json.dumps({"wiki": "x"}))
    assert load_session("broken") is None


def test_save_atomically_replaces(tmp_sessions_dir):
    """No torn writes — old file intact until os.replace."""
    save_session("w", [{"role": "user", "content": "v1"}])
    save_session("w", [{"role": "user", "content": "v2"}])
    loaded = load_session("w")
    assert loaded["messages"] == [{"role": "user", "content": "v2"}]
    # No .tmp files left
    tmps = list(sessions.SESSIONS_DIR.glob("*.tmp"))
    assert tmps == []
```

- [ ] **Step 1.3: Run tests — verify RED**

Run: `uv run pytest tests/test_sessions.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'wiki_cli.ai.sessions'`.

- [ ] **Step 1.4: Implement `wiki_cli/ai/sessions.py`**

```python
"""Per-wiki AI session persistence.

Each wiki profile owns one rolling session file. Sessions live at
~/.config/wiki-cli/sessions/<wiki-name>.json (mode 0600). Writes are
atomic via temp file + os.replace.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SESSIONS_DIR = Path.home() / ".config" / "wiki-cli" / "sessions"
_SESSION_FILE_MODE = 0o600


def _session_path(wiki_name: str) -> Path:
    return SESSIONS_DIR / f"{wiki_name}.json"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def has_session(wiki_name: str) -> bool:
    """Return True if a session file exists for *wiki_name*."""
    return _session_path(wiki_name).exists()


def load_session(wiki_name: str) -> dict[str, Any] | None:
    """Load the session for *wiki_name*, or None if missing/invalid.

    Returns None for: missing file, corrupt JSON, JSON missing 'messages'
    key. Does NOT delete the file on failure (user may want to recover).
    """
    path = _session_path(wiki_name)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
    except Exception:
        return None
    if not isinstance(data, dict) or "messages" not in data:
        return None
    return data


def save_session(wiki_name: str, messages: list[dict[str, Any]]) -> None:
    """Atomically save *messages* as the session for *wiki_name*.

    Preserves created_at if file exists; updates updated_at. Missing
    parent directory is created. Errors are non-fatal (caller can wrap).
    """
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)
    existing = load_session(wiki_name)
    now = _now()
    data = {
        "wiki": wiki_name,
        "messages": messages,
        "created_at": existing["created_at"] if existing else now,
        "updated_at": now,
    }
    target = _session_path(wiki_name)
    tmp = SESSIONS_DIR / f".{wiki_name}.json.tmp"
    tmp.write_text(json.dumps(data, indent=2) + "\n")
    try:
        tmp.chmod(_SESSION_FILE_MODE)
    except OSError:
        pass
    os.replace(tmp, target)


def delete_session(wiki_name: str) -> None:
    """Remove the session file for *wiki_name*. No-op if absent."""
    path = _session_path(wiki_name)
    if path.exists():
        path.unlink()
```

- [ ] **Step 1.5: Run tests — verify GREEN**

Run: `uv run pytest tests/test_sessions.py -v`
Expected: 11 pass.

- [ ] **Step 1.6: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: previously 239 + 11 new = 250 pass. (Jira tests excluded because they require env vars; ignore isn't strictly necessary but skips their expected failures.)

- [ ] **Step 1.7: Commit**

```bash
git add wiki_cli/ai/sessions.py tests/test_sessions.py tests/conftest.py
git commit -m "feat(ai): per-wiki session persistence with atomic writes"
```

---

## Task 2: Agent wiring (token cap + save + warning)

**Files:**
- Modify: `wiki_cli/ai/agent.py`
- Modify: `tests/ai_cli/success.py` (add agent-save test)
- Modify: `tests/test_ai_cli.py` (add wrapper)

**Interfaces this task changes:**
```python
class WikiAgent:
    def __init__(
        self,
        config: AIConfig | None = None,
        wiki_client: WikiJSClient | None = None,
        wiki_name: str | None = None,   # NEW
    ) -> None: ...
    def run(self, user_prompt: str) -> str: ...   # Now saves after each response
    def clear_history(self) -> None: ...          # Now also deletes session file
    def _warned_at_80pct: bool                     # NEW attribute
```

- [ ] **Step 2.1: Write failing tests**

Append to `tests/ai_cli/success.py`:

```python
def test_agent_saves_session_after_run(tmp_sessions_dir, tmp_wiki_config):
    """WikiAgent.run() persists the messages list to disk."""
    from wiki_cli.ai.agent import WikiAgent
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import has_session, load_session

    agent = WikiAgent(
        config=AIConfig(provider="openrouter", api_key="x", model="m", base_url=""),
        wiki_name="work",
    )
    agent.run("hi")  # mocked; works because client is also mocked
    assert has_session("work")
    loaded = load_session("work")
    assert loaded["messages"] == agent.messages


def test_agent_clear_history_deletes_session(tmp_sessions_dir, tmp_wiki_config):
    """WikiAgent.clear_history() also deletes the session file."""
    from wiki_cli.ai.agent import WikiAgent
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import has_session, save_session

    agent = WikiAgent(
        config=AIConfig(provider="openrouter", api_key="x", model="m", base_url=""),
        wiki_name="work",
    )
    save_session("work", [{"role": "user", "content": "x"}])
    assert has_session("work")
    agent.clear_history()
    assert not has_session("work")


def test_agent_warns_on_80pct_context(tmp_sessions_dir, tmp_wiki_config, capsys):
    """Warning fires once when estimate crosses 80% of MAX_CONTEXT_TOKENS."""
    from wiki_cli.ai.agent import MAX_CONTEXT_TOKENS, WikiAgent
    from wiki_cli.ai.config import AIConfig

    agent = WikiAgent(
        config=AIConfig(provider="openrouter", api_key="x", model="m", base_url=""),
        wiki_name="work",
    )
    # Inject messages that exceed 80% of MAX_CONTEXT_TOKENS (~80k tokens).
    # 4 chars per token estimate, so 80k tokens = 320k chars total.
    big = "x" * 350_000
    agent.messages = [
        {"role": "system", "content": "s"},
        {"role": "user", "content": big},
    ]
    with patch("sys.stderr") as mock_stderr:
        agent._check_token_warning()
    assert MAX_CONTEXT_TOKENS == 100_000
    output = str(mock_stderr.write.call_args)
    assert "approaching" in output.lower() or "warning" in output.lower()
```

Also append wrappers to `tests/test_ai_cli.py`:

```python
from ai_cli.success import test_agent_saves_session_after_run as _agent_save
from ai_cli.success import test_agent_clear_history_deletes_session as _agent_clear
from ai_cli.success import test_agent_warns_on_80pct_context as _agent_warn


def test_agent_saves_session_after_run(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_save(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_agent_clear_history_deletes_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_clear(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_agent_warns_on_80pct_context(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_warn(capsys, tmp_wiki_config, tmp_sessions_dir)
```

- [ ] **Step 2.2: Run tests — verify RED**

Run: `uv run pytest tests/test_ai_cli.py -v -k "agent_saves or agent_clear or agent_warns"`
Expected: FAIL with `TypeError: __init__() got an unexpected keyword argument 'wiki_name'` (or similar).

- [ ] **Step 2.3: Update `wiki_cli/ai/agent.py`**

Three edits.

**Edit 1** — Bump token cap:

Replace line 51:
```python
MAX_CONTEXT_TOKENS = 50_000
```
with:
```python
MAX_CONTEXT_TOKENS = 100_000
```

**Edit 2** — Update `__init__` to accept `wiki_name`:

Replace the existing `__init__` body (lines 75-103) with:

```python
    def __init__(
        self,
        config: AIConfig | None = None,
        wiki_client: WikiJSClient | None = None,
        wiki_name: str | None = None,
    ) -> None:
        self.config = config or AIConfig()
        if wiki_client is None:
            from wiki_cli.wikis import get_active_client

            self.wiki_client = get_active_client()
        else:
            self.wiki_client = wiki_client
        self.pages = PagesManager(self.wiki_client)
        self.client = self.config.get_client()
        self.wiki_name = wiki_name
        self._warned_at_80pct = False
        self.messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self.quiet = False

        # Jira (optional — gracefully unavailable if not configured)
        self.jira_manager = None
        try:
            from wiki_cli.jira.client import JiraClient
            from wiki_cli.jira.manager import JiraManager

            jira_client = JiraClient()
            self.jira_manager = JiraManager(jira_client)
        except Exception:
            pass
```

**Edit 3** — Add session save to `run()` and update `clear_history()`:

Replace `run` (lines 105-116) with:

```python
    def run(self, user_prompt: str) -> str:
        """Process a user prompt and return the AI's response.

        Maintains conversation history across calls so the LLM retains context.
        Persists history to disk after each response when wiki_name is set.
        """
        result = self._run_openai(user_prompt)
        if self.wiki_name:
            try:
                from wiki_cli.ai.sessions import save_session
                save_session(self.wiki_name, self.messages)
            except Exception:
                pass  # non-fatal
        return result
```

Replace `clear_history` (lines 118-122) with:

```python
    def clear_history(self) -> None:
        """Reset conversation history, keeping only the system prompt.
        Also deletes the on-disk session file if wiki_name is set.
        """
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
        ]
        self._warned_at_80pct = False
        if self.wiki_name:
            try:
                from wiki_cli.ai.sessions import delete_session
                delete_session(self.wiki_name)
            except Exception:
                pass
```

**Edit 4** — Add `_check_token_warning` method. Insert after `clear_history`:

```python
    def _check_token_warning(self) -> None:
        """Print a one-time warning when token estimate crosses 80% of MAX_CONTEXT_TOKENS."""
        if self._warned_at_80pct:
            return
        estimated = self._estimate_tokens(self.messages)
        threshold = int(MAX_CONTEXT_TOKENS * 0.8)
        if estimated >= threshold:
            import sys
            print(
                f"\n⚠ context approaching {MAX_CONTEXT_TOKENS // 1000}k limit "
                f"(~{estimated // 1000}k tokens). Older messages will be trimmed.",
                file=sys.stderr,
            )
            self._warned_at_80pct = True
```

**Edit 5** — Call `_check_token_warning` from `_trim_history`.

Find `_trim_history` (around line 137). Add a call at the top:

```python
    def _trim_history(self) -> None:
        self._check_token_warning()
        if self._estimate_tokens(self.messages) <= MAX_CONTEXT_TOKENS:
            return
        # ... existing body
```

If the body already exists, prepend the two new lines. Don't change anything else.

- [ ] **Step 2.4: Run tests — verify GREEN**

Run: `uv run pytest tests/test_ai_cli.py -v -k "agent_saves or agent_clear or agent_warns"`
Expected: 3 pass.

- [ ] **Step 2.5: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 250 pass + 3 new = 253 pass.

- [ ] **Step 2.6: Commit**

```bash
git add wiki_cli/ai/agent.py tests/ai_cli/success.py tests/test_ai_cli.py
git commit -m "feat(ai): 100k context cap + session save/clear + 80% warning"
```

---

## Task 3: CLI integration (startup resume + switch hooks + /clear)

**Files:**
- Modify: `wiki_cli/ai/cli.py`
- Modify: `tests/ai_cli/success.py` (add 3 tests)
- Modify: `tests/test_ai_cli.py` (add wrappers)

- [ ] **Step 3.1: Write failing tests**

Append to `tests/ai_cli/success.py`:

```python
def test_ai_startup_resumes_existing_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    """ai_mode() loads a pre-existing session and prints resume banner."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import save_session

    save_session("work", [
        {"role": "system", "content": "s"},
        {"role": "user", "content": "previous question"},
        {"role": "assistant", "content": "previous answer"},
    ])

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    with patch(INPUT_PATCH, side_effect=iter(["exit"])):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            ai_mode()
    mock_agent_cls.assert_called_once()
    kwargs = mock_agent_cls.call_args.kwargs
    assert kwargs.get("wiki_name") == "work"
    out = capsys.readouterr().out
    assert "resumed" in out.lower()


def test_ai_clear_wipes_session_file(tmp_wiki_config, tmp_sessions_dir):
    """ai_mode /clear dispatch deletes the session file."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import has_session, save_session

    save_session("work", [{"role": "user", "content": "x"}])
    assert has_session("work")

    fake = MagicMock()
    fake.url = "https://w.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    inputs = iter(["/clear", "exit"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent") as mock_agent_cls:
                            mock_agent = MagicMock()
                            mock_agent.wiki_name = "work"
                            mock_agent_cls.return_value = mock_agent
                            ai_mode()
    assert not has_session("work")
```

Add wrappers to `tests/test_ai_cli.py`:

```python
from ai_cli.success import test_ai_startup_resumes_existing_session as _resume
from ai_cli.success import test_ai_clear_wipes_session_file as _clear_wipe


def test_ai_startup_resumes_existing_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _resume(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_clear_wipes_session_file(capsys, tmp_wiki_config, tmp_sessions_dir):
    _clear_wipe(capsys, tmp_wiki_config, tmp_sessions_dir)
```

- [ ] **Step 3.2: Run tests — verify RED**

Run: `uv run pytest tests/test_ai_cli.py -v -k "resumes or clear_wipes"`
Expected: FAIL (wiki_name not passed to WikiAgent constructor; /clear doesn't delete session).

- [ ] **Step 3.3: Update `wiki_cli/ai/cli.py`**

Three edits.

**Edit 1** — Add session imports at the top of `ai_mode`'s imports. Find the `from wiki_cli.wikis import ...` block (around line 30) and add:

```python
from wiki_cli.ai.sessions import (
    delete_session,
    has_session,
    load_session,
    save_session,
)
```

**Edit 2** — Update `ai_mode` startup to pass `wiki_name` and resume session.

Find the agent construction in `ai_mode` (around lines 432-436):

```python
        if last and get_saved_key(last.get("provider", "")):
            provider = last["provider"]
            model = last["model"]
            config = _build_config_from_saved(provider, model)
            agent = WikiAgent(config=config, wiki_client=client)
        else:
            config = _build_config()
            agent = WikiAgent(config=config, wiki_client=client)
```

Replace both `WikiAgent(...)` calls with versions that pass `wiki_name`.

Inspect the file to find where the active wiki name is available. The startup block already has `client = get_active_client()` or `client = switch_wiki_flow()`. After that, the active wiki name can be obtained via `get_active_wiki_name()` (already imported in cli.py).

Add a line after the client construction:

```python
        wiki_name = get_active_wiki_name()
```

Then update both `WikiAgent(...)` calls to include `wiki_name=wiki_name`:

```python
        if last and get_saved_key(last.get("provider", "")):
            provider = last["provider"]
            model = last["model"]
            config = _build_config_from_saved(provider, model)
            agent = WikiAgent(config=config, wiki_client=client, wiki_name=wiki_name)
        else:
            config = _build_config()
            agent = WikiAgent(config=config, wiki_client=client, wiki_name=wiki_name)
```

**Then** after the agent is constructed, add the resume block (immediately after `agent = WikiAgent(...)`):

```python
        if wiki_name and has_session(wiki_name):
            session = load_session(wiki_name)
            if session:
                agent.messages = session["messages"]
                agent._warned_at_80pct = False
                timestamp = session.get("updated_at", "")
                rel = _format_relative(timestamp)
                print(
                    f"  {D}resumed previous session ({len(session['messages'])} messages, last: {rel}){R}\n"
                )
```

**Edit 3** — Add `_format_relative` helper somewhere in `ai/cli.py` (anywhere before `ai_mode()` is fine). Insert just before the `ai_mode` function:

```python
def _format_relative(timestamp: str) -> str:
    """Format an ISO timestamp as a human-readable relative time."""
    if not timestamp:
        return "unknown"
    from datetime import datetime, timezone
    try:
        dt = datetime.fromisoformat(timestamp)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return "just now"
        if seconds < 3600:
            m = seconds // 60
            return f"{m} min ago" if m == 1 else f"{m} mins ago"
        if seconds < 86400:
            h = seconds // 3600
            return f"{h} hour ago" if h == 1 else f"{h} hours ago"
        d = seconds // 86400
        return f"{d} day ago" if d == 1 else f"{d} days ago"
    except Exception:
        return "unknown"
```

**Edit 4** — Update `/clear` dispatch. Find the existing `/clear` block (around line 451):

```python
        if prompt == "/clear":
            agent.clear_history()
            print(f"  {G}history cleared{R}\n")
            continue
```

Replace with:

```python
        if prompt == "/clear":
            if agent.wiki_name:
                try:
                    delete_session(agent.wiki_name)
                except Exception:
                    pass
            agent.clear_history()
            print(f"  {G}history cleared{R}\n")
            continue
```

- [ ] **Step 3.4: Run tests — verify GREEN**

Run: `uv run pytest tests/test_ai_cli.py -v -k "resumes or clear_wipes"`
Expected: 2 pass.

- [ ] **Step 3.5: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 253 + 2 = 255 pass.

- [ ] **Step 3.6: Commit**

```bash
git add wiki_cli/ai/cli.py tests/ai_cli/success.py tests/test_ai_cli.py
git commit -m "feat(ai): wire session load on startup + delete on /clear"
```

---

## Task 4: README + finishing

**Files:**
- Modify: `README.md`

- [ ] **Step 4.1: Update README — add session memory mentions + 100k token limit**

In `README.md`, find the "Slash commands" subsection. After the existing commands table, add a brief note:

```markdown
### Session memory

Conversations persist per wiki profile. When you reopen `wiki-ai`, the previous session is restored automatically with a banner showing message count and last activity. Use `/clear` to wipe the current wiki's session. Sessions live at `~/.config/wiki-cli/sessions/<wiki-name>.json` (mode `0600`).

The AI assistant caps context at 100,000 tokens. When cumulative messages cross 80% of that limit, a one-time warning prints and older messages get trimmed.
```

Insert this block right after the slash commands table (before the "LLM providers" subsection).

- [ ] **Step 4.2: Run full suite — verify no regressions**

Run: `uv run pytest tests/ --ignore=tests/test_jira_client.py --ignore=tests/test_jira_config.py -q 2>&1 | tail -5`
Expected: 255 pass (no regressions).

- [ ] **Step 4.3: Commit**

```bash
git add README.md
git commit -m "docs: session memory + 100k context"
```

---

## Self-Review

**Spec coverage:**
- `MAX_CONTEXT_TOKENS = 100_000` → Task 2 Edit 1
- One rolling session per wiki → Tasks 1 + 2 + 3 (consistent)
- Save on every response → Task 2 Edit 3 (run() saves)
- Save on switch/add → Task 3 Edit 2 (passes wiki_name; existing switch/add handlers already rebuild agent)
- Save on Ctrl-C → handled by `run()` saving after each response (no extra code needed)
- Auto-resume on startup → Task 3 Edit 2 (post-agent construction)
- `/clear` wipes disk → Task 3 Edit 4
- 80% warning → Task 2 Edit 4 + Edit 5
- Atomic writes → Task 1 Step 1.4 (os.replace)
- File mode 0600 → Task 1 Step 1.4 (chmod after write)
- Storage location `~/.config/wiki-cli/sessions/` → Task 1
- JSON schema → Task 1
- File mode 0600 test → Task 1 Step 1.2
- Atomic write test → Task 1 Step 1.2
- README update → Task 4

**Placeholder scan:** No TBDs. Exact code for every step.

**Type consistency:**
- Session module exports: `SESSIONS_DIR`, `load_session`, `save_session`, `delete_session`, `has_session` — used consistently across Tasks 1, 2, 3.
- `MAX_CONTEXT_TOKENS = 100_000` defined in Task 2, referenced in Task 2's warning logic.
- `wiki_name: str | None = None` parameter added in Task 2, used in Task 3 to pass `wiki_name` to constructor.
- `_warned_at_80pct` flag set in Task 2 (`__init__` and `clear_history`), checked in Task 2 (`_check_token_warning`).
- `_format_relative` defined in Task 3, used in Task 3's resume block.
- `tmp_sessions_dir` fixture added in Task 1, used in Tasks 2 and 3 tests.
