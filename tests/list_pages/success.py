from unittest.mock import patch

from wiki_cli.cli_pages import list_pages
from wiki_cli.models import Page

INPUT_PATCH = "builtins.input"


def test_list_success(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="a", title="Alpha", tags=["wiki"]),
        Page(id=2, path="b", title="Beta", tags=["setup"]),
    ]
    inputs = iter(["1", "", "q"])

    with patch(INPUT_PATCH, side_effect=inputs):
        list_pages(mock_manager)

    mock_manager.list_all.assert_called_once_with(order_by="TITLE")
    output = capsys.readouterr().out
    assert "Total: 2 page(s)" in output
    assert "Alpha" in output
    print(f"\n  [LIST] 2 pages listed")


def test_list_empty(mock_manager, capsys):
    mock_manager.list_all.return_value = []
    inputs = iter(["1", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        list_pages(mock_manager)

    output = capsys.readouterr().out
    assert "No pages found." in output
    print(f"\n  [LIST] Empty result")


def test_list_filter_tag(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="a", title="Alpha", tags=["wiki"]),
        Page(id=2, path="b", title="Beta", tags=["setup"]),
        Page(id=3, path="c", title="Gamma", tags=["wiki", "guide"]),
    ]
    inputs = iter(["1", "wiki", "q"])

    with patch(INPUT_PATCH, side_effect=inputs):
        list_pages(mock_manager)

    output = capsys.readouterr().out
    assert "Alpha" in output
    assert "Gamma" in output
    assert "Beta" not in output
    print(f"\n  [LIST] Filtered by tag 'wiki'")


def test_list_filter_no_match(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="a", title="Alpha", tags=["wiki"]),
    ]
    inputs = iter(["1", "nonexistent", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        list_pages(mock_manager)

    output = capsys.readouterr().out
    assert "No pages found with tag 'nonexistent'." in output
    print(f"\n  [LIST] Filter no match")


def test_list_sort_by_path(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="a", title="A"),
    ]
    inputs = iter(["2", "", "q"])

    with patch(INPUT_PATCH, side_effect=inputs):
        list_pages(mock_manager)

    mock_manager.list_all.assert_called_once_with(order_by="PATH")
    print(f"\n  [LIST] Sort by PATH")
