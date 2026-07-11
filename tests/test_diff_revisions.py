from diff_revisions.success import test_diff_success as _success
from diff_revisions.success import test_diff_no_changes as _no_changes
from diff_revisions.success import test_diff_invalid_page_id as _invalid_page
from diff_revisions.success import test_diff_invalid_version_id as _invalid_ver


def test_diff_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_diff_no_changes(mock_manager, capsys):
    _no_changes(mock_manager, capsys)


def test_diff_invalid_page_id(mock_manager, capsys):
    _invalid_page(mock_manager, capsys)


def test_diff_invalid_version_id(mock_manager, capsys):
    _invalid_ver(mock_manager, capsys)
