"""Tests for JiraClient with mocked JIRA library."""

import pytest
from unittest.mock import MagicMock, patch

from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.errors import JiraConfigError
from wiki_cli.exceptions import WikiJSError


@pytest.fixture
def mock_jira_lib():
    """Mock the jira.JIRA class at the jira module level."""
    with patch("jira.JIRA") as mock_cls:
        instance = MagicMock()
        mock_cls.return_value = instance
        yield instance


@pytest.fixture
def client(mock_jira_lib):
    return JiraClient(
        server="https://test.atlassian.net",
        email="test@test.com",
        api_token="test_token",
    )


class TestJiraClientConnection:
    def test_test_connection_success(self, client, mock_jira_lib):
        mock_jira_lib.myself.return_value = {
            "displayName": "Nasimul",
            "emailAddress": "nasimul@test.com",
        }
        result = client.test_connection()
        assert result["displayName"] == "Nasimul"
        assert result["emailAddress"] == "nasimul@test.com"

    def test_test_connection_failure(self, client, mock_jira_lib):
        mock_jira_lib.myself.side_effect = Exception("Unauthorized")
        with pytest.raises(WikiJSError, match="connection test failed"):
            client.test_connection()


class TestJiraClientProjects:
    def test_list_projects(self, client, mock_jira_lib):
        proj1 = MagicMock()
        proj1.raw = {"key": "A", "name": "Alpha"}
        proj2 = MagicMock()
        proj2.raw = {"key": "B", "name": "Beta"}
        mock_jira_lib.projects.return_value = [proj1, proj2]

        result = client.list_projects()
        assert len(result) == 2
        assert result[0]["key"] == "A"
        assert result[1]["key"] == "B"

    def test_list_projects_error(self, client, mock_jira_lib):
        mock_jira_lib.projects.side_effect = Exception("Network error")
        with pytest.raises(WikiJSError, match="Failed to list"):
            client.list_projects()

    def test_get_project(self, client, mock_jira_lib):
        mock_proj = MagicMock()
        mock_proj.raw = {"key": "PROJ1", "name": "Project 1"}
        mock_jira_lib.project.return_value = mock_proj

        result = client.get_project("PROJ1")
        assert result["key"] == "PROJ1"

    def test_get_project_not_found(self, client, mock_jira_lib):
        mock_jira_lib.project.side_effect = Exception("Not Found")
        with pytest.raises(WikiJSError, match="Failed to get project"):
            client.get_project("NOPE")


class TestJiraClientSearch:
    def test_search_issues(self, client, mock_jira_lib):
        issue1 = MagicMock()
        issue1.raw = {"key": "P-1", "fields": {"summary": "Test"}}
        mock_jira_lib.search_issues.return_value = [issue1]

        result = client.search_issues("project = P")
        assert len(result) == 1
        assert result[0]["key"] == "P-1"
        mock_jira_lib.search_issues.assert_called_once_with("project = P", maxResults=50)

    def test_search_with_custom_max(self, client, mock_jira_lib):
        mock_jira_lib.search_issues.return_value = []
        client.search_issues("project = P", max_results=10)
        mock_jira_lib.search_issues.assert_called_once_with("project = P", maxResults=10)

    def test_search_error(self, client, mock_jira_lib):
        mock_jira_lib.search_issues.side_effect = Exception("JQL parse error")
        with pytest.raises(WikiJSError, match="Jira search failed"):
            client.search_issues("invalid jql")


class TestJiraClientIssue:
    def test_get_issue(self, client, mock_jira_lib):
        mock_issue = MagicMock()
        mock_issue.raw = {"key": "PROJ-42", "fields": {"summary": "Fix bug"}}
        mock_jira_lib.issue.return_value = mock_issue

        result = client.get_issue("PROJ-42")
        assert result["key"] == "PROJ-42"

    def test_get_issue_not_found(self, client, mock_jira_lib):
        mock_jira_lib.issue.side_effect = Exception("Not Found")
        with pytest.raises(WikiJSError, match="Failed to get issue"):
            client.get_issue("NOPE-1")

    def test_get_comments(self, client, mock_jira_lib):
        mock_issue = MagicMock()
        comment1 = MagicMock()
        comment1.raw = {"id": "100", "body": "Hello"}
        comment2 = MagicMock()
        comment2.raw = {"id": "101", "body": "World"}
        mock_issue.fields.comment.comments = [comment1, comment2]
        mock_jira_lib.issue.return_value = mock_issue

        result = client.get_comments("PROJ-1")
        assert len(result) == 2
        assert result[0]["body"] == "Hello"

    def test_get_changelog(self, client, mock_jira_lib):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "values": [
                {"id": "500", "items": [{"field": "status"}]},
                {"id": "501", "items": [{"field": "assignee"}]},
            ]
        }
        mock_response.raise_for_status = MagicMock()
        mock_jira_lib._session.get.return_value = mock_response

        result = client.get_changelog("PROJ-1")
        assert len(result) == 2
        assert result[0]["id"] == "500"
        assert result[1]["id"] == "501"

    def test_get_transitions(self, client, mock_jira_lib):
        mock_jira_lib.transitions.return_value = [
            {"id": "31", "name": "Start", "to": {"name": "In Progress"}},
        ]
        result = client.get_transitions("PROJ-1")
        assert len(result) == 1
        assert result[0]["name"] == "Start"
