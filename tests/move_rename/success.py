from unittest.mock import patch

from wiki_cli.cli_pages import move_rename_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def _existing_page():
    return Page(id=1, path="docs/old", title="Old Title", content="c")


def test_move_success(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    mock_manager.update.return_value = PageResponse(succeeded=True, message="OK")
    inputs = iter(["1", "docs/new", "New Title", "yes"])

    with patch(INPUT_PATCH, side_effect=inputs):
        move_rename_page(mock_manager)

    updated = mock_manager.update.call_args[0][0]
    assert updated.path == "docs/new"
    assert updated.title == "New Title"
    output = capsys.readouterr().out
    assert "Moved page 1 to: docs/new" in output
    print(f"\n  [MOVE] Path: docs/old → docs/new, Title: Old Title → New Title")


def test_move_no_changes(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    inputs = iter(["1", "", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        move_rename_page(mock_manager)

    mock_manager.update.assert_not_called()
    output = capsys.readouterr().out
    assert "No changes made." in output
    print(f"\n  [MOVE] No changes")


def test_move_cancelled(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    inputs = iter(["1", "docs/new", "", "no"])

    with patch(INPUT_PATCH, side_effect=inputs):
        move_rename_page(mock_manager)

    mock_manager.update.assert_not_called()
    output = capsys.readouterr().out
    assert "Cancelled." in output
    print(f"\n  [MOVE] Cancelled")


def test_move_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        move_rename_page(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
