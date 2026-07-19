"""JQL validation and safe query construction."""

from __future__ import annotations

import re

from wiki_cli.jira.errors import JiraValidationError


class JQLValidator:
    """Validates and sanitizes JQL queries to prevent injection.

    Uses a hybrid approach:
    - Template-based query building from safe filter parameters
    - Validation of raw JQL strings against forbidden patterns
    """

    FORBIDDEN_KEYWORDS = frozenset({
        "DROP", "DELETE", "UPDATE", "INSERT", "EXEC", "EXECUTE",
        "ALTER", "CREATE", "TRUNCATE", "GRANT", "REVOKE",
    })

    FORBIDDEN_PATTERNS = (
        "UNION", "OR 1=1", "OR 1 = 1", "1=1",
        "--", ";", "/*", "*/", "CHAR(", "CONCAT(",
    )

    def validate(self, jql: str) -> str:
        """Validate a raw JQL string for safety.

        Args:
            jql: The JQL query to validate.

        Returns:
            The validated JQL string (unchanged if safe).

        Raises:
            JiraValidationError: If forbidden keywords or patterns are detected.
        """
        if not jql or not jql.strip():
            raise JiraValidationError("JQL query cannot be empty.")

        upper = jql.upper()

        for keyword in self.FORBIDDEN_KEYWORDS:
            if re.search(r'\b' + keyword + r'\b', upper):
                raise JiraValidationError(
                    f"Forbidden keyword in JQL: {keyword}"
                )

        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern.lower() in jql.lower():
                raise JiraValidationError(
                    f"Forbidden pattern in JQL: {pattern}"
                )

        return jql

    def build_search_query(
        self,
        project: str | None = None,
        status: str | None = None,
        assignee: str | None = None,
        priority: str | None = None,
        issue_type: str | None = None,
    ) -> str:
        """Build a safe JQL query from filter parameters.

        All values are quoted to prevent injection through filter values.

        Args:
            project: Project key filter (e.g., 'PROJ').
            status: Status name filter (e.g., 'In Progress').
            assignee: Assignee display name or email filter.
            priority: Priority name filter (e.g., 'High').
            issue_type: Issue type name filter (e.g., 'Bug').

        Returns:
            A safe JQL query string.
        """
        parts = []

        if project:
            self._validate_value(project)
            parts.append(f'project = "{project}"')
        if status:
            self._validate_value(status)
            parts.append(f'status = "{status}"')
        if assignee:
            self._validate_value(assignee)
            parts.append(f'assignee = "{assignee}"')
        if priority:
            self._validate_value(priority)
            parts.append(f'priority = "{priority}"')
        if issue_type:
            self._validate_value(issue_type)
            parts.append(f'issuetype = "{issue_type}"')

        if not parts:
            raise JiraValidationError(
                "At least one filter (project, status, assignee, priority, "
                "or issue type) is required. Jira Cloud does not allow "
                "unbounded searches."
            )

        return " AND ".join(parts) + " order by created DESC"

    def _validate_value(self, value: str) -> None:
        """Validate a single filter value for safety.

        Raises:
            JiraValidationError: If the value contains forbidden characters.
        """
        forbidden = ['"', "'", "\\", ";", "--"]
        for char in forbidden:
            if char in value:
                raise JiraValidationError(
                    f"Forbidden character '{char}' in filter value: {value}"
                )
