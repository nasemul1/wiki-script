from restore_revision.success import test_restore_success as _success
from restore_revision.success import test_restore_cancelled as _cancelled
from restore_revision.success import test_restore_invalid_page_id as _invalid_page
from restore_revision.success import test_restore_invalid_version_id as _invalid_ver


def test_restore_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_restore_cancelled(mock_manager, capsys):
    _cancelled(mock_manager, capsys)


def test_restore_invalid_page_id(mock_manager, capsys):
    _invalid_page(mock_manager, capsys)


def test_restore_invalid_version_id(mock_manager, capsys):
    _invalid_ver(mock_manager, capsys)
