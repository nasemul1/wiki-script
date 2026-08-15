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
