from unittest.mock import patch

from wiki_cli.cli_pages import fetch_page

INPUT_PATCH = "builtins.input"


def test_fetch_invalid_id(mock_manager, capsys):
    inputs = iter(["1", "abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        fetch_page(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")


def test_fetch_path_required(mock_manager, capsys):
    inputs = iter(["2", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        fetch_page(mock_manager)

    mock_manager.get_by_path.assert_not_called()
    output = capsys.readouterr().out
    assert "Path is required." in output
    print(f"\n  [VALIDATION] Empty path rejected")
