"""Tests for Jira AI tool dispatch."""

import json
import pytest
from unittest.mock import MagicMock, patch

from wiki_cli.ai.agent import WikiAgent
from wiki_cli.ai.tools import TOOLS
from wiki_cli.jira.models import (
    JiraIssue,
    JiraProject,
)


@pytest.fixture
def agent():
    """Create a WikiAgent with mocked internals."""
    with patch("wiki_cli.ai.agent.WikiJSClient"), \
         patch("wiki_cli.ai.agent.PagesManager"), \
         patch("wiki_cli.ai.agent.AIConfig"):
        a = WikiAgent.__new__(WikiAgent)
        a.pages = MagicMock()
        a.jira_manager = MagicMock()
        a.client = MagicMock()
        a.messages = []
        a.quiet = True
        yield a


class TestJiraToolsInToolList:
    def test_all_jira_tools_present(self):
        tool_names = [t["function"]["name"] for t in TOOLS]
        expected = [
            "jira_test_connection",
            "jira_list_projects",
            "jira_search_issues",
            "jira_get_issue",
            "jira_get_comments",
            "jira_get_changelog",
            "jira_get_transitions",
        ]
        for name in expected:
            assert name in tool_names, f"{name} missing from TOOLS"

    def test_jira_tool_schemas_have_required_fields(self):
        for tool in TOOLS:
            name = tool["function"]["name"]
            if name.startswith("jira_"):
                assert "description" in tool["function"]
                assert "parameters" in tool["function"]
                assert "type" in tool
                assert tool["type"] == "function"


class TestJiraToolHandlers:
    def test_jira_test_connection(self, agent):
        agent.jira_manager.test_connection.return_value = {
            "displayName": "Nasimul",
            "emailAddress": "n@test.com",
        }
        result = agent._tool_jira_test_connection({})
        assert result["displayName"] == "Nasimul"

    def test_jira_test_connection_not_configured(self, agent):
        agent.jira_manager = None
        result = agent._tool_jira_test_connection({})
        assert "error" in result
        assert "not configured" in result["error"]

    def test_jira_list_projects(self, agent):
        agent.jira_manager.list_projects.return_value = [
            JiraProject(key="A", name="Alpha"),
        ]
        result = agent._tool_jira_list_projects({})
        assert result["total"] == 1
        assert result["projects"][0]["key"] == "A"

    def test_jira_search_issues(self, agent):
        agent.jira_manager.search_issues.return_value = [
            JiraIssue(
                key="P-1", summary="Test", status="Open",
                priority="High", issue_type="Bug",
            ),
        ]
        result = agent._tool_jira_search_issues({"project": "P"})
        assert result["total"] == 1
        assert result["issues"][0]["key"] == "P-1"

    def test_jira_get_issue(self, agent):
        agent.jira_manager.get_issue.return_value = JiraIssue(
            key="P-42", summary="Fix", status="Open",
            priority="Medium", issue_type="Task",
        )
        result = agent._tool_jira_get_issue({"issue_key": "P-42"})
        assert result["key"] == "P-42"

    def test_jira_get_comments(self, agent):
        agent.jira_manager.get_comments.return_value = []
        result = agent._tool_jira_get_comments({"issue_key": "P-1"})
        assert result["total"] == 0

    def test_jira_get_changelog(self, agent):
        agent.jira_manager.get_changelog.return_value = []
        result = agent._tool_jira_get_changelog({"issue_key": "P-1"})
        assert result["total"] == 0

    def test_jira_get_transitions(self, agent):
        agent.jira_manager.get_transitions.return_value = []
        result = agent._tool_jira_get_transitions({"issue_key": "P-1"})
        assert result["total"] == 0

    def test_jira_not_configured_returns_error(self, agent):
        agent.jira_manager = None
        for method in [
            "_tool_jira_list_projects",
            "_tool_jira_search_issues",
            "_tool_jira_get_comments",
            "_tool_jira_get_changelog",
            "_tool_jira_get_transitions",
        ]:
            result = getattr(agent, method)({"issue_key": "P-1"})
            assert "error" in result

    def test_jira_get_issue_not_configured(self, agent):
        agent.jira_manager = None
        result = agent._tool_jira_get_issue({"issue_key": "P-1"})
        assert "error" in result


class TestJiraToolDispatch:
    def test_dispatch_routes_to_jira_handler(self, agent):
        agent.jira_manager.test_connection.return_value = {"displayName": "Test"}
        args_json = json.dumps({})
        result = agent._execute_tool("jira_test_connection", args_json)
        assert result["success"] is True
        assert result["data"]["displayName"] == "Test"

    def test_dispatch_jira_search(self, agent):
        agent.jira_manager.search_issues.return_value = []
        args_json = json.dumps({"project": "PROJ"})
        result = agent._execute_tool("jira_search_issues", args_json)
        assert result["success"] is True
        assert result["data"]["total"] == 0

    def test_dispatch_unknown_tool(self, agent):
        result = agent._execute_tool("unknown_tool", "{}")
        assert result["success"] is False
        assert "Unknown tool" in result["error"]


class TestJiraSummarize:
    def test_summarize_args_jira_search(self, agent):
        result = agent._summarize_args("jira_search_issues", {"project": "PROJ"})
        assert "PROJ" in result

    def test_summarize_args_jira_get_issue(self, agent):
        result = agent._summarize_args("jira_get_issue", {"issue_key": "P-1"})
        assert "P-1" in result

    def test_summarize_result_jira_projects(self, agent):
        result = agent._summarize_result("jira_list_projects", {"total": 5})
        assert "5 projects" in result

    def test_summarize_result_jira_search(self, agent):
        result = agent._summarize_result("jira_search_issues", {"total": 3})
        assert "3 issues" in result

    def test_summarize_result_jira_not_configured(self, agent):
        result = agent._summarize_result("jira_test_connection", {"error": "not configured"})
        assert "not configured" in result
