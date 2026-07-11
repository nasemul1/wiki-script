from clone_page.success import test_clone_success as _success
from clone_page.success import test_clone_empty_path as _empty_path
from clone_page.success import test_clone_invalid_id as _invalid


def test_clone_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_clone_empty_path(mock_manager, capsys):
    _empty_path(mock_manager, capsys)


def test_clone_invalid_id(mock_manager, capsys):
    _invalid(mock_manager, capsys)
