from cli_wikis.success import (
    test_manage_wikis_menu_back_returns_current as _back,
)
from cli_wikis.success import (
    test_manage_wikis_menu_list_shows_active_marker as _list,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_cancels_on_n as _cancel,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_succeeds_on_y as _ok,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_active_rebuilds_via_switch as _rebuild,
)
from cli_wikis.success import (
    test_manage_wikis_menu_remove_active_no_remaining as _no_remaining,
)
from cli_wikis.success import (
    test_remove_wiki_flow_unknown_name as _unknown,
)
from cli_wikis.success import (
    test_remove_wiki_flow_cancel_option as _cancel_opt,
)


def test_back(tmp_wiki_config, capsys):
    _back(tmp_wiki_config, capsys)


def test_list(tmp_wiki_config, capsys):
    _list(tmp_wiki_config, capsys)


def test_cancel(tmp_wiki_config, capsys):
    _cancel(tmp_wiki_config, capsys)


def test_ok(tmp_wiki_config, capsys):
    _ok(tmp_wiki_config, capsys)


def test_rebuild(tmp_wiki_config, capsys):
    _rebuild(tmp_wiki_config, capsys)


def test_no_remaining(tmp_wiki_config, capsys):
    _no_remaining(tmp_wiki_config, capsys)


def test_unknown(tmp_wiki_config, capsys):
    _unknown(tmp_wiki_config, capsys)


def test_cancel_opt(tmp_wiki_config, capsys):
    _cancel_opt(tmp_wiki_config, capsys)
