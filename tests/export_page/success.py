import os
from unittest.mock import patch, mock_open

from wiki_cli.cli_pages import export_page
from wiki_cli.models import Page

INPUT_PATCH = "builtins.input"


def test_export_success(mock_manager, capsys, tmp_path):
    page = Page(
        id=1, path="docs/intro", title="Intro", content="# Hello",
        description="Desc", tags=["wiki"], isPublished=True, isPrivate=False,
        locale="en", editor="markdown",
    )
    mock_manager.get_by_id.return_value = page
    export_file = str(tmp_path / "exported.md")
    inputs = iter(["1", export_file])

    with patch(INPUT_PATCH, side_effect=inputs):
        export_page(mock_manager)

    assert os.path.isfile(export_file)
    with open(export_file) as f:
        content = f.read()
    assert "title: Intro" in content
    assert "path: docs/intro" in content
    assert "# Hello" in content
    assert "tags: [wiki]" in content
    output = capsys.readouterr().out
    assert "Exported page 1" in output
    print(f"\n  [EXPORT] Written to {export_file}")


def test_export_default_filename(mock_manager, capsys, tmp_path):
    page = Page(id=1, path="docs/intro", title="Intro", content="x")
    mock_manager.get_by_id.return_value = page
    inputs = iter(["1", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("builtins.open", mock_open()) as mocked_file:
            export_page(mock_manager)

    mocked_file.assert_called_once_with("docs_intro.md", "w", encoding="utf-8")
    print(f"\n  [EXPORT] Default filename: docs_intro.md")


def test_export_invalid_id(mock_manager, capsys):
    inputs = iter(["abc"])

    with patch(INPUT_PATCH, side_effect=inputs):
        export_page(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    output = capsys.readouterr().out
    assert "Invalid ID." in output
    print(f"\n  [VALIDATION] Non-numeric ID rejected")
