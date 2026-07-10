"""System-related menu handlers."""

from __future__ import annotations

from wiki_cli import WikiJSClient, WikiJSError
from wiki_cli.pages import PagesManager


def test_connection(client: WikiJSClient, pages: PagesManager) -> None:
    print("\nTesting connection...")
    print(f"URL: {client.url}")

    try:
        result = pages.list_all(order_by="CREATED")
        print(f"Pages accessible: {len(result)}")
        if result:
            print(f"Most recently created: {result[0].path} -- {result[0].title}")
    except WikiJSError as exc:
        print(f"Error: {exc}")
        return

    print("Connection OK.")
