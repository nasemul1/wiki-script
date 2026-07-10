"""Wiki.js automation toolkit for managing pages via GraphQL."""

from wiki_script.wiki_client import WikiJSClient
from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page, PageResponse, PageHistory, PageVersion
from wiki_script.operations.pages import PagesManager

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
