from unittest.mock import patch, MagicMock

from wiki_cli.cli_main import main
from wiki_cli import WikiJSError
from wiki_cli.client import WikiJSClient

INPUT_PATCH = "builtins.input"


def _client():
    c = MagicMock(spec=WikiJSClient)
    c.url = "https://w.com/graphql"
    return c


def test_menu_exit(capsys, tmp_wiki_config):
    wikis_save = MagicMock()
    with patch(INPUT_PATCH, side_effect=iter(["0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()
    output = capsys.readouterr().out
    assert "Goodbye!" in output
    print(f"\n  [MENU] Exit")


def test_menu_invalid_option(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["99", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                main()
    output = capsys.readouterr().out
    assert "Invalid option. Try again." in output
    print(f"\n  [MENU] Invalid option handled")


def test_menu_dispatches_handler(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["1", "", "", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                with patch("wiki_cli.cli_main.create_page") as mock_create:
                    main()
    mock_create.assert_called_once()
    print(f"\n  [MENU] Handler dispatched")


def test_menu_handles_error(capsys, tmp_wiki_config):
    with patch(INPUT_PATCH, side_effect=iter(["16", "", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager"):
                with patch("wiki_cli.cli_main.test_connection", side_effect=WikiJSError("Conn failed")):
                    main()
    output = capsys.readouterr().err
    assert "Error: Conn failed" in output
    print(f"\n  [MENU] WikiJSError handled gracefully")


def test_menu_switch_wiki_rebuilds(capsys, tmp_wiki_config):
    new_client = MagicMock(spec=WikiJSClient)
    new_client.url = "https://new.com/graphql"
    with patch(INPUT_PATCH, side_effect=iter(["18", "0"])):
        with patch("wiki_cli.cli_main.get_active_client", return_value=_client()):
            with patch("wiki_cli.cli_main.PagesManager") as mock_pm:
                with patch("wiki_cli.cli_main.switch_wiki_flow", return_value=new_client) as mock_sw:
                    main()
    mock_sw.assert_called_once()
    output = capsys.readouterr().out
    assert "Switch Wiki" in output
    print(f"\n  [MENU] Switch wiki rebuilds client")
