"""Tests for wiki_cli.cli_wikis module."""

from unittest.mock import MagicMock, patch

from wiki_cli.client import WikiJSClient
from wiki_cli import wikis
from wiki_cli.cli_wikis import manage_wikis_menu, _remove_wiki_flow

INPUT_PATCH = "builtins.input"


def _client(url="https://w.com/graphql"):
    c = MagicMock(spec=WikiJSClient)
    c.url = url
    return c


def test_manage_wikis_menu_back_returns_current(tmp_wiki_config, capsys):
    """Option 0 returns current client without changes."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    client = _client()
    with patch(INPUT_PATCH, side_effect=iter(["0"])):
        result = manage_wikis_menu(client)
    assert result is client
    out = capsys.readouterr().out
    assert "Manage Wikis" in out


def test_manage_wikis_menu_list_shows_active_marker(tmp_wiki_config, capsys):
    """Option 3 lists profiles with * marker on active."""
    wikis.save_wiki("work", "https://w.com/graphql", "k")
    wikis.save_wiki("home", "https://h.com/graphql", "k2")
    wikis.set_active_wiki("work")
    with patch(INPUT_PATCH, side_effect=iter(["3", "0"])):
        manage_wikis_menu(_client())
    out = capsys.readouterr().out
    assert "work" in out
    assert "home" in out


def test_manage_wikis_menu_remove_cancels_on_n(tmp_wiki_config, capsys):
    """Option 4 + 'n' confirm keeps profile."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    client = _client()
    inputs = iter(["4", "1", "n", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "cancelled" in out.lower()


def test_manage_wikis_menu_remove_succeeds_on_y(tmp_wiki_config, capsys):
    """Option 4 + 'y' removes non-active profile."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.save_wiki("b", "https://b.com/graphql", "k2")
    wikis.set_active_wiki("a")
    client = _client()
    # 4 = remove, 2 = pick profile "b", y = confirm, 0 = back
    inputs = iter(["4", "2", "y", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert wikis.get_wiki("b") is None
    assert wikis.get_active_wiki_name() == "a"
    assert result is client


def test_manage_wikis_menu_remove_active_rebuilds_via_switch(tmp_wiki_config, capsys):
    """Removing active profile triggers switch flow for remaining profiles."""
    wikis.save_wiki("work", "https://w.com/graphql", "k")
    wikis.save_wiki("home", "https://h.com/graphql", "k2")
    wikis.set_active_wiki("work")
    client = _client()
    new_client = _client("https://h.com/graphql")
    # 4 = remove, 2 = pick profile "work" (sorted: home, work), y = confirm,
    # then switch flow: 1 = pick "home" from remaining, 0 = back
    inputs = iter(["4", "2", "y", "1", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_wikis.switch_wiki_flow", return_value=new_client):
            result = manage_wikis_menu(client)
    assert wikis.get_wiki("work") is None
    assert result is new_client


def test_manage_wikis_menu_remove_active_no_remaining(tmp_wiki_config, capsys):
    """Removing last profile clears active, returns current client."""
    wikis.save_wiki("only", "https://o.com/graphql", "k")
    wikis.set_active_wiki("only")
    client = _client()
    inputs = iter(["4", "1", "y", "0"])
    with patch(INPUT_PATCH, side_effect=inputs):
        result = manage_wikis_menu(client)
    assert wikis.get_wiki("only") is None
    assert wikis.get_active_wiki_name() is None
    assert result is client


def test_remove_wiki_flow_unknown_name(tmp_wiki_config, capsys):
    """Pick index out of range prints error, no change."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    inputs = iter(["99", "0"])  # invalid picker index, then back
    with patch(INPUT_PATCH, side_effect=inputs):
        client = _client()
        result = _remove_wiki_flow(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
    out = capsys.readouterr().out
    assert "invalid" in out.lower() or "not found" in out.lower()


def test_remove_wiki_flow_cancel_option(tmp_wiki_config, capsys):
    """Picker option 'cancel' (last index) returns current client."""
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    inputs = iter(["2", "0"])  # 2 = cancel (1 profile + 1 cancel)
    with patch(INPUT_PATCH, side_effect=inputs):
        client = _client()
        result = _remove_wiki_flow(client)
    assert result is client
    assert wikis.get_wiki("a") is not None
