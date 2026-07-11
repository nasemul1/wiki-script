"""AI provider configuration and credential storage.

Supported providers:
  - openai       OpenAI API (gpt-4o, gpt-4o-mini, etc.)
  - openrouter   OpenRouter (access 100+ models via openrouter.ai)
  - groq         Groq (fast inference for llama, mixtral, gemma, etc.)
  - mistral      Mistral AI (mistral-tiny, mistral-small, etc.)
  - ollama       Ollama local (llama3, mistral, codellama, etc.)
  - ollama-cloud Ollama via remote server
"""

from __future__ import annotations

import json
import getpass
import httpx
from dataclasses import dataclass
from pathlib import Path


# ---------------------------------------------------------------------------
# Credential storage  (~/.config/wiki-cli/credentials.json)
# ---------------------------------------------------------------------------

_CRED_DIR = Path.home() / ".config" / "wiki-cli"
_CRED_FILE = _CRED_DIR / "credentials.json"


def _load_credentials() -> dict[str, str]:
    """Load saved API keys from disk."""
    if not _CRED_FILE.exists():
        return {}
    try:
        return json.loads(_CRED_FILE.read_text())
    except Exception:
        return {}


def _save_credentials(creds: dict[str, str]) -> None:
    """Persist API keys to disk."""
    _CRED_DIR.mkdir(parents=True, exist_ok=True)
    _CRED_FILE.write_text(json.dumps(creds, indent=2) + "\n")
    # Restrict file permissions (owner read/write only)
    _CRED_FILE.chmod(0o600)


def get_saved_key(provider: str) -> str:
    """Return the saved API key for *provider*, or empty string."""
    return _load_credentials().get(provider, "")


def save_key(provider: str, api_key: str) -> None:
    """Save an API key for *provider*."""
    creds = _load_credentials()
    creds[provider] = api_key
    _save_credentials(creds)


def remove_key(provider: str) -> None:
    """Remove the saved API key for *provider*."""
    creds = _load_credentials()
    creds.pop(provider, None)
    _save_credentials(creds)


def list_saved_keys() -> dict[str, str]:
    """Return all saved API keys."""
    return _load_credentials()


# ---------------------------------------------------------------------------
# Provider defaults
# ---------------------------------------------------------------------------

PROVIDER_DEFAULTS: dict[str, dict[str, str]] = {
    "openai": {
        "base_url": "https://api.openai.com/v1",
        "models_url": "https://api.openai.com/v1/models",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "models_url": "https://openrouter.ai/api/v1/models",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "models_url": "https://api.groq.com/openai/v1/models",
    },
    "mistral": {
        "base_url": "https://api.mistral.ai/v1",
        "models_url": "https://api.mistral.ai/v1/models",
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "models_url": "http://localhost:11434/api/tags",
    },
    "ollama-cloud": {
        "base_url": "",
        "models_url": "",
    },
}


# ---------------------------------------------------------------------------
# AIConfig
# ---------------------------------------------------------------------------

@dataclass
class AIConfig:
    """Configuration for the AI provider."""

    provider: str = ""
    api_key: str = ""
    model: str = ""
    base_url: str = ""

    def get_client(self):
        """Initialize and return the OpenAI-compatible LLM client."""
        import openai

        kwargs: dict[str, str] = {}
        if self.provider == "ollama":
            kwargs["api_key"] = "ollama"
        else:
            kwargs["api_key"] = self.api_key

        if self.base_url:
            kwargs["base_url"] = self.base_url

        return openai.OpenAI(**kwargs)


# ---------------------------------------------------------------------------
# Model fetching
# ---------------------------------------------------------------------------

def fetch_models(provider: str, api_key: str = "", base_url: str = "") -> list[str]:
    """Fetch available models from the provider's API.

    Returns a sorted list of model ID strings.
    """
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    models_url = defaults.get("models_url", "")
    if not models_url:
        return []

    headers: dict[str, str] = {}
    if api_key and provider != "ollama":
        headers["Authorization"] = f"Bearer {api_key}"

    try:
        resp = httpx.get(models_url, headers=headers, timeout=10)
        resp.raise_for_status()
        data = resp.json()
    except Exception:
        return []

    if provider == "ollama":
        return sorted(m.get("name", "") for m in data.get("models", []) if m.get("name"))

    models = data.get("data", [])
    ids = sorted(m.get("id", "") for m in models if m.get("id"))
    return ids
