"""Low-level Jira API client wrapper."""

from __future__ import annotations

import os

from wiki_cli.exceptions import WikiJSError
from wiki_cli.jira.auth import JiraAuth


class JiraClient:
    """Wraps the jira library for low-level API access.

    Handles authentication, connection, and raw API calls.
    Does not normalize or validate responses — that is the manager's job.

    Attributes:
        auth: The JiraAuth instance holding credentials.
        _client: The underlying jira.JIRA client.
    """

    def __init__(
        self,
        server: str | None = None,
        email: str | None = None,
        api_token: str | None = None,
    ) -> None:
        self.auth = JiraAuth(server=server, email=email, api_token=api_token)
        self._client = self.auth.get_client()

    def test_connection(self) -> dict:
        """Verify connectivity and return the authenticated user info.

        Returns:
            Dict with 'displayName' and 'emailAddress' of the current user.

        Raises:
            WikiJSError: If the connection test fails.
        """
        try:
            myself = self._client.myself()
            return {
                "displayName": myself.get("displayName", "Unknown"),
                "emailAddress": myself.get("emailAddress", "Unknown"),
            }
        except Exception as exc:
            raise WikiJSError(f"Jira connection test failed: {exc}") from exc

    def list_projects(self) -> list[dict]:
        """Return raw data for all accessible projects.

        Returns:
            List of raw project dicts from the Jira API.

        Raises:
            WikiJSError: If the API call fails.
        """
        try:
            projects = self._client.projects()
            return [p.raw for p in projects]
        except Exception as exc:
            raise WikiJSError(f"Failed to list Jira projects: {exc}") from exc

    def get_project(self, key: str) -> dict:
        """Return raw data for a single project.

        Args:
            key: The project key (e.g., 'PROJ').

        Raises:
            WikiJSError: If the project is not found or the API call fails.
        """
        try:
            return self._client.project(key).raw
        except Exception as exc:
            raise WikiJSError(f"Failed to get project '{key}': {exc}") from exc

    def search_issues(self, jql: str, max_results: int = 50) -> list[dict]:
        """Search issues using a JQL query.

        Args:
            jql: The JQL query string.
            max_results: Maximum number of results to return (default 50).

        Returns:
            List of raw issue dicts from the Jira API.

        Raises:
            WikiJSError: If the search fails.
        """
        try:
            issues = self._client.search_issues(jql, maxResults=max_results)
            return [i.raw for i in issues]
        except Exception as exc:
            raise WikiJSError(f"Jira search failed: {exc}") from exc

    def get_issue(self, issue_key: str) -> dict:
        """Return raw data for a single issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Raises:
            WikiJSError: If the issue is not found or the API call fails.
        """
        try:
            return self._client.issue(issue_key).raw
        except Exception as exc:
            raise WikiJSError(
                f"Failed to get issue '{issue_key}': {exc}"
            ) from exc

    def get_comments(self, issue_key: str) -> list[dict]:
        """Return raw comments for an issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Raises:
            WikiJSError: If the API call fails.
        """
        try:
            issue = self._client.issue(issue_key)
            return [c.raw for c in issue.fields.comment.comments]
        except Exception as exc:
            raise WikiJSError(
                f"Failed to get comments for '{issue_key}': {exc}"
            ) from exc

    def get_changelog(self, issue_key: str) -> list[dict]:
        """Return raw changelog histories for an issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Raises:
            WikiJSError: If the API call fails.
        """
        try:
            url = f"{self.auth.server}/rest/api/2/issue/{issue_key}/changelog"
            response = self._client._session.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("values", [])
        except Exception as exc:
            raise WikiJSError(
                f"Failed to get changelog for '{issue_key}': {exc}"
            ) from exc

    def get_transitions(self, issue_key: str) -> list[dict]:
        """Return available transitions for an issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Raises:
            WikiJSError: If the API call fails.
        """
        try:
            return self._client.transitions(issue_key)
        except Exception as exc:
            raise WikiJSError(
                f"Failed to get transitions for '{issue_key}': {exc}"
            ) from exc
