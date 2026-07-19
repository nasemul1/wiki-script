"""Jira authentication handling."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from wiki_cli.jira.errors import JiraConfigError

load_dotenv()


class JiraAuth:
    """Manages Jira authentication credentials.

    Reads from environment variables:
        JIRA_SERVER: The Jira instance URL (e.g., https://domain.atlassian.net)
        JIRA_EMAIL: The user email for authentication
        JIRA_API_TOKEN: The API token for authentication
    """

    def __init__(
        self,
        server: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self.server = server or os.getenv("JIRA_SERVER", "")
        self.email = email or os.getenv("JIRA_EMAIL", "")
        self.api_token = api_token or os.getenv("JIRA_API_TOKEN", "")

        if not self.server:
            raise JiraConfigError(
                "JIRA_SERVER is not set. Provide it as an argument or in the environment."
            )
        if not self.email:
            raise JiraConfigError(
                "JIRA_EMAIL is not set. Provide it as an argument or in the environment."
            )
        if not self.api_token:
            raise JiraConfigError(
                "JIRA_API_TOKEN is not set. Provide it as an argument or in the environment."
            )

    def get_client(self):
        """Create and return an authenticated JIRA client.

        Returns:
            A jira.JIRA instance authenticated with basic auth.

        Raises:
            JiraAuthError: If the jira library is not installed.
        """
        try:
            from jira import JIRA
        except ImportError:
            raise JiraConfigError(
                "The 'jira' package is not installed. "
                "Install it with: pip install jira"
            )

        return JIRA(
            server=self.server,
            basic_auth=(self.email, self.api_token),
        )
