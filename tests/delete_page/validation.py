from unittest.mock import patch

from wiki_cli.cli_pages import delete_page

INPUT_PATCH = "builtins.input"


def test_delete_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        delete_page(mock_manager)

    mock_manager.delete.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
