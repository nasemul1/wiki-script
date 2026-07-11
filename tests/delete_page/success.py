from unittest.mock import patch

from wiki_cli.cli_pages import delete_page

INPUT_PATCH = "builtins.input"


def test_delete_success(mock_manager, capsys):
    inputs = iter(["5", "yes"])

    with patch(INPUT_PATCH, side_effect=inputs):
        delete_page(mock_manager)

    mock_manager.delete.assert_called_once_with(5)
    output = capsys.readouterr().out
    assert "Deleted page 5." in output
    print(f"\n  [DELETE] Called delete(5)")


def test_delete_cancelled(mock_manager, capsys):
    inputs = iter(["5", "no"])

    with patch(INPUT_PATCH, side_effect=inputs):
        delete_page(mock_manager)

    mock_manager.delete.assert_not_called()
    output = capsys.readouterr().out
    assert "Cancelled." in output
    print(f"\n  [DELETE] Cancelled — delete() not called")


def test_delete_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        delete_page(mock_manager)

    mock_manager.delete.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
