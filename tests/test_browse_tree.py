from browse_tree.success import test_browse_tree_structure as _structure
from browse_tree.success import test_browse_empty as _empty
from browse_tree.success import test_browse_view_page as _view
from browse_tree.success import test_browse_skip_view as _skip


def test_browse_tree_structure(mock_manager, capsys):
    _structure(mock_manager, capsys)


def test_browse_empty(mock_manager, capsys):
    _empty(mock_manager, capsys)


def test_browse_view_page(mock_manager, capsys):
    _view(mock_manager, capsys)


def test_browse_skip_view(mock_manager, capsys):
    _skip(mock_manager, capsys)
