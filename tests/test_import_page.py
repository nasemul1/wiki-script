from import_page.success import test_import_with_frontmatter as _frontmatter
from import_page.success import test_import_without_frontmatter as _plain
from import_page.success import test_import_file_not_found as _not_found
from import_page.success import test_import_empty_filename as _empty


def test_import_with_frontmatter(mock_manager, capsys, tmp_path):
    _frontmatter(mock_manager, capsys, tmp_path)


def test_import_without_frontmatter(mock_manager, capsys, tmp_path):
    _plain(mock_manager, capsys, tmp_path)


def test_import_file_not_found(mock_manager, capsys):
    _not_found(mock_manager, capsys)


def test_import_empty_filename(mock_manager, capsys):
    _empty(mock_manager, capsys)
