from export_page.success import test_export_success as _success
from export_page.success import test_export_default_filename as _default
from export_page.success import test_export_invalid_id as _invalid


def test_export_success(mock_manager, capsys, tmp_path):
    _success(mock_manager, capsys, tmp_path)


def test_export_default_filename(mock_manager, capsys, tmp_path):
    _default(mock_manager, capsys, tmp_path)


def test_export_invalid_id(mock_manager, capsys):
    _invalid(mock_manager, capsys)
