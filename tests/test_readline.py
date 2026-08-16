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
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
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
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "ac"


def test_input_with_history_arrow_left_right(monkeypatch):
    """Arrow keys don't change buffer, but cursor position moves."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["a", "b", "c", "\x1b", "[", "D", "X", "\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "abXc"


def test_input_with_history_arrow_up_history(monkeypatch):
    """Up arrow retrieves previous history entry."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["\r"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
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
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        with pytest.raises(KeyboardInterrupt):
            input_with_history("> ")


def test_input_with_history_ctrl_d_empty_raises_eof(monkeypatch):
    """Ctrl-D on empty buffer raises EOFError."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["\x04"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        with pytest.raises(EOFError):
            input_with_history("> ")


def test_input_with_history_ctrl_d_after_content_returns_buffer(monkeypatch):
    """Ctrl-D after content returns buffer (no EOF)."""
    monkeypatch.setattr(sys.stdin, "isatty", _fake_stdin_isatty(True))
    monkeypatch.setattr(sys.stdin, "fileno", lambda: 0)
    chars = ["x", "\x04"]
    monkeypatch.setattr(sys.stdin, "read", lambda n=1: "".join(chars.pop(0) for _ in range(n)) if chars else "")
    with patch("wiki_cli.ai.readline.termios"), patch("wiki_cli.ai.readline.tty"):
        result = input_with_history("> ")
    assert result == "x"
