"""Tests for Jira CLI handlers."""

import pytest
from unittest.mock import MagicMock, patch

from wiki_cli.cli_jira import (
    get_jira_issue,
    get_jira_project,
    list_jira_projects,
    search_jira_issues,
    check_jira_connection,
    view_issue_changelog,
    view_issue_comments,
    view_issue_transitions,
)
from wiki_cli.jira.manager import JiraManager
from wiki_cli.jira.models import (
    JiraChangelogEntry,
    JiraComment,
    JiraIssue,
    JiraProject,
    JiraTransition,
)
from wiki_cli.jira.errors import JiraNotFoundError

INPUT_PATCH = "builtins.input"


@pytest.fixture
def mock_manager():
    return MagicMock(spec=JiraManager)


class TestCheckJiraConnection:
    def test_success(self, mock_manager, capsys):
        mock_manager.test_connection.return_value = {
            "displayName": "Nasimul",
            "emailAddress": "nasimul@test.com",
        }
        check_jira_connection(mock_manager)
        output = capsys.readouterr().out
        assert "Nasimul" in output
        assert "nasimul@test.com" in output


class TestListJiraProjects:
    def test_projects_found(self, mock_manager, capsys):
        mock_manager.list_projects.return_value = [
            JiraProject(key="A", name="Alpha", project_type="business"),
            JiraProject(key="B", name="Beta", project_type="software"),
        ]
        list_jira_projects(mock_manager)
        output = capsys.readouterr().out
        assert "Alpha" in output
        assert "Beta" in output
        assert "Total: 2" in output

    def test_no_projects(self, mock_manager, capsys):
        mock_manager.list_projects.return_value = []
        list_jira_projects(mock_manager)
        output = capsys.readouterr().out
        assert "No accessible projects" in output


class TestGetJiraProject:
    def test_success(self, mock_manager, capsys):
        mock_manager.get_project.return_value = JiraProject(
            key="PROJ1", name="My Project", lead="Nasimul"
        )
        with patch(INPUT_PATCH, return_value="PROJ1"):
            get_jira_project(mock_manager)
        output = capsys.readouterr().out
        assert "PROJ1" in output
        assert "My Project" in output

    def test_empty_key(self, mock_manager, capsys):
        with patch(INPUT_PATCH, return_value=""):
            get_jira_project(mock_manager)
        output = capsys.readouterr().out
        assert "required" in output.lower()


class TestSearchJiraIssues:
    def test_search_by_filters(self, mock_manager, capsys):
        mock_manager.search_issues.return_value = [
            JiraIssue(
                key="P-1", summary="Bug fix", status="Open",
                priority="High", issue_type="Bug",
            ),
        ]
        inputs = iter(["1", "PROJ1", "", "", "", "", ""])
        with patch(INPUT_PATCH, side_effect=inputs):
            search_jira_issues(mock_manager)
        output = capsys.readouterr().out
        assert "P-1" in output
        assert "Bug fix" in output

    def test_search_no_results(self, mock_manager, capsys):
        mock_manager.search_issues.return_value = []
        inputs = iter(["1", "", "", "", "", "", ""])
        with patch(INPUT_PATCH, side_effect=inputs):
            search_jira_issues(mock_manager)
        output = capsys.readouterr().out
        assert "No issues found" in output

    def test_search_by_jql(self, mock_manager, capsys):
        mock_manager.search_issues.return_value = [
            JiraIssue(
                key="P-2", summary="Task", status="Closed",
                priority="Low", issue_type="Task",
            ),
        ]
        inputs = iter(["2", "project = P", ""])
        with patch(INPUT_PATCH, side_effect=inputs):
            search_jira_issues(mock_manager)
        output = capsys.readouterr().out
        assert "P-2" in output


class TestGetJiraIssue:
    def test_success(self, mock_manager, capsys):
        mock_manager.get_issue.return_value = JiraIssue(
            key="PROJ-42",
            summary="Fix login",
            description="Users can't login",
            status="In Progress",
            priority="Critical",
            issue_type="Bug",
            labels=["auth"],
            assignee="Nasimul",
            reporter="Naveed",
            created="2026-07-15",
            updated="2026-07-16",
        )
        with patch(INPUT_PATCH, return_value="PROJ-42"):
            get_jira_issue(mock_manager)
        output = capsys.readouterr().out
        assert "PROJ-42" in output
        assert "Fix login" in output
        assert "In Progress" in output
        assert "Critical" in output
        assert "Nasimul" in output

    def test_empty_key(self, mock_manager, capsys):
        with patch(INPUT_PATCH, return_value=""):
            get_jira_issue(mock_manager)
        output = capsys.readouterr().out
        assert "required" in output.lower()


class TestViewIssueComments:
    def test_comments_found(self, mock_manager, capsys):
        mock_manager.get_comments.return_value = [
            JiraComment(id="1", author="Nasimul", body="Working on it"),
            JiraComment(id="2", author="Naveed", body="Thanks"),
        ]
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_comments(mock_manager)
        output = capsys.readouterr().out
        assert "Nasimul" in output
        assert "Working on it" in output
        assert "Total: 2" in output

    def test_no_comments(self, mock_manager, capsys):
        mock_manager.get_comments.return_value = []
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_comments(mock_manager)
        output = capsys.readouterr().out
        assert "No comments" in output


class TestViewIssueChangelog:
    def test_changelog_found(self, mock_manager, capsys):
        mock_manager.get_changelog.return_value = [
            JiraChangelogEntry(
                id="1", author="Nasimul", created="2026-07-15T10:00:00",
                field="status", from_value="Open", to_value="In Progress",
            ),
        ]
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_changelog(mock_manager)
        output = capsys.readouterr().out
        assert "status" in output
        assert "Open" in output
        assert "In Progress" in output

    def test_empty_changelog(self, mock_manager, capsys):
        mock_manager.get_changelog.return_value = []
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_changelog(mock_manager)
        output = capsys.readouterr().out
        assert "No changelog" in output


class TestViewIssueTransitions:
    def test_transitions_found(self, mock_manager, capsys):
        mock_manager.get_transitions.return_value = [
            JiraTransition(id="31", name="Start Progress", to_status="In Progress"),
            JiraTransition(id="41", name="Close", to_status="Closed"),
        ]
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_transitions(mock_manager)
        output = capsys.readouterr().out
        assert "Start Progress" in output
        assert "In Progress" in output
        assert "Total: 2" in output

    def test_no_transitions(self, mock_manager, capsys):
        mock_manager.get_transitions.return_value = []
        with patch(INPUT_PATCH, return_value="PROJ-1"):
            view_issue_transitions(mock_manager)
        output = capsys.readouterr().out
        assert "No available transitions" in output
