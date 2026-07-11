from unittest.mock import patch

from wiki_cli.cli_pages import clone_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def test_clone_success(mock_manager, capsys):
    source = Page(id=1, path="docs/intro", title="Intro", content="# Hi")
    mock_manager.get_by_id.return_value = source
    mock_manager.clone_page.return_value = PageResponse(
        succeeded=True, message="Cloned",
        page=Page(id=2, path="docs/copy", title="Copy"),
    )
    inputs = iter(["1", "docs/copy", "Copy of Intro"])

    with patch(INPUT_PATCH, side_effect=inputs):
        clone_page(mock_manager)

    mock_manager.clone_page.assert_called_once_with(1, "docs/copy", "Copy of Intro")
    output = capsys.readouterr().out
    assert "Cloned page (id=2): docs/copy" in output
    print(f"\n  [CLONE] Source: docs/intro → Target: docs/copy (id=2)")


def test_clone_empty_path(mock_manager, capsys):
    source = Page(id=1, path="docs/intro", title="Intro")
    mock_manager.get_by_id.return_value = source
    inputs = iter(["1", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        clone_page(mock_manager)

    mock_manager.clone_page.assert_not_called()
    output = capsys.readouterr().out
    assert "Path is required." in output
    print(f"\n  [VALIDATION] Empty path rejected")


def test_clone_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        clone_page(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
