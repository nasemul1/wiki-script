from main_menu.success import test_menu_exit as _exit
from main_menu.success import test_menu_invalid_option as _invalid
from main_menu.success import test_menu_dispatches_handler as _dispatch
from main_menu.success import test_menu_handles_error as _error
from main_menu.success import test_menu_option_18_label as _label
from main_menu.success import test_menu_manage_wikis_rebuilds as _manage


def test_menu_exit(capsys, tmp_wiki_config):
    _exit(capsys, tmp_wiki_config)


def test_menu_invalid_option(capsys, tmp_wiki_config):
    _invalid(capsys, tmp_wiki_config)


def test_menu_dispatches_handler(capsys, tmp_wiki_config):
    _dispatch(capsys, tmp_wiki_config)


def test_menu_handles_error(capsys, tmp_wiki_config):
    _error(capsys, tmp_wiki_config)


def test_menu_option_18_label(capsys, tmp_wiki_config):
    _label(capsys, tmp_wiki_config)


def test_menu_manage_wikis_rebuilds(capsys, tmp_wiki_config):
    _manage(capsys, tmp_wiki_config)
