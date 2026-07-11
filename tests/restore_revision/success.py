from unittest.mock import patch

from wiki_cli.cli_history import restore_revision
from wiki_cli.models import PageVersion

INPUT_PATCH = "builtins.input"


def test_restore_success(mock_manager, capsys):
    mock_manager.get_version.return_value = PageVersion(
        versionId=3, pageId=1, title="Intro", versionDate="2024-01-01", authorName="Admin",
    )
    mock_manager.restore_version.return_value = True
    inputs = iter(["1", "3", "yes"])

    with patch(INPUT_PATCH, side_effect=inputs):
        restore_revision(mock_manager)

    mock_manager.restore_version.assert_called_once_with(1, 3)
    output = capsys.readouterr().out
    assert "Page restored to version 3." in output
    print(f"\n  [RESTORE] Restored to version 3")


def test_restore_cancelled(mock_manager, capsys):
    mock_manager.get_version.return_value = PageVersion(
        versionId=3, pageId=1, title="Intro", versionDate="2024-01-01", authorName="Admin",
    )
    inputs = iter(["1", "3", "no"])

    with patch(INPUT_PATCH, side_effect=inputs):
        restore_revision(mock_manager)

    mock_manager.restore_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Cancelled." in output
    print(f"\n  [RESTORE] Cancelled")


def test_restore_invalid_page_id(mock_manager, capsys):
    inputs = iter(["abc", "3"])

    with patch(INPUT_PATCH, side_effect=inputs):
        restore_revision(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid page ID." in output
    print(f"\n  [VALIDATION] Invalid page ID")


def test_restore_invalid_version_id(mock_manager, capsys):
    inputs = iter(["1", "abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        restore_revision(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid version ID." in output
    print(f"\n  [VALIDATION] Invalid version ID")
