import json
from pathlib import Path
from unittest.mock import patch

import pytest

from wiki_cli import wikis
from wiki_cli.exceptions import WikiJSError


@pytest.fixture
def tmp_config(tmp_path, monkeypatch):
    f1 = tmp_path / "wikis.json"
    f2 = tmp_path / "active_wiki.txt"
    monkeypatch.setattr(wikis, "WIKIS_FILE", f1)
    monkeypatch.setattr(wikis, "ACTIVE_FILE", f2)
    return f1, f2


def test_list_wikis_empty(tmp_config):
    assert wikis.list_wikis() == {}


def test_save_and_get_wiki(tmp_config):
    wikis.save_wiki("work", "https://w.work.com/graphql", "secret1")
    assert wikis.get_wiki("work") == {
        "url": "https://w.work.com/graphql",
        "api_key": "secret1",
    }
    assert "work" in wikis.list_wikis()


def test_save_wiki_creates_file_with_mode_0600(tmp_config):
    f1, _ = tmp_config
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    assert f1.exists()
    assert oct(f1.stat().st_mode & 0o777) == "0o600"


def test_save_wiki_rejects_duplicate_name_case_insensitive(tmp_config):
    wikis.save_wiki("Work", "https://w.com/graphql", "k")
    with pytest.raises(WikiJSError, match="already exists"):
        wikis.save_wiki("work", "https://other.com/graphql", "k2")


def test_save_wiki_rejects_duplicate_url(tmp_config):
    wikis.save_wiki("a", "https://same.com/graphql", "k")
    with pytest.raises(WikiJSError, match="url already saved"):
        wikis.save_wiki("b", "https://same.com/graphql", "k2")


def test_save_wiki_rejects_empty_name(tmp_config):
    with pytest.raises(WikiJSError, match="name required"):
        wikis.save_wiki("  ", "https://x.com/graphql", "k")


def test_save_wiki_rejects_name_with_whitespace(tmp_config):
    with pytest.raises(WikiJSError, match="no spaces"):
        wikis.save_wiki("my work", "https://x.com/graphql", "k")


def test_save_wiki_rejects_url_without_scheme(tmp_config):
    with pytest.raises(WikiJSError, match="http"):
        wikis.save_wiki("a", "wikijs.com/graphql", "k")


def test_save_wiki_rejects_empty_key(tmp_config):
    with pytest.raises(WikiJSError, match="api key required"):
        wikis.save_wiki("a", "https://x.com/graphql", "  ")


def test_remove_wiki(tmp_config):
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.remove_wiki("a")
    assert wikis.get_wiki("a") is None


def test_remove_wiki_missing_is_noop(tmp_config):
    wikis.remove_wiki("ghost")


def test_set_and_get_active_wiki(tmp_config):
    assert wikis.get_active_wiki_name() is None
    wikis.set_active_wiki("work")
    assert wikis.get_active_wiki_name() == "work"


def test_active_file_permissions(tmp_config):
    _, f2 = tmp_config
    wikis.set_active_wiki("x")
    assert oct(f2.stat().st_mode & 0o777) == "0o600"


def test_set_active_wiki_none_clears(tmp_config):
    wikis.set_active_wiki("a")
    wikis.set_active_wiki(None)
    assert wikis.get_active_wiki_name() is None


def test_load_corrupt_json_returns_empty(tmp_config):
    f1, _ = tmp_config
    f1.write_text("{not json")
    assert wikis.list_wikis() == {}


def test_get_active_client_raises_when_none(tmp_config):
    with pytest.raises(WikiJSError, match="no active wiki"):
        wikis.get_active_client()


def test_get_active_client_raises_when_active_missing(tmp_config):
    _, f2 = tmp_config
    f2.write_text("ghost")
    with pytest.raises(WikiJSError, match="no active wiki"):
        wikis.get_active_client()


def test_get_active_client_returns_client(tmp_config):
    wikis.save_wiki("w", "https://w.com/graphql", "k")
    wikis.set_active_wiki("w")
    client = wikis.get_active_client()
    assert client.url == "https://w.com/graphql"
    assert client.api_key == "k"


def test_switch_wiki_flow_jumps_to_named(tmp_config, capsys):
    wikis.save_wiki("work", "https://work.com/graphql", "wk")
    client = wikis.switch_wiki_flow("work")
    assert client.url == "https://work.com/graphql"
    assert wikis.get_active_wiki_name() == "work"
    out = capsys.readouterr().out
    assert "work" in out


def test_switch_wiki_flow_named_missing_no_state_change(tmp_config, capsys):
    wikis.save_wiki("a", "https://a.com/graphql", "k")
    wikis.set_active_wiki("a")
    with pytest.raises(WikiJSError):
        wikis.switch_wiki_flow("ghost")
    assert wikis.get_active_wiki_name() == "a"


def test_switch_wiki_flow_new_creates_profile(tmp_config):
    inputs = iter(["work", "https://work.com/graphql", "secret"])
    with patch("builtins.input", side_effect=inputs):
        with patch("wiki_cli.wikis.getpass.getpass", return_value="secret"):
            client = wikis.switch_wiki_flow("--new")
    assert wikis.get_active_wiki_name() == "work"
    assert client.url == "https://work.com/graphql"
    assert wikis.get_wiki("work")["api_key"] == "secret"


def test_switch_wiki_flow_interactive_picks_existing(tmp_config):
    wikis.save_wiki("a", "https://a.com/graphql", "ka")
    inputs = iter(["1"])
    with patch("builtins.input", side_effect=inputs):
        client = wikis.switch_wiki_flow()
    assert client.url == "https://a.com/graphql"
    assert wikis.get_active_wiki_name() == "a"
