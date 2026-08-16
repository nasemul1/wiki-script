from ai_cli.success import (
    test_ai_remove_wiki_unknown_name_no_change as _unknown,
)
from ai_cli.success import (
    test_ai_remove_wiki_cancels_on_n as _cancel,
)
from ai_cli.success import (
    test_ai_remove_wiki_succeeds_on_y as _ok,
)
from ai_cli.success import (
    test_ai_remove_wiki_default_target_is_active as _default,
)
from ai_cli.success import (
    test_ai_remove_wiki_accepts_yes as _yes,
)


def test_unknown(capsys, tmp_wiki_config):
    _unknown(capsys, tmp_wiki_config)


def test_cancel(capsys, tmp_wiki_config):
    _cancel(capsys, tmp_wiki_config)


def test_ok(capsys, tmp_wiki_config):
    _ok(capsys, tmp_wiki_config)


def test_default(capsys, tmp_wiki_config):
    _default(capsys, tmp_wiki_config)


def test_yes(capsys, tmp_wiki_config):
    _yes(capsys, tmp_wiki_config)


from ai_cli.success import test_ai_add_wiki_saves_profile as _add_save
from ai_cli.success import test_ai_add_wiki_clears_history as _add_clear
from ai_cli.success import test_ai_add_wiki_duplicate_name_no_change as _add_dup


def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    _add_save(capsys, tmp_wiki_config)


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    _add_clear(capsys, tmp_wiki_config)


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    _add_dup(capsys, tmp_wiki_config)
