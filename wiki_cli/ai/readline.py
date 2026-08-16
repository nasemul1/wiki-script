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

try:
    import termios as _termios
    import tty as _tty
except ImportError:
    _termios = None
    _tty = None

# Bind module-level aliases so tests can patch() them even on platforms where
# POSIX termios/tty are available; on non-POSIX they remain None and _fallback
# is used. Tests override these via unittest.mock.patch.
termios = _termios  # type: ignore[assignment]
tty = _tty  # type: ignore[assignment]


def _fallback(prompt: str) -> str:
    return input(prompt)


def input_with_history(prompt: str, *, history: list[str] | None = None) -> str:
    """Read a line of input with arrow-key cursor movement and history.

    Falls back to plain input() when stdin is not a TTY (e.g., pipes, tests).
    """
    if not sys.stdin.isatty() or _termios is None or _tty is None:
        return _fallback(prompt)

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
                # Ctrl-D with non-empty buffer submits current contents.
                sys.stdout.write("\r\n")
                sys.stdout.flush()
                break
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
