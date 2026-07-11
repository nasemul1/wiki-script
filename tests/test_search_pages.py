from search_pages.success import test_search_success as _success
from search_pages.success import test_search_empty_query as _empty
from search_pages.success import test_search_no_results as _no_results
from search_pages.success import test_search_with_locale as _locale
from search_pages.success import test_search_with_tag_filter as _filter


def test_search_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_search_empty_query(mock_manager, capsys):
    _empty(mock_manager, capsys)


def test_search_no_results(mock_manager, capsys):
    _no_results(mock_manager, capsys)


def test_search_with_locale(mock_manager, capsys):
    _locale(mock_manager, capsys)


def test_search_with_tag_filter(mock_manager, capsys):
    _filter(mock_manager, capsys)
