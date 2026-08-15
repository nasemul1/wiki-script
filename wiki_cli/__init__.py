"""Wiki.js automation toolkit for managing pages via GraphQL."""

from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError
from wiki_cli.models import Page, PageResponse, PageHistory, PageVersion
from wiki_cli.pages import PagesManager
from wiki_cli.wikis import get_active_client, switch_wiki_flow
from wiki_cli.cli_main import main

__all__ = [
    "WikiJSClient",
    "WikiJSError",
    "Page",
    "PageResponse",
    "PageHistory",
    "PageVersion",
    "PagesManager",
    "get_active_client",
    "switch_wiki_flow",
    "main",
]

# Jira exports (optional — requires jira package)
try:
    from wiki_cli.jira import (
        JiraClient,
        JiraManager,
        JiraProject,
        JiraIssue,
        JiraComment,
        JiraChangelogEntry,
        JiraTransition,
        JQLValidator,
    )

    __all__ += [
        "JiraClient",
        "JiraManager",
        "JiraProject",
        "JiraIssue",
        "JiraComment",
        "JiraChangelogEntry",
        "JiraTransition",
        "JQLValidator",
    ]
except ImportError:
    pass

__version__ = "0.1.0"
