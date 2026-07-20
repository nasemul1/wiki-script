"""Pydantic models for Jira resources."""

from datetime import datetime

from pydantic import BaseModel


class JiraProject(BaseModel):
    """Represents a Jira project."""

    key: str
    name: str
    description: str | None = None
    lead: str | None = None
    project_type: str | None = None


class JiraIssue(BaseModel):
    """Represents a Jira issue."""

    key: str
    summary: str
    description: str | None = None
    status: str
    priority: str
    issue_type: str
    labels: list[str] = []
    assignee: str | None = None
    reporter: str | None = None
    created: str = ""
    updated: str = ""


class JiraComment(BaseModel):
    """Represents a comment on a Jira issue."""

    id: str
    author: str
    body: str
    created: str = ""
    updated: str | None = None


class JiraChangelogEntry(BaseModel):
    """Represents a single change in a Jira issue's changelog."""

    id: str
    author: str
    created: str = ""
    field: str
    from_value: str | None = None
    to_value: str | None = None


class JiraTransition(BaseModel):
    """Represents an available transition for a Jira issue."""

    id: str
    name: str
    to_status: str
