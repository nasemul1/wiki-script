"""Wiki.js automation toolkit for managing pages via GraphQL."""

from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError
from wiki_cli.models import Page, PageResponse, PageHistory, PageVersion
from wiki_cli.pages import PagesManager

__all__ = [
    "WikiJSClient",
    "WikiJSError",
    "Page",
    "PageResponse",
    "PageHistory",
    "PageVersion",
    "PagesManager",
]
__version__ = "0.1.0"
