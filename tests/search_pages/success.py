from unittest.mock import patch

from wiki_cli.cli_pages import search_pages
from wiki_cli.models import Page

INPUT_PATCH = "builtins.input"


def test_search_success(mock_manager, capsys):
    mock_manager.search.return_value = [
        Page(id=1, path="docs/intro", title="Introduction", tags=["wiki"]),
    ]
    inputs = iter(["intro", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        search_pages(mock_manager)

    mock_manager.search.assert_called_once_with("intro")
    output = capsys.readouterr().out
    assert "Total: 1 page(s)" in output
    print(f"\n  [SEARCH] Found 1 page for 'intro'")


def test_search_empty_query(mock_manager, capsys):
    inputs = iter(["", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        search_pages(mock_manager)

    mock_manager.search.assert_not_called()
    output = capsys.readouterr().out
    assert "Query is required." in output
    print(f"\n  [VALIDATION] Empty query rejected")


def test_search_no_results(mock_manager, capsys):
    mock_manager.search.return_value = []
    inputs = iter(["xyz", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        search_pages(mock_manager)

    output = capsys.readouterr().out
    assert "No pages found." in output
    print(f"\n  [SEARCH] No results")


def test_search_with_locale(mock_manager, capsys):
    mock_manager.search.return_value = []
    inputs = iter(["intro", "en", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        search_pages(mock_manager)

    mock_manager.search.assert_called_with("intro", locale="en")
    print(f"\n  [SEARCH] With locale 'en'")


def test_search_with_tag_filter(mock_manager, capsys):
    mock_manager.search.return_value = [
        Page(id=1, path="a", title="A", tags=["wiki"]),
        Page(id=2, path="b", title="B", tags=["setup"]),
    ]
    inputs = iter(["query", "", "wiki", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        search_pages(mock_manager)

    output = capsys.readouterr().out
    assert "A" in output
    assert "B" not in output
    print(f"\n  [SEARCH] Filtered by tag 'wiki'")
