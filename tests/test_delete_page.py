from delete_page.success import test_delete_success as _success
from delete_page.success import test_delete_cancelled as _cancelled
from delete_page.validation import test_delete_invalid_id as _invalid


def test_delete_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_delete_cancelled(mock_manager, capsys):
    _cancelled(mock_manager, capsys)


def test_delete_invalid_id(mock_manager, capsys):
    _invalid(mock_manager, capsys)
