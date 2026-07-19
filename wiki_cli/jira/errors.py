"""Jira-specific error types."""

from wiki_cli.exceptions import WikiJSError


class JiraError(WikiJSError):
    """Base exception for all Jira API errors."""


class JiraAuthError(JiraError):
    """Raised when authentication with Jira fails."""


class JiraNotFoundError(JiraError):
    """Raised when a requested resource is not found."""


class JiraRateLimitError(JiraError):
    """Raised when Jira rate limit is exceeded."""


class JiraTimeoutError(JiraError):
    """Raised when a Jira request times out."""


class JiraValidationError(JiraError):
    """Raised when JQL validation fails."""


class JiraConfigError(JiraError):
    """Raised when Jira configuration is missing or invalid."""
