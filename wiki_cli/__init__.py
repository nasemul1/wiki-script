"""Wiki.js automation toolkit for managing pages via GraphQL."""

from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError
from wiki_cli.models import Page, PageResponse, PageHistory, PageVersion
from wiki_cli.pages import PagesManager
from wiki_cli.cli_main import main

__all__ = [
    "WikiJSClient",
    "WikiJSError",
    "Page",
    "PageResponse",
    "PageHistory",
    "PageVersion",
    "PagesManager",
    "main",
]
__version__ = "0.1.0"
