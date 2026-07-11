from view_history.success import test_view_history_success as _success
from view_history.success import test_view_history_empty as _empty
from view_history.success import test_view_history_invalid_id as _invalid


def test_view_history_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_view_history_empty(mock_manager, capsys):
    _empty(mock_manager, capsys)


def test_view_history_invalid_id(mock_manager, capsys):
    _invalid(mock_manager, capsys)
