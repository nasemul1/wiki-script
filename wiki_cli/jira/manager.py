"""JiraManager — handles all Jira operations with normalization and validation."""

from __future__ import annotations

import os

from dotenv import load_dotenv

from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.errors import JiraNotFoundError
from wiki_cli.jira.jql import JQLValidator
from wiki_cli.jira.models import (
    JiraChangelogEntry,
    JiraComment,
    JiraIssue,
    JiraProject,
    JiraTransition,
)

load_dotenv()


class JiraManager:
    """Handles Jira operations with allowlisting, JQL safety, and normalized models.

    Attributes:
        client: An initialized JiraClient instance.
        allowed_projects: List of project keys that are permitted. Empty means all.
        validator: JQLValidator instance for query safety.
    """

    def __init__(
        self,
        client: JiraClient,
        allowed_projects: list[str] | None = None,
    ) -> None:
        self.client = client
        self.validator = JQLValidator()

        if allowed_projects is None:
            raw = os.getenv("JIRA_PROJECT_ALLOWLIST", "")
            self.allowed_projects = [
                p.strip() for p in raw.split(",") if p.strip()
            ]
        else:
            self.allowed_projects = allowed_projects

    def test_connection(self) -> dict:
        """Test Jira connectivity and return user info.

        Returns:
            Dict with 'displayName' and 'emailAddress'.
        """
        return self.client.test_connection()

    def list_projects(self) -> list[JiraProject]:
        """List accessible projects, filtered by the allowlist.

        Returns:
            List of JiraProject instances for allowed projects.
        """
        raw_projects = self.client.list_projects()
        result = []

        for p in raw_projects:
            project = JiraProject(
                key=p.get("key", ""),
                name=p.get("name", ""),
                description=p.get("description"),
                lead=p.get("lead", {}).get("displayName")
                if p.get("lead")
                else None,
                project_type=p.get("projectTypeKey"),
            )

            if not self.allowed_projects or project.key in self.allowed_projects:
                result.append(project)

        return result

    def get_project(self, key: str) -> JiraProject:
        """Get a single project by key.

        Args:
            key: The project key (e.g., 'PROJ').

        Raises:
            JiraNotFoundError: If the project is not in the allowlist or not found.
        """
        if self.allowed_projects and key not in self.allowed_projects:
            raise JiraNotFoundError(
                f"Project '{key}' is not in the allowed projects list."
            )

        raw = self.client.get_project(key)
        return JiraProject(
            key=raw.get("key", ""),
            name=raw.get("name", ""),
            description=raw.get("description"),
            lead=raw.get("lead", {}).get("displayName")
            if raw.get("lead")
            else None,
            project_type=raw.get("projectTypeKey"),
        )

    def search_issues(
        self,
        jql: str | None = None,
        project: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        priority: str | None = None,
        issue_type: str | None = None,
    ) -> list[JiraIssue]:
        """Search issues using validated JQL or filter parameters.

        Either provide raw JQL (which will be validated) or use the filter
        parameters to build a safe query automatically.

        Args:
            jql: Raw JQL query string (optional).
            project: Project key filter.
            status: Status filter.
            assignee: Assignee filter.
            priority: Priority filter.
            issue_type: Issue type filter.

        Returns:
            List of JiraIssue instances.
        """
        if jql is None:
            jql = self.validator.build_search_query(
                project=project,
                status=status,
                assignee=assignee,
                priority=priority,
                issue_type=issue_type,
            )
        else:
            jql = self.validator.validate(jql)

        raw_issues = self.client.search_issues(jql)
        return [self._parse_issue(i) for i in raw_issues]

    def get_issue(self, issue_key: str) -> JiraIssue:
        """Get a single issue by key.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Returns:
            JiraIssue instance.

        Raises:
            JiraNotFoundError: If the issue is not found.
        """
        raw = self.client.get_issue(issue_key)
        return self._parse_issue(raw)

    def get_comments(self, issue_key: str) -> list[JiraComment]:
        """Get comments for an issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Returns:
            List of JiraComment instances.
        """
        raw_comments = self.client.get_comments(issue_key)
        return [
            JiraComment(
                id=str(c.get("id", "")),
                author=c.get("author", {}).get("displayName", "Unknown"),
                body=c.get("body", ""),
                created=c.get("created", ""),
                updated=c.get("updated"),
            )
            for c in raw_comments
        ]

    def get_changelog(self, issue_key: str) -> list[JiraChangelogEntry]:
        """Get the changelog (history) for an issue.

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Returns:
            List of JiraChangelogEntry instances, one per field change.
        """
        raw_histories = self.client.get_changelog(issue_key)
        entries = []

        for history in raw_histories:
            author = history.get("author", {}).get("displayName", "Unknown")
            created = history.get("created", "")

            for item in history.get("items", []):
                entries.append(
                    JiraChangelogEntry(
                        id=str(history.get("id", "")),
                        author=author,
                        created=created,
                        field=item.get("field", "Unknown"),
                        from_value=item.get("fromString"),
                        to_value=item.get("toString"),
                    )
                )

        return entries

    def get_transitions(self, issue_key: str) -> list[JiraTransition]:
        """Get available transitions for an issue (read-only inspection).

        Args:
            issue_key: The issue key (e.g., 'PROJ-123').

        Returns:
            List of JiraTransition instances.
        """
        raw_transitions = self.client.get_transitions(issue_key)
        return [
            JiraTransition(
                id=str(t.get("id", "")),
                name=t.get("name", ""),
                to_status=t.get("to", {}).get("name", ""),
            )
            for t in raw_transitions
        ]

    def _parse_issue(self, raw: dict) -> JiraIssue:
        """Parse a raw Jira issue dict into a JiraIssue model."""
        fields = raw.get("fields", {})
        return JiraIssue(
            key=raw.get("key", ""),
            summary=fields.get("summary", ""),
            description=fields.get("description"),
            status=fields.get("status", {}).get("name", "Unknown"),
            priority=fields.get("priority", {}).get("name", "Unknown"),
            issue_type=fields.get("issuetype", {}).get("name", "Unknown"),
            labels=fields.get("labels", []),
            assignee=fields.get("assignee", {}).get("displayName")
            if fields.get("assignee")
            else None,
            reporter=fields.get("reporter", {}).get("displayName")
            if fields.get("reporter")
            else None,
            created=fields.get("created", ""),
            updated=fields.get("updated", ""),
        )
