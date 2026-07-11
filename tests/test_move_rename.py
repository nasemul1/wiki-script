from move_rename.success import test_move_success as _success
from move_rename.success import test_move_no_changes as _no_changes
from move_rename.success import test_move_cancelled as _cancelled
from move_rename.success import test_move_invalid_id as _invalid


def test_move_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_move_no_changes(mock_manager, capsys):
    _no_changes(mock_manager, capsys)


def test_move_cancelled(mock_manager, capsys):
    _cancelled(mock_manager, capsys)


def test_move_invalid_id(mock_manager, capsys):
    _invalid(mock_manager, capsys)
