"""Interactive AI chat interface for Wiki.js management.

Startup: if saved keys exist → quick start; otherwise full setup.
During chat: /providers, /models, /remove-key, /help
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

from wiki_cli import WikiJSError, wikis
from wiki_cli.ai.agent import WikiAgent
from wiki_cli.ai.config import (
    AIConfig,
    PROVIDER_DEFAULTS,
    fetch_models,
    get_saved_key,
    save_key,
    remove_key,
    list_saved_keys,
)
from wiki_cli.wikis import (
    get_active_client,
    get_active_wiki_name,
    get_wiki,
    list_wikis,
    remove_wiki,
    set_active_wiki,
    switch_wiki_flow,
)
from wiki_cli.pages import PagesManager

PROVIDERS = [
    ("openai", "OpenAI"),
    ("openrouter", "OpenRouter"),
    ("groq", "Groq"),
    ("mistral", "Mistral"),
    ("ollama", "Ollama (Local)"),
    ("ollama-cloud", "Ollama Cloud (Remote)"),
]

_PROVIDER_LABELS = dict(PROVIDERS)

_STATE_DIR = Path.home() / ".config" / "wiki-cli"
_LAST_CONFIG_FILE = _STATE_DIR / "last_config.json"

# ── ANSI ─────────────────────────────────────────────────────────────

R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
C = "\033[36m"
G = "\033[32m"
Y = "\033[33m"
M = "\033[35m"
W = "\033[97m"
X = "\033[90m"

PAD = 28


def _pad(text: str, width: int = PAD) -> str:
    raw = len(text.replace(R, '').replace(B, '').replace(D, '').replace(C, '').replace(G, '').replace(Y, '').replace(M, '').replace(W, '').replace(X, ''))
    return text + ' ' * max(width - raw, 0)


# ── State ────────────────────────────────────────────────────────────

def _load_last_config() -> dict[str, str] | None:
    if _LAST_CONFIG_FILE.exists():
        try:
            return json.loads(_LAST_CONFIG_FILE.read_text())
        except Exception:
            pass
    return None


def _save_last_config(provider: str, model: str) -> None:
    _STATE_DIR.mkdir(parents=True, exist_ok=True)
    _LAST_CONFIG_FILE.write_text(json.dumps({"provider": provider, "model": model}) + "\n")


# ── Setup ───────────────────────────────────────────────────────────

def _banner():
    print()
    print(f"  {B}wiki-ai{R}  {D}Wiki.js AI Assistant{R}")
    print(f"  {D}type /help for commands{R}")
    print()


def _config_status(config: AIConfig):
    label = _PROVIDER_LABELS.get(config.provider, config.provider)
    print(f"  {D}provider:{R}  {B}{label}{R}")
    print(f"  {D}model:{R}     {B}{config.model}{R}")
    print()


def _pick_provider() -> str:
    saved = list_saved_keys()
    saved_list = [(k, l) for k, l in PROVIDERS if k in saved]

    if saved_list:
        print(f"  {D}saved providers:{R}")
        print()
        for i, (_, label) in enumerate(saved_list, 1):
            print(f"    {C}{i}{R}    {label}")
        print(f"    {C}{len(saved_list) + 1}{R}    {D}add new{R}")
        print()

        while True:
            choice = input(f"  {C}>{R} ").strip() or "1"
            if choice.isdigit():
                idx = int(choice)
                if 1 <= idx <= len(saved_list):
                    return saved_list[idx - 1][0]
                if idx == len(saved_list) + 1:
                    break
            print(f"  {Y}invalid choice{R}")
    else:
        print(f"  {D}no saved providers{R}")
        print()

    print(f"  {D}available providers:{R}")
    print()
    for i, (_, label) in enumerate(PROVIDERS, 1):
        print(f"    {C}{i}{R}    {label}")
    print()

    while True:
        choice = input(f"  {C}>{R} ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(PROVIDERS):
            return PROVIDERS[int(choice) - 1][0]
        print(f"  {Y}invalid choice{R}")


def _enter_api_key(provider: str) -> str:
    if provider == "ollama":
        return "ollama"

    if provider == "ollama-cloud":
        saved = get_saved_key(provider)
        if saved:
            return saved
        return input(f"  {C}>{R} api key: ").strip()

    saved = get_saved_key(provider)
    if saved:
        masked = saved[:8] + "•••" + saved[-4:] if len(saved) > 12 else saved[:8] + "•••"
        print(f"  {D}saved key:{R}    {D}{masked}{R}")
        print(f"    {C}1{R}    use saved")
        print(f"    {C}2{R}    enter new")
        print()
        choice = input(f"  {C}>{R} ").strip() or "1"
        if choice == "1":
            return saved

    label = _PROVIDER_LABELS.get(provider, provider)
    print(f"  {D}{label} api key:{R}")
    while True:
        key = input(f"  {C}>{R} ").strip()
        if key:
            save_key(provider, key)
            print(f"  {G}saved{R}")
            return key
        print(f"  {Y}required{R}")


def _pick_model(provider: str, api_key: str) -> str:
    print(f"  {D}fetching models...{R}", end="", flush=True)
    models = fetch_models(provider, api_key)
    print()

    if not models:
        defaults = PROVIDER_DEFAULTS.get(provider, {})
        model = defaults.get("default_model", "gpt-4o")
        print(f"  {D}using default:{R} {model}")
        print()
        return model

    print(f"  {D}available models:{R}")
    print()
    col = 36
    for i in range(0, len(models), 2):
        row = models[i : i + 2]
        left = f"    {C}{i+1:>3}{R}  {row[0]:<{col}}"
        if len(row) > 1:
            left += f"  {C}{i+2:>3}{R}  {row[1]}"
        print(left)
    print()

    while True:
        choice = input(f"  {C}>{R} model [1]: ").strip() or "1"
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            picked = models[int(choice) - 1]
            print(f"  {G}selected:{R} {picked}")
            print()
            return picked
        print(f"  {Y}invalid choice{R}")


def _build_config() -> AIConfig:
    provider = _pick_provider()
    api_key = _enter_api_key(provider)
    model = _pick_model(provider, api_key)
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    _save_last_config(provider, model)
    return AIConfig(provider=provider, api_key=api_key, model=model, base_url=defaults.get("base_url", ""))


def _build_config_from_saved(provider: str, model: str) -> AIConfig:
    api_key = get_saved_key(provider) if provider != "ollama" else "ollama"
    defaults = PROVIDER_DEFAULTS.get(provider, {})
    return AIConfig(provider=provider, api_key=api_key, model=model, base_url=defaults.get("base_url", ""))


# ── Editor ──────────────────────────────────────────────────────────

class _Spinner:
    def __init__(self):
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        i = 0
        while not self._stop.is_set():
            sys.stdout.write(f"\r  {C}{frames[i % len(frames)]}{R} thinking... ")
            sys.stdout.flush()
            self._stop.wait(0.08)
            i += 1
        sys.stdout.write(f"\r{' ' * 30}\r")
        sys.stdout.flush()

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()
        self._thread.join()

def _open_editor(initial: str = "") -> str | None:
    """Open $EDITOR for multi-line input. Returns content or None on cancel."""
    editor = os.environ.get("EDITOR", "") or os.environ.get("VISUAL", "")
    if not editor:
        candidates = ["vi", "vim", "nano", "gedit", "notepad", "notepad++", "code"]
        for e in candidates:
            if shutil.which(e):
                editor = e
                break
    if not editor:
        print(f"  {Y}no editor found. set $EDITOR or install vim/notepad{R}")
        return None

    with tempfile.NamedTemporaryFile(suffix=".md", mode="w", delete=False) as f:
        f.write(initial)
        tmp = f.name

    try:
        subprocess.run([editor, tmp])
        content = Path(tmp).read_text().strip()
        return content if content else None
    finally:
        Path(tmp).unlink(missing_ok=True)


# ── Slash commands ──────────────────────────────────────────────────

def _cmd_providers(agent: WikiAgent) -> None:
    config = _build_config()
    agent.__init__(config)
    print()
    _config_status(config)


def _cmd_models(agent: WikiAgent) -> None:
    models = fetch_models(agent.config.provider, agent.config.api_key)
    if not models:
        print(f"  {Y}could not fetch models{R}")
        return

    print(f"  {D}available models:{R}")
    print()
    col = 36
    for i in range(0, len(models), 2):
        row = models[i : i + 2]
        left = f"    {C}{i+1:>3}{R}  {row[0]:<{col}}"
        if len(row) > 1:
            left += f"  {C}{i+2:>3}{R}  {row[1]}"
        print(left)
    print()

    while True:
        choice = input(f"  {C}>{R} model [q=cancel]: ").strip()
        if choice.lower() == "q":
            return
        if choice.isdigit() and 1 <= int(choice) <= len(models):
            new_model = models[int(choice) - 1]
            agent.config.model = new_model
            _save_last_config(agent.config.provider, new_model)
            print(f"  {G}selected:{R} {new_model}")
            print()
            return
        print(f"  {Y}invalid choice{R}")


def _cmd_remove_key(agent: WikiAgent) -> None:
    remove_key(agent.config.provider)
    print(f"  {G}key removed{R}")


def _cmd_help() -> None:
    print(f"""
  {B}commands:{R}
    {C}/edit{R}           open editor for multi-line input
    {C}/clear{R}          clear conversation history
    {C}/providers{R}      switch provider
    {C}/models{R}         switch model
    {C}/add-wiki{R}       add a new wiki profile (auto-switches + clears history)
    {C}/switch-wiki{R}    switch active wiki (interactive, or /switch-wiki <name> or --new)
    {C}/wikis{R}          list saved wikis
    {C}/remove-wiki{R}    remove a wiki profile (asks to confirm)
    {C}/remove-key{R}     remove saved api key
    {C}/help{R}           show this help
    {C}exit{R}            quit
""")


def _cmd_switch_wiki(agent: WikiAgent, arg: str) -> None:
    """Rebuild agent.wiki_client + agent.pages after switching."""
    new_client = switch_wiki_flow(arg)
    agent.wiki_client = new_client
    agent.pages = PagesManager(new_client)
    print()


def _cmd_wikis() -> None:
    data = list_wikis()
    active = None
    try:
        from wiki_cli.wikis import get_active_wiki_name
        active = get_active_wiki_name()
    except Exception:
        pass

    if not data:
        print(f"  {D}no saved wikis{R}\n")
        return

    print(f"  {D}saved wikis:{R}")
    print()
    for name in sorted(data):
        marker = f" {G}*{R}" if name == active else "  "
        print(f"  {marker} {B}{name}{R}  {data[name]['url']}")
    print()


def _cmd_remove_wiki(agent: WikiAgent, arg: str) -> None:
    target = arg.strip() or get_active_wiki_name()
    if not target:
        print(f"  {Y}no wiki specified and no active wiki{R}\n")
        return

    entry = wikis.get_wiki(target)
    if not entry:
        print(f"  {Y}wiki '{target}' not found{R}\n")
        return

    ans = input(f"  remove '{target}' ({entry['url']})? [y/n]: ").strip().lower()
    if ans not in ("y", "yes"):
        print(f"  {D}cancelled{R}\n")
        return

    wikis.remove_wiki(target)

    if get_active_wiki_name() == target:
        set_active_wiki(None)
        agent.wiki_client = None
        agent.pages = None
        remaining = wikis.list_wikis()
        if remaining:
            new_client = switch_wiki_flow()
            agent.wiki_client = new_client
            agent.pages = PagesManager(new_client)
        else:
            print(f"  {Y}no saved wikis. /switch-wiki to add one.{R}\n")

    print(f"  {G}removed → {target}{R}\n")


def _cmd_add_wiki(agent: WikiAgent) -> None:
    """Add a new wiki profile, set as active, rebuild agent, clear history."""
    from wiki_cli.client import WikiJSClient
    from wiki_cli.pages import PagesManager
    from wiki_cli.wikis import _prompt_new_profile, save_wiki, set_active_wiki

    name, url, api_key = _prompt_new_profile()
    save_wiki(name, url, api_key)
    set_active_wiki(name)

    agent.wiki_client = WikiJSClient(url=url, api_key=api_key)
    agent.pages = PagesManager(agent.wiki_client)
    agent.clear_history()

    print(f"  {G}saved → active: {name} (history cleared){R}\n")


# ── Main ────────────────────────────────────────────────────────────

def ai_mode() -> None:
    _banner()

    try:
        try:
            client = get_active_client()
        except WikiJSError:
            print(f"  {D}no active wiki. let's configure one.{R}\n")
            client = switch_wiki_flow()

        last = _load_last_config()
        if last and get_saved_key(last.get("provider", "")):
            provider = last["provider"]
            model = last["model"]
            config = _build_config_from_saved(provider, model)
            agent = WikiAgent(config=config, wiki_client=client)
        else:
            config = _build_config()
            agent = WikiAgent(config=config, wiki_client=client)

    except WikiJSError as exc:
        print(f"  {Y}error: {exc}{R}", file=sys.stderr)
        sys.exit(1)
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    except Exception as exc:
        print(f"  {Y}error: {exc}{R}", file=sys.stderr)
        sys.exit(1)

    _config_status(config)

    while True:
        try:
            prompt = input(f"  {C}>{R} ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not prompt:
            continue

        if prompt == "/help":
            _cmd_help()
            continue
        if prompt == "/clear":
            agent.clear_history()
            print(f"  {G}history cleared{R}\n")
            continue
        if prompt == "/edit":
            content = _open_editor()
            if content:
                prompt = content
            else:
                continue
        if prompt == "/providers":
            _cmd_providers(agent)
            continue
        if prompt == "/models":
            _cmd_models(agent)
            continue
        if prompt == "/remove-key":
            _cmd_remove_key(agent)
            continue
        if prompt == "/add-wiki":
            try:
                _cmd_add_wiki(agent)
            except WikiJSError as exc:
                print(f"  {Y}{exc}{R}\n")
            continue
        if prompt.startswith("/switch-wiki"):
            arg = prompt[len("/switch-wiki"):].strip()
            try:
                _cmd_switch_wiki(agent, arg)
            except WikiJSError as exc:
                print(f"  {Y}{exc}{R}\n")
            continue
        if prompt == "/wikis":
            _cmd_wikis()
            continue
        if prompt.startswith("/remove-wiki"):
            arg = prompt[len("/remove-wiki"):].strip()
            try:
                _cmd_remove_wiki(agent, arg)
            except WikiJSError as exc:
                print(f"  {Y}{exc}{R}\n")
            continue
        if prompt.lower() in ("exit", "quit", "q"):
            break

        try:
            agent.quiet = True
            spinner = _Spinner()
            spinner.start()
            try:
                response = agent.run(prompt)
            finally:
                spinner.stop()
                agent.quiet = False
            print(f"\n{response}\n")
        except Exception as exc:
            print(f"  {Y}error: {exc}{R}\n")
