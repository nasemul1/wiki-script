from view_revision.success import test_view_revision_success as _success
from view_revision.success import test_view_revision_invalid_page_id as _invalid_page
from view_revision.success import test_view_revision_invalid_version_id as _invalid_ver


def test_view_revision_success(mock_manager, capsys):
    _success(mock_manager, capsys)


def test_view_revision_invalid_page_id(mock_manager, capsys):
    _invalid_page(mock_manager, capsys)


def test_view_revision_invalid_version_id(mock_manager, capsys):
    _invalid_ver(mock_manager, capsys)
