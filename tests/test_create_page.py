from create_page.success import test_valid_inputs as _valid
from create_page.success import test_all_fields_set_correctly as _all_fields
from create_page.validation import test_path_required as _path_req
from create_page.validation import test_title_required as _title_req
from create_page.defaults import test_uses_default_values_when_blanks as _defaults
from create_page.defaults import test_empty_tag_string_becomes_empty_list as _empty_tags


def test_valid_inputs(mock_manager, capsys):
    _valid(mock_manager, capsys)


def test_all_fields_set_correctly(mock_manager):
    _all_fields(mock_manager)


def test_path_required(mock_manager, capsys):
    _path_req(mock_manager, capsys)


def test_title_required(mock_manager, capsys):
    _title_req(mock_manager, capsys)


def test_uses_default_values_when_blanks(mock_manager, capsys):
    _defaults(mock_manager, capsys)


def test_empty_tag_string_becomes_empty_list(mock_manager):
    _empty_tags(mock_manager)
