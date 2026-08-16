"""Tests for AI assistant slash command handlers."""

from unittest.mock import patch, MagicMock

from wiki_cli import wikis
from wiki_cli.ai.cli import _cmd_remove_wiki
from wiki_cli.pages import PagesManager

INPUT_PATCH = "builtins.input"


def _agent():
    a = MagicMock()
    a.wiki_client = MagicMock()
    a.wiki_client.url = "https://w.com/graphql"
    a.pages = MagicMock(spec=PagesManager)
    return a


def test_ai_remove_wiki_unknown_name_no_change(capsys, tmp_wiki_config):
    """Unknown name prints error, no state change."""
    wikis.save_wiki("real", "https://r.com/graphql", "k")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["ghost"])):
        _cmd_remove_wiki(agent, "ghost")
    assert wikis.get_wiki("real") is not None
    assert wikis.get_wiki("ghost") is None
    out = capsys.readouterr().out
    assert "not found" in out.lower()


def test_ai_remove_wiki_cancels_on_n(capsys, tmp_wiki_config):
    """User types 'n' to confirm — no removal."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["n"])):
        _cmd_remove_wiki(agent, "a")
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_ai_remove_wiki_succeeds_on_y(capsys, tmp_wiki_config):
    """User types 'y' — non-active profile removed."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["y"])):
        _cmd_remove_wiki(agent, "b")
    assert wikis.get_wiki("b") is None
    assert wikis.get_active_wiki_name() == "a"
    out = capsys.readouterr().out
    assert "removed" in out.lower()


def test_ai_remove_wiki_default_target_is_active(capsys, tmp_wiki_config):
    """Empty arg defaults to active wiki."""
    wikis.save_wiki("active", "https://a.com/graphql", "k")
    wikis.set_active_wiki("active")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["n"])):
        _cmd_remove_wiki(agent, "")
    assert wikis.get_wiki("active") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_ai_remove_wiki_accepts_yes(capsys, tmp_wiki_config):
    """User types 'yes' (full word) — confirm succeeds."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    agent = _agent()
    with patch(INPUT_PATCH, side_effect=iter(["yes"])):
        _cmd_remove_wiki(agent, "b")
    assert wikis.get_wiki("b") is None


def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    """Verify profile saved, set active, agent rebuilt."""
    from wiki_cli.ai.cli import _cmd_add_wiki
    from wiki_cli.pages import PagesManager

    agent = MagicMock()
    inputs = iter(["prod", "https://prod.com/graphql", "secret"])
    with patch(INPUT_PATCH, side_effect=inputs):
        _cmd_add_wiki(agent)
    assert wikis.get_wiki("prod") == {
        "url": "https://prod.com/graphql",
        "api_key": "secret",
    }
    assert wikis.get_active_wiki_name() == "prod"
    assert agent.wiki_client is not None
    assert agent.wiki_client.url == "https://prod.com/graphql"
    assert agent.wiki_client.api_key == "secret"
    assert isinstance(agent.pages, PagesManager)
    agent.clear_history.assert_called_once()
    out = capsys.readouterr().out
    assert "saved → active: prod" in out
    assert "history cleared" in out
    print(f"\n  [AI] /add-wiki saves + auto-switches + clears history")


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    """Verify conversation history cleared after add."""
    from wiki_cli.ai.cli import _cmd_add_wiki

    agent = MagicMock()
    inputs = iter(["w", "https://w.com/graphql", "k"])
    with patch(INPUT_PATCH, side_effect=inputs):
        _cmd_add_wiki(agent)
    agent.clear_history.assert_called_once()
    print(f"\n  [AI] /add-wiki clears conversation history")


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    """Duplicate name raises WikiJSError; active not set, agent not rebuilt."""
    import pytest
    from wiki_cli import WikiJSError
    from wiki_cli.ai.cli import _cmd_add_wiki

    wikis.save_wiki("existing", "https://e.com/graphql", "k1")
    agent = MagicMock()
    original_client = agent.wiki_client
    inputs = iter(["existing", "https://other.com/graphql", "k2"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with pytest.raises(WikiJSError):
            _cmd_add_wiki(agent)
    assert wikis.get_active_wiki_name() is None
    assert agent.wiki_client is original_client
    print(f"\n  [AI] /add-wiki duplicate name raises and preserves state")


def test_ai_add_wiki_dispatch_catches_duplicate(capsys, tmp_wiki_config):
    """Dispatch loop must catch WikiJSError from /add-wiki and continue."""
    from wiki_cli.ai.cli import ai_mode
    from wiki_cli.ai.config import AIConfig

    wikis.save_wiki("existing", "https://e.com/graphql", "k1")

    fake = MagicMock()
    fake.url = "https://e.com/graphql"
    cfg = AIConfig(provider="openrouter", api_key="x", model="m", base_url="")

    inputs = iter([
        "/add-wiki",
        "existing",
        "https://other.com/graphql",
        "k2",
        "exit",
    ])
    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.ai.cli.get_active_client", return_value=fake):
            with patch("wiki_cli.ai.cli._load_last_config", return_value=None):
                with patch("wiki_cli.ai.cli.get_saved_key", return_value=""):
                    with patch("wiki_cli.ai.cli._build_config", return_value=cfg):
                        with patch("wiki_cli.ai.cli.WikiAgent"):
                            ai_mode()
    out = capsys.readouterr().out
    assert "already exists" in out
    assert "wiki-ai" in out
    print(f"\n  [AI] /add-wiki dispatch catches WikiJSError and continues")


def test_agent_saves_session_after_run(capsys, tmp_wiki_config, tmp_sessions_dir):
    """WikiAgent.run() persists the messages list to disk."""
    from wiki_cli.ai.agent import WikiAgent
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import has_session, load_session

    agent = WikiAgent(
        config=AIConfig(provider="openrouter", api_key="x", model="m", base_url=""),
        wiki_client=MagicMock(),
        wiki_name="work",
    )
    with patch.object(agent, "_run_openai", return_value="ok"):
        agent.run("hi")
    assert has_session("work")
    loaded = load_session("work")
    assert loaded["messages"] == agent.messages


def test_agent_clear_history_deletes_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    """WikiAgent.clear_history() also deletes the session file."""
    from wiki_cli.ai.agent import WikiAgent
    from wiki_cli.ai.config import AIConfig
    from wiki_cli.ai.sessions import has_session, save_session

    agent = WikiAgent(
        config=AIConfig(provider="openrouter", api_key="x", model="m", base_url=""),
        wiki_client=MagicMock(),
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
        wiki_client=MagicMock(),
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
    output = str(mock_stderr.write.call_args_list[0])
    assert "approaching" in output.lower() or "warning" in output.lower()
