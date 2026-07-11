from fetch_page.success import test_fetch_by_id as _by_id
from fetch_page.success import test_fetch_by_path as _by_path
from fetch_page.success import test_fetch_default_choice_is_id as _default_choice
from fetch_page.validation import test_fetch_invalid_id as _invalid_id
from fetch_page.validation import test_fetch_path_required as _path_required


def test_fetch_by_id(mock_manager, capsys):
    _by_id(mock_manager, capsys)


def test_fetch_by_path(mock_manager, capsys):
    _by_path(mock_manager, capsys)


def test_fetch_default_choice_is_id(mock_manager, capsys):
    _default_choice(mock_manager, capsys)


def test_fetch_invalid_id(mock_manager, capsys):
    _invalid_id(mock_manager, capsys)


def test_fetch_path_required(mock_manager, capsys):
    _path_required(mock_manager, capsys)
