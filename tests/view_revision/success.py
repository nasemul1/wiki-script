from unittest.mock import patch

from wiki_cli.cli_history import view_specific_revision
from wiki_cli.models import PageVersion

INPUT_PATCH = "builtins.input"


def test_view_revision_success(mock_manager, capsys):
    mock_manager.get_version.return_value = PageVersion(
        versionId=5, pageId=1, path="docs/intro", title="Intro",
        content="# v5 content", versionDate="2024-01-10",
        authorName="Admin", action="update", isPublished=True, tags=["wiki"],
    )
    inputs = iter(["1", "5"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_specific_revision(mock_manager)

    mock_manager.get_version.assert_called_once_with(1, 5)
    output = capsys.readouterr().out
    assert "Version:   5" in output
    assert "# v5 content" in output
    print(f"\n  [REVISION] Viewed version 5")


def test_view_revision_invalid_page_id(mock_manager, capsys):
    inputs = iter(["abc", "5"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_specific_revision(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid page ID." in output
    print(f"\n  [VALIDATION] Invalid page ID")


def test_view_revision_invalid_version_id(mock_manager, capsys):
    inputs = iter(["1", "abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        view_specific_revision(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid version ID." in output
    print(f"\n  [VALIDATION] Invalid version ID")
