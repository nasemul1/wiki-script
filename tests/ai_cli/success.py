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
