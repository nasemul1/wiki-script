"""Wiki.js profile storage and active-client resolution.

Files (under ~/.config/wiki-cli/):
  - wikis.json         {name: {url, api_key}}   mode 0600
  - active_wiki.txt    single-line profile name  mode 0600
"""

from __future__ import annotations

import json
from pathlib import Path

from wiki_cli.exceptions import WikiJSError

WIKIS_DIR = Path.home() / ".config" / "wiki-cli"
WIKIS_FILE = WIKIS_DIR / "wikis.json"
ACTIVE_FILE = WIKIS_DIR / "active_wiki.txt"


def _ensure_mode(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError:
        pass


def _load_wikis() -> dict[str, dict[str, str]]:
    if not WIKIS_FILE.exists():
        return {}
    try:
        data = json.loads(WIKIS_FILE.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_wikis(data: dict[str, dict[str, str]]) -> None:
    WIKIS_DIR.mkdir(parents=True, exist_ok=True)
    WIKIS_FILE.write_text(json.dumps(data, indent=2) + "\n")
    _ensure_mode(WIKIS_FILE)


def list_wikis() -> dict[str, dict[str, str]]:
    """Return all saved wiki profiles."""
    return _load_wikis()


def get_wiki(name: str) -> dict[str, str] | None:
    """Return the profile named *name*, or None."""
    return _load_wikis().get(name)


def _validate(name: str, url: str, api_key: str) -> None:
    if not name or not name.strip():
        raise WikiJSError("name required")
    if any(ch.isspace() for ch in name):
        raise WikiJSError("name has no spaces allowed")
    if not url or not url.strip():
        raise WikiJSError("url required")
    stripped = url.strip()
    if not (stripped.startswith("http://") or stripped.startswith("https://")):
        raise WikiJSError("url must start with http:// or https://")
    if not api_key or not api_key.strip():
        raise WikiJSError("api key required")


def save_wiki(name: str, url: str, api_key: str) -> None:
    """Create or overwrite a named wiki profile. Rejects duplicates by name or URL."""
    _validate(name, url, api_key)
    name = name.strip()
    url = url.strip()
    api_key = api_key.strip()

    data = _load_wikis()

    if name.lower() in {k.lower() for k in data}:
        raise WikiJSError(f"wiki '{name}' already exists")

    for existing_name, entry in data.items():
        if entry.get("url") == url:
            raise WikiJSError(f"url already saved as '{existing_name}'")

    data[name] = {"url": url, "api_key": api_key}
    _save_wikis(data)


def remove_wiki(name: str) -> None:
    """Remove a profile by name. No-op if absent."""
    data = _load_wikis()
    if name in data:
        del data[name]
        _save_wikis(data)


def get_active_wiki_name() -> str | None:
    """Return the active profile name, or None."""
    if not ACTIVE_FILE.exists():
        return None
    name = ACTIVE_FILE.read_text().strip()
    return name or None


def set_active_wiki(name: str | None) -> None:
    """Persist the active profile name. Pass None to clear."""
    WIKIS_DIR.mkdir(parents=True, exist_ok=True)
    if name is None:
        ACTIVE_FILE.write_text("")
    else:
        ACTIVE_FILE.write_text(name + "\n")
    _ensure_mode(ACTIVE_FILE)


def get_active_client():
    """Return a WikiJSClient for the active profile. Raises WikiJSError if none."""
    from wiki_cli.client import WikiJSClient

    name = get_active_wiki_name()
    if not name:
        raise WikiJSError("no active wiki. run /switch-wiki to configure one.")
    entry = get_wiki(name)
    if not entry:
        raise WikiJSError("no active wiki. run /switch-wiki to configure one.")
    return WikiJSClient(url=entry["url"], api_key=entry["api_key"])


def _read_api_key() -> str:
    """Prompt for an API key via plain input() so paste works in any terminal.

    getpass.getpass() can hang or drop pasted content depending on terminal
    mode (bracketed paste, kitty/wezterm). Plain input() reads the whole
    line including pastes. This matches _enter_api_key() in
    wiki_cli/ai/cli.py which also uses input() for the same reason.
    """
    return input("  api key: ").strip()


def _prompt_new_profile() -> tuple[str, str, str]:
    while True:
        name = input("  name: ").strip()
        if not name:
            print("  required")
            continue
        if any(ch.isspace() for ch in name):
            print("  no spaces allowed")
            continue
        break

    while True:
        url = input("  url: ").strip()
        if url.startswith("http://") or url.startswith("https://"):
            break
        print("  url must start with http:// or https://")

    while True:
        api_key = _read_api_key()
        if api_key:
            return name, url, api_key
        print("  required")

    return "", "", ""  # unreachable


def switch_wiki_flow(arg: str = "") -> "WikiJSClient":
    """Interactive wiki switcher. Returns a freshly-built WikiJSClient.

    Args:
        arg: "" → interactive picker. "<name>" → jump to that profile.
             "--new" → force new-profile flow.
    """
    from wiki_cli.client import WikiJSClient

    if arg == "--new":
        name, url, api_key = _prompt_new_profile()
        save_wiki(name, url, api_key)
        set_active_wiki(name)
        print(f"  saved → active: {name}")
        return WikiJSClient(url=url, api_key=api_key)

    if arg:
        entry = get_wiki(arg)
        if not entry:
            raise WikiJSError(f"wiki '{arg}' not found")
        set_active_wiki(arg)
        print(f"  switched → {arg}")
        return WikiJSClient(url=entry["url"], api_key=entry["api_key"])

    data = list_wikis()
    names = sorted(data.keys())

    if names:
        print("  saved wikis:")
        for i, n in enumerate(names, 1):
            print(f"    {i}    {n:<16} {data[n]['url']}")
        print(f"    {len(names) + 1}    add new")
        print()
        while True:
            choice = input("  > ").strip() or "1"
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(names):
                    picked = names[idx - 1]
                    set_active_wiki(picked)
                    print(f"  switched → {picked}")
                    entry = data[picked]
                    return WikiJSClient(url=entry["url"], api_key=entry["api_key"])
                if idx == len(names) + 1:
                    break
            print("  invalid choice")
    else:
        print("  no saved wikis")

    name, url, api_key = _prompt_new_profile()
    save_wiki(name, url, api_key)
    set_active_wiki(name)
    print(f"  saved → active: {name}")
    return WikiJSClient(url=url, api_key=api_key)
