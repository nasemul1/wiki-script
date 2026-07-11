from unittest.mock import MagicMock

from wiki_cli.cli_system import test_connection
from wiki_cli.models import Page
from wiki_cli.pages import PagesManager
from wiki_cli.client import WikiJSClient


def test_connection_success(capsys):
    client = MagicMock(spec=WikiJSClient)
    client.url = "https://wiki.example.com/graphql"
    pages = MagicMock(spec=PagesManager)
    pages.list_all.return_value = [
        Page(id=1, path="docs/intro", title="Intro"),
    ]

    test_connection(client, pages)

    pages.list_all.assert_called_once_with(order_by="CREATED")
    output = capsys.readouterr().out
    assert "Testing connection..." in output
    assert "Pages accessible: 1" in output
    assert "Most recently created: docs/intro -- Intro" in output
    assert "Connection OK." in output
    print(f"\n  [CONNECTION] Success with 1 page")


def test_connection_no_pages(capsys):
    client = MagicMock(spec=WikiJSClient)
    client.url = "https://wiki.example.com/graphql"
    pages = MagicMock(spec=PagesManager)
    pages.list_all.return_value = []

    test_connection(client, pages)

    output = capsys.readouterr().out
    assert "Pages accessible: 0" in output
    assert "Connection OK." in output
    print(f"\n  [CONNECTION] Success with 0 pages")
