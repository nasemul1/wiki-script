from unittest.mock import patch

from wiki_cli.cli_history import view_page_history
from wiki_cli.models import Page, PageHistory

INPUT_PATCH = "builtins.input"


def test_view_history_success(mock_manager, capsys):
    mock_manager.get_by_id.return_value = Page(id=1, path="docs/intro", title="Intro")
    mock_manager.get_history.return_value = (
        [
            PageHistory(versionId=5, versionDate="2024-01-10", authorName="Admin", actionType="update"),
            PageHistory(versionId=1, versionDate="2024-01-01", authorName="Admin", actionType="create"),
        ],
        2,
    )
    inputs = iter(["1"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_page_history(mock_manager)

    mock_manager.get_history.assert_called_once()
    output = capsys.readouterr().out
    assert "Total: 2 revision(s)" in output
    print(f"\n  [HISTORY] 2 revisions listed")


def test_view_history_empty(mock_manager, capsys):
    mock_manager.get_by_id.return_value = Page(id=1, path="x", title="X")
    mock_manager.get_history.return_value = ([], 0)
    inputs = iter(["1"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_page_history(mock_manager)

    output = capsys.readouterr().out
    assert "No history entries found." in output
    print(f"\n  [HISTORY] Empty")


def test_view_history_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_page_history(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
