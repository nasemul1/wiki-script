"""Jira-related menu handlers."""

from __future__ import annotations

from wiki_cli.jira.manager import JiraManager
from wiki_cli.jira.errors import JiraConfigError


def check_jira_connection(jira: JiraManager) -> None:
    result = jira.test_connection()
    print(f"\nConnected as: {result['displayName']} ({result['emailAddress']})")


def list_jira_projects(jira: JiraManager) -> None:
    projects = jira.list_projects()
    if not projects:
        print("\nNo accessible projects.")
        return

    print(f"\n{'Key':<10} {'Name':<35} {'Type':<15} {'Lead'}")
    print("-" * 75)
    for p in projects:
        print(f"{p.key:<10} {p.name:<35} {p.project_type or 'N/A':<15} {p.lead or 'N/A'}")
    print(f"\nTotal: {len(projects)} project(s)")


def get_jira_project(jira: JiraManager) -> None:
    key = input("Project key (e.g., PROJ): ").strip()
    if not key:
        print("Project key is required.")
        return

    project = jira.get_project(key)
    print(f"\nKey:         {project.key}")
    print(f"Name:        {project.name}")
    print(f"Description: {project.description or 'N/A'}")
    print(f"Lead:        {project.lead or 'N/A'}")
    print(f"Type:        {project.project_type or 'N/A'}")


def search_jira_issues(jira: JiraManager) -> None:
    print("Search by:")
    print("  1. Filter (safe, recommended)")
    print("  2. Raw JQL (validated)")
    choice = input("Choice [1]: ").strip() or "1"

    if choice == "2":
        jql = input("JQL query: ").strip()
        if not jql:
            print("JQL query is required.")
            return
        issues = jira.search_issues(jql=jql)
    else:
        project = input("Project key (leave blank for all): ").strip() or None
        status = input("Status (leave blank for all): ").strip() or None
        assignee = input("Assignee (leave blank for all): ").strip() or None
        priority = input("Priority (leave blank for all): ").strip() or None
        issue_type = input("Issue type (leave blank for all): ").strip() or None

        issues = jira.search_issues(
            project=project,
            status=status,
            assignee=assignee,
            priority=priority,
            issue_type=issue_type,
        )

    if not issues:
        print("\nNo issues found.")
        return

    _print_issue_table(issues)
    print(f"\nTotal: {len(issues)} issue(s)")


def get_jira_issue(jira: JiraManager) -> None:
    key = input("Issue key (e.g., PROJ-123): ").strip()
    if not key:
        print("Issue key is required.")
        return

    issue = jira.get_issue(key)
    print(f"\n{'=' * 60}")
    print(f"Key:        {issue.key}")
    print(f"Summary:    {issue.summary}")
    print(f"Status:     {issue.status}")
    print(f"Priority:   {issue.priority}")
    print(f"Type:       {issue.issue_type}")
    print(f"Assignee:   {issue.assignee or 'Unassigned'}")
    print(f"Reporter:   {issue.reporter or 'N/A'}")
    print(f"Labels:     {', '.join(issue.labels) if issue.labels else 'None'}")
    print(f"Created:    {issue.created}")
    print(f"Updated:    {issue.updated}")
    print(f"{'=' * 60}")
    if issue.description:
        print(f"\nDescription:\n{issue.description}")
    else:
        print("\nNo description.")


def view_issue_comments(jira: JiraManager) -> None:
    key = input("Issue key (e.g., PROJ-123): ").strip()
    if not key:
        print("Issue key is required.")
        return

    comments = jira.get_comments(key)
    if not comments:
        print(f"\nNo comments on {key}.")
        return

    print(f"\n--- Comments on {key} ---")
    for i, c in enumerate(comments, 1):
        print(f"\n[{i}] {c.author} — {c.created}")
        print(f"    {c.body[:200]}{'...' if len(c.body) > 200 else ''}")
    print(f"\nTotal: {len(comments)} comment(s)")


def view_issue_changelog(jira: JiraManager) -> None:
    key = input("Issue key (e.g., PROJ-123): ").strip()
    if not key:
        print("Issue key is required.")
        return

    changelog = jira.get_changelog(key)
    if not changelog:
        print(f"\nNo changelog entries for {key}.")
        return

    print(f"\n--- Changelog for {key} ---")
    print(f"{'Date':<22} {'Author':<20} {'Field':<15} {'From':<20} {'To'}")
    print("-" * 95)
    for entry in changelog:
        date = entry.created[:19] if entry.created else ""
        from_val = (entry.from_value or "")[:20]
        to_val = (entry.to_value or "")[:20]
        print(f"{date:<22} {entry.author:<20} {entry.field:<15} {from_val:<20} {to_val}")
    print(f"\nTotal: {len(changelog)} change(s)")


def view_issue_transitions(jira: JiraManager) -> None:
    key = input("Issue key (e.g., PROJ-123): ").strip()
    if not key:
        print("Issue key is required.")
        return

    transitions = jira.get_transitions(key)
    if not transitions:
        print(f"\nNo available transitions for {key}.")
        return

    print(f"\n--- Available transitions for {key} ---")
    print(f"{'ID':<8} {'Name':<25} {'To Status'}")
    print("-" * 50)
    for t in transitions:
        print(f"{t.id:<8} {t.name:<25} {t.to_status}")
    print(f"\nTotal: {len(transitions)} transition(s)")


def _print_issue_table(issues) -> None:
    print(f"\n{'Key':<14} {'Status':<15} {'Priority':<10} {'Type':<12} {'Summary'}")
    print("-" * 85)
    for issue in issues:
        summary = issue.summary[:40] + "..." if len(issue.summary) > 40 else issue.summary
        print(f"{issue.key:<14} {issue.status:<15} {issue.priority:<10} {issue.issue_type:<12} {summary}")
