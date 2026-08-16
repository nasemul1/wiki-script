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