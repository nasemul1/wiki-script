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