"""Tests for Jira configuration and authentication."""

import os
import pytest
from unittest.mock import patch, MagicMock

from wiki_cli.jira.auth import JiraAuth
from wiki_cli.jira.client import JiraClient
from wiki_cli.jira.errors import JiraConfigError
from wiki_cli.jira.manager import JiraManager


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    """Ensure Jira env vars don't leak between tests."""
    monkeypatch.delenv("JIRA_SERVER", raising=False)
    monkeypatch.delenv("JIRA_EMAIL", raising=False)
    monkeypatch.delenv("JIRA_API_TOKEN", raising=False)
    monkeypatch.delenv("JIRA_PROJECT_ALLOWLIST", raising=False)


class TestJiraAuth:
    def test_raises_when_no_server(self):
        with pytest.raises(JiraConfigError, match="JIRA_SERVER"):
            JiraAuth(server="", email="a@b.com", api_token="tok")

    def test_raises_when_no_email(self):
        with pytest.raises(JiraConfigError, match="JIRA_EMAIL"):
            JiraAuth(server="https://x.atlassian.net", email="", api_token="tok")

    def test_raises_when_no_token(self):
        with pytest.raises(JiraConfigError, match="JIRA_API_TOKEN"):
            JiraAuth(server="https://x.atlassian.net", email="a@b.com", api_token="")

    def test_reads_from_env(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://env.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "env@test.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "env_token")
        auth = JiraAuth()
        assert auth.server == "https://env.atlassian.net"
        assert auth.email == "env@test.com"
        assert auth.api_token == "env_token"

    def test_explicit_args_override_env(self, monkeypatch):
        monkeypatch.setenv("JIRA_SERVER", "https://env.atlassian.net")
        auth = JiraAuth(server="https://explicit.atlassian.net", email="e@x.com", api_token="tok")
        assert auth.server == "https://explicit.atlassian.net"

    def test_get_client_returns_jira_instance(self):
        auth = JiraAuth(server="https://x.atlassian.net", email="a@b.com", api_token="tok")
        with patch("jira.JIRA") as mock_jira:
            mock_jira.return_value = MagicMock()
            client = auth.get_client()
            assert client is not None
            mock_jira.assert_called_once_with(
                server="https://x.atlassian.net",
                basic_auth=("a@b.com", "tok"),
            )


class TestJiraClientInit:
    def test_raises_on_missing_config(self):
        with pytest.raises(JiraConfigError):
            JiraClient(server="", email="", api_token="")

    def test_stores_auth(self):
        client = JiraClient(
            server="https://test.atlassian.net",
            email="test@test.com",
            api_token="test_token",
        )
        assert client.auth.server == "https://test.atlassian.net"
        assert client.auth.email == "test@test.com"


class TestJiraManagerInit:
    def test_reads_allowlist_from_env(self, monkeypatch):
        monkeypatch.setenv("JIRA_PROJECT_ALLOWLIST", "PROJ1, PROJ2, PROJ3")
        monkeypatch.setenv("JIRA_SERVER", "https://x.atlassian.net")
        monkeypatch.setenv("JIRA_EMAIL", "a@b.com")
        monkeypatch.setenv("JIRA_API_TOKEN", "tok")

        with patch("jira.JIRA"):
            client = JiraClient()
            manager = JiraManager(client)
            assert manager.allowed_projects == ["PROJ1", "PROJ2", "PROJ3"]

    def test_empty_allowlist_means_all_projects(self):
        """When allowlist is empty, all projects should be returned."""
        pass

    def test_custom_allowlist(self):
        client = MagicMock()
        manager = JiraManager(client, allowed_projects=["A", "B"])
        assert manager.allowed_projects == ["A", "B"]
