from update_page.success import test_replace_content as _replace
from update_page.success import test_append_content as _append
from update_page.success import test_keep_content_unchanged as _keep
from update_page.success import test_update_with_new_tags as _tags
from update_page.validation import test_update_invalid_id as _invalid_id


def test_replace_content(mock_manager, capsys):
    _replace(mock_manager, capsys)


def test_append_content(mock_manager, capsys):
    _append(mock_manager, capsys)


def test_keep_content_unchanged(mock_manager, capsys):
    _keep(mock_manager, capsys)


def test_update_with_new_tags(mock_manager, capsys):
    _tags(mock_manager, capsys)


def test_update_invalid_id(mock_manager, capsys):
    _invalid_id(mock_manager, capsys)
