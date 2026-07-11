from unittest.mock import patch

from wiki_cli.cli_pages import create_page

INPUT_PATCH = "builtins.input"


def test_path_required(mock_manager, capsys):
    inputs = iter(["", "Title", "content", "", "", "en", "n", "y"])

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    mock_manager.create.assert_not_called()
    output = capsys.readouterr().out
    assert "Path is required." in output


def test_title_required(mock_manager, capsys):
    inputs = iter(["test/path", "", "content", "", "", "en", "n", "y"])

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    mock_manager.create.assert_not_called()
    output = capsys.readouterr().out
    assert "Title is required." in output
