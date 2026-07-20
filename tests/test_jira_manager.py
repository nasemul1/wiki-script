"""Tests for JiraManager operations with mocked client."""

import pytest
from unittest.mock import MagicMock

from wiki_cli.jira.manager import JiraManager
from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.models import (
    JiraChangelogEntry,
    JiraComment,
    JiraIssue,
    JiraProject,
    JiraTransition,
)
from wiki_cli.jira.errors import JiraNotFoundError


@pytest.fixture
def jira_client():
    return MagicMock(spec=JiraClient)


@pytest.fixture
def manager(jira_client):
    return JiraManager(jira_client, allowed_projects=["PROJ1", "PROJ2"])


@pytest.fixture
def manager_no_allowlist(jira_client):
    return JiraManager(jira_client, allowed_projects=[])


# ── test_connection ─────────────────────────────────────────────────


class TestManagerConnection:
    def test_returns_user_info(self, manager, jira_client):
        jira_client.test_connection.return_value = {
            "displayName": "Nasimul",
            "emailAddress": "nasimul@test.com",
        }
        result = manager.test_connection()
        assert result["displayName"] == "Nasimul"
        assert result["emailAddress"] == "nasimul@test.com"


# ── list_projects ───────────────────────────────────────────────────


class TestManagerListProjects:
    def test_filters_by_allowlist(self, manager, jira_client):
        jira_client.list_projects.return_value = [
            {"key": "PROJ1", "name": "Project 1", "projectTypeKey": "business"},
            {"key": "PROJ2", "name": "Project 2", "projectTypeKey": "software"},
            {"key": "PROJ3", "name": "Project 3", "projectTypeKey": "business"},
        ]
        projects = manager.list_projects()
        assert len(projects) == 2
        keys = [p.key for p in projects]
        assert "PROJ1" in keys
        assert "PROJ2" in keys
        assert "PROJ3" not in keys

    def test_empty_allowlist_returns_all(self, manager_no_allowlist, jira_client):
        jira_client.list_projects.return_value = [
            {"key": "A", "name": "A"},
            {"key": "B", "name": "B"},
        ]
        projects = manager_no_allowlist.list_projects()
        assert len(projects) == 2

    def test_parses_lead(self, manager, jira_client):
        jira_client.list_projects.return_value = [
            {
                "key": "PROJ1",
                "name": "P1",
                "lead": {"displayName": "Nasimul"},
            },
        ]
        projects = manager.list_projects()
        assert projects[0].lead == "Nasimul"

    def test_handles_missing_lead(self, manager, jira_client):
        jira_client.list_projects.return_value = [
            {"key": "PROJ1", "name": "P1"},
        ]
        projects = manager.list_projects()
        assert projects[0].lead is None


# ── get_project ─────────────────────────────────────────────────────


class TestManagerGetProject:
    def test_allowed_project(self, manager, jira_client):
        jira_client.get_project.return_value = {
            "key": "PROJ1",
            "name": "Project 1",
            "projectTypeKey": "business",
        }
        project = manager.get_project("PROJ1")
        assert project.key == "PROJ1"

    def test_unallowed_project_raises(self, manager):
        with pytest.raises(JiraNotFoundError, match="not in the allowed"):
            manager.get_project("SECRET")


# ── search_issues ───────────────────────────────────────────────────


class TestManagerSearchIssues:
    def test_search_with_filters(self, manager, jira_client):
        jira_client.search_issues.return_value = [
            {
                "key": "PROJ1-1",
                "fields": {
                    "summary": "Test issue",
                    "status": {"name": "Open"},
                    "priority": {"name": "High"},
                    "issuetype": {"name": "Bug"},
                    "labels": ["urgent"],
                    "assignee": {"displayName": "Nasimul"},
                    "reporter": {"displayName": "Naveed"},
                    "created": "2026-01-15",
                    "updated": "2026-01-16",
                },
            }
        ]
        issues = manager.search_issues(project="PROJ1")
        assert len(issues) == 1
        assert issues[0].key == "PROJ1-1"
        assert issues[0].status == "Open"
        assert issues[0].assignee == "Nasimul"
        assert "urgent" in issues[0].labels

    def test_search_with_raw_jql(self, manager, jira_client):
        jira_client.search_issues.return_value = [
            {
                "key": "PROJ1-2",
                "fields": {
                    "summary": "Another issue",
                    "status": {"name": "Closed"},
                    "priority": {"name": "Low"},
                    "issuetype": {"name": "Task"},
                    "labels": [],
                },
            }
        ]
        issues = manager.search_issues(jql='project = PROJ1 AND status = "Closed"')
        assert len(issues) == 1
        assert issues[0].key == "PROJ1-2"

    def test_empty_results(self, manager, jira_client):
        jira_client.search_issues.return_value = []
        issues = manager.search_issues(jql="project = EMPTY")
        assert issues == []


# ── get_issue ───────────────────────────────────────────────────────


class TestManagerGetIssue:
    def test_returns_parsed_issue(self, manager, jira_client):
        jira_client.get_issue.return_value = {
            "key": "PROJ1-42",
            "fields": {
                "summary": "Fix login bug",
                "description": "Users cannot login",
                "status": {"name": "In Progress"},
                "priority": {"name": "Critical"},
                "issuetype": {"name": "Bug"},
                "labels": ["auth", "urgent"],
                "assignee": {"displayName": "Nasimul"},
                "reporter": {"displayName": "Naveed"},
                "created": "2026-07-15T10:00:00.000+0000",
                "updated": "2026-07-16T12:00:00.000+0000",
            },
        }
        issue = manager.get_issue("PROJ1-42")
        assert issue.key == "PROJ1-42"
        assert issue.summary == "Fix login bug"
        assert issue.description == "Users cannot login"
        assert issue.status == "In Progress"
        assert issue.priority == "Critical"
        assert issue.issue_type == "Bug"
        assert issue.assignee == "Nasimul"
        assert issue.reporter == "Naveed"

    def test_handles_null_assignee(self, manager, jira_client):
        jira_client.get_issue.return_value = {
            "key": "PROJ1-1",
            "fields": {
                "summary": "Unassigned",
                "status": {"name": "Open"},
                "priority": {"name": "Medium"},
                "issuetype": {"name": "Task"},
                "labels": [],
                "assignee": None,
                "reporter": None,
            },
        }
        issue = manager.get_issue("PROJ1-1")
        assert issue.assignee is None
        assert issue.reporter is None


# ── get_comments ────────────────────────────────────────────────────


class TestManagerGetComments:
    def test_returns_parsed_comments(self, manager, jira_client):
        jira_client.get_comments.return_value = [
            {
                "id": "100",
                "author": {"displayName": "Nasimul"},
                "body": "Working on this",
                "created": "2026-07-15T10:00:00.000+0000",
                "updated": "2026-07-15T11:00:00.000+0000",
            },
            {
                "id": "101",
                "author": {"displayName": "Naveed"},
                "body": "Looks good",
                "created": "2026-07-15T12:00:00.000+0000",
                "updated": None,
            },
        ]
        comments = manager.get_comments("PROJ1-1")
        assert len(comments) == 2
        assert comments[0].author == "Nasimul"
        assert comments[0].body == "Working on this"
        assert comments[1].author == "Naveed"
        assert comments[1].updated is None

    def test_empty_comments(self, manager, jira_client):
        jira_client.get_comments.return_value = []
        comments = manager.get_comments("PROJ1-1")
        assert comments == []


# ── get_changelog ───────────────────────────────────────────────────


class TestManagerGetChangelog:
    def test_returns_parsed_changelog(self, manager, jira_client):
        jira_client.get_changelog.return_value = [
            {
                "id": "500",
                "author": {"displayName": "Nasimul"},
                "created": "2026-07-15T10:00:00.000+0000",
                "items": [
                    {
                        "field": "status",
                        "fromString": "Open",
                        "toString": "In Progress",
                    },
                    {
                        "field": "assignee",
                        "fromString": None,
                        "toString": "Nasimul",
                    },
                ],
            }
        ]
        entries = manager.get_changelog("PROJ1-1")
        assert len(entries) == 2
        assert entries[0].field == "status"
        assert entries[0].from_value == "Open"
        assert entries[0].to_value == "In Progress"
        assert entries[1].field == "assignee"
        assert entries[1].from_value is None

    def test_empty_changelog(self, manager, jira_client):
        jira_client.get_changelog.return_value = []
        entries = manager.get_changelog("PROJ1-1")
        assert entries == []


# ── get_transitions ─────────────────────────────────────────────────


class TestManagerGetTransitions:
    def test_returns_parsed_transitions(self, manager, jira_client):
        jira_client.get_transitions.return_value = [
            {"id": "31", "name": "Start Progress", "to": {"name": "In Progress"}},
            {"id": "41", "name": "Close Issue", "to": {"name": "Closed"}},
        ]
        transitions = manager.get_transitions("PROJ1-1")
        assert len(transitions) == 2
        assert transitions[0].name == "Start Progress"
        assert transitions[0].to_status == "In Progress"
        assert transitions[1].name == "Close Issue"

    def test_empty_transitions(self, manager, jira_client):
        jira_client.get_transitions.return_value = []
        transitions = manager.get_transitions("PROJ1-1")
        assert transitions == []
