from unittest.mock import patch

from wiki_cli.cli_history import diff_two_revisions
from wiki_cli.models import PageVersion

INPUT_PATCH = "builtins.input"


def test_diff_success(mock_manager, capsys):
    mock_manager.get_version.side_effect = [
        PageVersion(versionId=3, content="old line", versionDate="2024-01-01"),
        PageVersion(versionId=5, content="new line", versionDate="2024-01-10"),
    ]
    inputs = iter(["1", "3", "5"])

    with patch(INPUT_PATCH, side_effect=inputs):
        diff_two_revisions(mock_manager)

    output = capsys.readouterr().out
    assert "--- v3" in output
    assert "+++ v5" in output
    assert "-old line" in output
    assert "+new line" in output
    print(f"\n  [DIFF] Shown diff between v3 and v5")


def test_diff_no_changes(mock_manager, capsys):
    mock_manager.get_version.side_effect = [
        PageVersion(versionId=1, content="same", versionDate="2024-01-01"),
        PageVersion(versionId=2, content="same", versionDate="2024-01-02"),
    ]
    inputs = iter(["1", "1", "2"])

    with patch(INPUT_PATCH, side_effect=inputs):
        diff_two_revisions(mock_manager)

    output = capsys.readouterr().out
    assert "No differences found" in output
    print(f"\n  [DIFF] No differences")


def test_diff_invalid_page_id(mock_manager, capsys):
    inputs = iter(["abc", "1", "2"])

    with patch(INPUT_PATCH, side_effect=inputs):
        diff_two_revisions(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid page ID." in output
    print(f"\n  [VALIDATION] Invalid page ID")


def test_diff_invalid_version_id(mock_manager, capsys):
    inputs = iter(["1", "abc", "2"])

    with patch(INPUT_PATCH, side_effect=inputs):
        diff_two_revisions(mock_manager)

    mock_manager.get_version.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid version ID." in output
    print(f"\n  [VALIDATION] Invalid version ID")
