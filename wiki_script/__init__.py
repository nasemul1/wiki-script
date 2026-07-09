"""Wiki.js automation toolkit for managing pages and assets via GraphQL."""

from wiki_script.wiki_client import WikiJSClient
from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page, Asset, AssetFolder, PageResponse, PageHistory, PageVersion
from wiki_script.operations.pages import PagesManager
from wiki_script.operations.assets import AssetsManager

__all__ = [
    "WikiJSClient",
    "WikiJSError",
    "Page",
    "Asset",
    "AssetFolder",
    "PageResponse",
    "PageHistory",
    "PageVersion",
    "PagesManager",
    "AssetsManager",
]
__version__ = "0.1.0"
