from list_pages.success import test_list_success as _success
from list_pages.success import test_list_empty as _empty
from list_pages.success import test_list_filter_tag as _filter
from list_pages.success import test_list_filter_no_match as _no_match
from list_pages.success import test_list_sort_by_path as _sort


def test_list_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_list_empty(mock_manager, capsys):
    _empty(mock_manager, capsys)


def test_list_filter_tag(mock_manager, capsys):
    _filter(mock_manager, capsys)


def test_list_filter_no_match(mock_manager, capsys):
    _no_match(mock_manager, capsys)


def test_list_sort_by_path(mock_manager, capsys):
    _sort(mock_manager, capsys)
