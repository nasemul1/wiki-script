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
from ai_cli.success import (
    test_ai_add_wiki_dispatch_catches_duplicate as _add_dispatch,
)


def test_ai_add_wiki_saves_profile(capsys, tmp_wiki_config):
    _add_save(capsys, tmp_wiki_config)


def test_ai_add_wiki_clears_history(capsys, tmp_wiki_config):
    _add_clear(capsys, tmp_wiki_config)


def test_ai_add_wiki_duplicate_name_no_change(capsys, tmp_wiki_config):
    _add_dup(capsys, tmp_wiki_config)


def test_ai_add_wiki_dispatch_catches_duplicate(capsys, tmp_wiki_config):
    _add_dispatch(capsys, tmp_wiki_config)


from ai_cli.success import test_agent_saves_session_after_run as _agent_save
from ai_cli.success import test_agent_clear_history_deletes_session as _agent_clear
from ai_cli.success import test_agent_warns_on_80pct_context as _agent_warn


def test_agent_saves_session_after_run(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_save(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_agent_clear_history_deletes_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_clear(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_agent_warns_on_80pct_context(capsys, tmp_wiki_config, tmp_sessions_dir):
    _agent_warn(capsys, tmp_wiki_config, tmp_sessions_dir)


from ai_cli.success import test_ai_startup_resumes_existing_session as _resume
from ai_cli.success import test_ai_clear_wipes_session_file as _clear_wipe
from ai_cli.success import test_switch_wiki_saves_outgoing_session as _switch_save
from ai_cli.success import test_switch_wiki_updates_wiki_name as _switch_name
from ai_cli.success import test_switch_wiki_loads_incoming_session as _switch_load
from ai_cli.success import test_add_wiki_saves_outgoing_session as _add_save_out


def test_ai_startup_resumes_existing_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _resume(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_ai_clear_wipes_session_file(tmp_wiki_config, tmp_sessions_dir):
    _clear_wipe(tmp_wiki_config, tmp_sessions_dir)


def test_switch_wiki_saves_outgoing_session(tmp_wiki_config, tmp_sessions_dir):
    _switch_save(tmp_wiki_config, tmp_sessions_dir)


def test_switch_wiki_updates_wiki_name(tmp_wiki_config):
    _switch_name(tmp_wiki_config)


def test_switch_wiki_loads_incoming_session(capsys, tmp_wiki_config, tmp_sessions_dir):
    _switch_load(capsys, tmp_wiki_config, tmp_sessions_dir)


def test_add_wiki_saves_outgoing_session(tmp_wiki_config, tmp_sessions_dir):
    _add_save_out(tmp_wiki_config, tmp_sessions_dir)
