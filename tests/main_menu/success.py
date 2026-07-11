from unittest.mock import patch, MagicMock

from wiki_cli.cli_main import main
from wiki_cli import WikiJSError

INPUT_PATCH = "builtins.input"


def test_menu_exit(capsys):
    inputs = iter(["0"])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_main.WikiJSClient"):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()

    output = capsys.readouterr().out
    assert "Goodbye!" in output
    print(f"\n  [MENU] Exit")


def test_menu_invalid_option(capsys):
    inputs = iter(["99", "0"])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_main.WikiJSClient"):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()

    output = capsys.readouterr().out
    assert "Invalid option. Try again." in output
    print(f"\n  [MENU] Invalid option handled")


def test_menu_dispatches_handler(capsys):
    inputs = iter(["1", "", "", "0"])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_main.WikiJSClient"):
            with patch("wiki_cli.cli_main.PagesManager") as mock_pm:
                with patch("wiki_cli.cli_main.create_page") as mock_create:
                    main()

    mock_create.assert_called_once()
    print(f"\n  [MENU] Handler dispatched")


def test_menu_handles_error(capsys):
    inputs = iter(["16", "", "0"])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("wiki_cli.cli_main.WikiJSClient") as mock_client:
            with patch("wiki_cli.cli_main.PagesManager") as mock_pm:
                with patch("wiki_cli.cli_main.test_connection", side_effect=WikiJSError("Conn failed")):
                    mock_client_inst = mock_client.return_value
                    main()

    output = capsys.readouterr().err
    assert "Error: Conn failed" in output
    print(f"\n  [MENU] WikiJSError handled gracefully")
