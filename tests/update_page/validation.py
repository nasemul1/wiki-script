from unittest.mock import patch

from wiki_cli.cli_pages import update_page

INPUT_PATCH = "builtins.input"


def test_update_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        update_page(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    mock_manager.update.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
