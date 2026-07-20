"""Tests for JQL validation and injection prevention."""

import pytest

from wiki_cli.jira.jql import JQLValidator
from wiki_cli.jira.errors import JiraValidationError


@pytest.fixture
def validator():
    return JQLValidator()


# ── Safe queries ────────────────────────────────────────────────────


class TestSafeQueries:
    def test_valid_simple_query(self, validator):
        result = validator.validate("project = PROJ AND status = Open")
        assert result == "project = PROJ AND status = Open"

    def test_valid_complex_query(self, validator):
        jql = 'project = PROJ AND status = "In Progress" AND assignee = "Nasimul"'
        result = validator.validate(jql)
        assert result == jql

    def test_valid_order_by(self, validator):
        result = validator.validate("project = PROJ ORDER BY created DESC")
        assert "ORDER BY" in result

    def test_valid_with_parentheses(self, validator):
        result = validator.validate("project = PROJ AND (status = Open OR status = Closed)")
        assert result is not None


# ── Forbidden keywords ─────────────────────────────────────────────


class TestForbiddenKeywords:
    @pytest.mark.parametrize("keyword", [
        "DROP", "drop", "Drop",
        "DELETE", "delete",
        "UPDATE", "update",
        "INSERT", "insert",
        "EXEC", "exec",
        "EXECUTE", "execute",
        "ALTER", "alter",
        "CREATE", "create",
        "TRUNCATE", "truncate",
        "GRANT", "grant",
        "REVOKE", "revoke",
    ])
    def test_forbidden_keywords_rejected(self, validator, keyword):
        with pytest.raises(JiraValidationError, match="Forbidden keyword"):
            validator.validate(f"project = PROJ; {keyword} TABLE issues")

    def test_drop_in_union(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden keyword"):
            validator.validate("project = PROJ UNION DROP TABLE users")


# ── Forbidden patterns ─────────────────────────────────────────────


class TestForbiddenPatterns:
    @pytest.mark.parametrize("pattern", [
        "UNION",
        "union",
        "Or 1=1",
        "OR 1=1",
        "OR 1 = 1",
        "1=1",
        "--",
        ";",
        "/*",
        "*/",
        "CHAR(",
        "CONCAT(",
    ])
    def test_forbidden_patterns_rejected(self, validator, pattern):
        with pytest.raises(JiraValidationError, match="Forbidden pattern"):
            validator.validate(f"project = PROJ {pattern} x")


# ── Empty / blank queries ──────────────────────────────────────────


class TestEmptyQueries:
    def test_empty_string_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="cannot be empty"):
            validator.validate("")

    def test_whitespace_only_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="cannot be empty"):
            validator.validate("   ")

    def test_none_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="cannot be empty"):
            validator.validate(None)


# ── Build safe queries ─────────────────────────────────────────────


class TestBuildSearchQuery:
    def test_project_only(self, validator):
        q = validator.build_search_query(project="PROJ")
        assert q == 'project = "PROJ" order by created DESC'

    def test_status_only(self, validator):
        q = validator.build_search_query(status="In Progress")
        assert q == 'status = "In Progress" order by created DESC'

    def test_assignee_only(self, validator):
        q = validator.build_search_query(assignee="Nasimul")
        assert q == 'assignee = "Nasimul" order by created DESC'

    def test_multiple_filters(self, validator):
        q = validator.build_search_query(project="PROJ", status="Open", priority="High")
        assert 'project = "PROJ"' in q
        assert 'status = "Open"' in q
        assert 'priority = "High"' in q
        assert " AND " in q
        assert q.endswith("order by created DESC")

    def test_no_filters_raises_error(self, validator):
        with pytest.raises(JiraValidationError, match="At least one filter"):
            validator.build_search_query()

    def test_all_filters(self, validator):
        q = validator.build_search_query(
            project="PROJ", status="Open", assignee="user@test.com",
            priority="Critical", issue_type="Bug"
        )
        assert 'project = "PROJ"' in q
        assert 'status = "Open"' in q
        assert 'assignee = "user@test.com"' in q
        assert 'priority = "Critical"' in q
        assert 'issuetype = "Bug"' in q


# ── Value injection prevention ─────────────────────────────────────


class TestValueInjection:
    def test_quote_in_project_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden character"):
            validator.build_search_query(project='PROJ"; DROP TABLE--')

    def test_semicolon_in_value_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden character"):
            validator.build_search_query(status="Open; DELETE")

    def test_single_quote_in_value_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden character"):
            validator.build_search_query(assignee="user' OR 1=1")

    def test_backslash_in_value_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden character"):
            validator.build_search_query(project="PROJ\\ DROP")

    def test_dash_dash_in_value_rejected(self, validator):
        with pytest.raises(JiraValidationError, match="Forbidden character"):
            validator.build_search_query(assignee="user--comment")
