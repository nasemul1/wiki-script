"""Tests for Jira Pydantic models."""

import pytest

from wiki_cli.jira.models import (
    JiraChangelogEntry,
    JiraComment,
    JiraIssue,
    JiraProject,
    JiraTransition,
)


class TestJiraProject:
    def test_minimal(self):
        p = JiraProject(key="PROJ", name="My Project")
        assert p.key == "PROJ"
        assert p.name == "My Project"
        assert p.description is None
        assert p.lead is None
        assert p.project_type is None

    def test_full(self):
        p = JiraProject(
            key="DEV",
            name="Dev Project",
            description="Development work",
            lead="Nasimul",
            project_type="business",
        )
        assert p.key == "DEV"
        assert p.lead == "Nasimul"
        assert p.project_type == "business"

    def test_model_dump(self):
        p = JiraProject(key="T", name="Test")
        d = p.model_dump()
        assert d["key"] == "T"
        assert d["name"] == "Test"
        assert isinstance(d, dict)


class TestJiraIssue:
    def test_minimal(self):
        i = JiraIssue(
            key="PROJ-1",
            summary="Test issue",
            status="Open",
            priority="Medium",
            issue_type="Task",
        )
        assert i.key == "PROJ-1"
        assert i.labels == []
        assert i.assignee is None
        assert i.reporter is None

    def test_full(self):
        i = JiraIssue(
            key="PROJ-123",
            summary="Fix bug",
            description="Detailed description",
            status="In Progress",
            priority="High",
            issue_type="Bug",
            labels=["frontend", "urgent"],
            assignee="Nasimul",
            reporter="Naveed",
            created="2026-01-15T10:00:00.000+0000",
            updated="2026-01-16T12:00:00.000+0000",
        )
        assert i.assignee == "Nasimul"
        assert len(i.labels) == 2
        assert "frontend" in i.labels

    def test_model_dump_roundtrip(self):
        i = JiraIssue(
            key="X-1", summary="S", status="Open",
            priority="Low", issue_type="Task",
        )
        d = i.model_dump()
        i2 = JiraIssue(**d)
        assert i2.key == i.key
        assert i2.summary == i.summary


class TestJiraComment:
    def test_minimal(self):
        c = JiraComment(id="100", author="Nasimul", body="Hello")
        assert c.id == "100"
        assert c.created == ""
        assert c.updated is None

    def test_full(self):
        c = JiraComment(
            id="200",
            author="Naveed",
            body="Looks good",
            created="2026-01-15T10:00:00.000+0000",
            updated="2026-01-15T11:00:00.000+0000",
        )
        assert c.body == "Looks good"
        assert c.updated is not None


class TestJiraChangelogEntry:
    def test_minimal(self):
        e = JiraChangelogEntry(
            id="1", author="Nasimul", field="status"
        )
        assert e.from_value is None
        assert e.to_value is None

    def test_with_values(self):
        e = JiraChangelogEntry(
            id="2",
            author="Naveed",
            created="2026-01-15T10:00:00.000+0000",
            field="status",
            from_value="Open",
            to_value="In Progress",
        )
        assert e.from_value == "Open"
        assert e.to_value == "In Progress"


class TestJiraTransition:
    def test_basic(self):
        t = JiraTransition(id="31", name="Start Progress", to_status="In Progress")
        assert t.id == "31"
        assert t.name == "Start Progress"
        assert t.to_status == "In Progress"


class TestModelValidation:
    def test_missing_required_field_project(self):
        with pytest.raises(Exception):
            JiraProject()

    def test_missing_required_field_issue(self):
        with pytest.raises(Exception):
            JiraIssue()

    def test_missing_required_field_comment(self):
        with pytest.raises(Exception):
            JiraComment()

    def test_extra_fields_ignored(self):
        p = JiraProject(key="X", name="Y", unknown_field="ignored")
        assert p.key == "X"
