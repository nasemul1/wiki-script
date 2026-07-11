import os
from unittest.mock import patch

from wiki_cli.cli_pages import import_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def test_import_with_frontmatter(mock_manager, capsys, tmp_path):
    md_file = tmp_path / "page.md"
    md_file.write_text("---\npath: imported/page\ntitle: Imported\n---\n# Content here")
    mock_manager.create.return_value = PageResponse(
        succeeded=True, message="OK", page=Page(id=10, path="imported/page", title="Imported"),
    )
    inputs = iter([str(md_file), "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        import_page(mock_manager)

    created = mock_manager.create.call_args[0][0]
    assert created.path == "imported/page"
    assert created.title == "Imported"
    assert created.content == "# Content here"
    output = capsys.readouterr().out
    assert "Imported page (id=10)" in output
    print(f"\n  [IMPORT] From frontmatter: path={created.path}, title={created.title}")


def test_import_without_frontmatter(mock_manager, capsys, tmp_path):
    md_file = tmp_path / "plain.md"
    md_file.write_text("# Plain content")
    mock_manager.create.return_value = PageResponse(
        succeeded=True, message="OK", page=Page(id=20, path="plain", title="Plain Page"),
    )
    inputs = iter([str(md_file), "plain", "Plain Page"])

    with patch(INPUT_PATCH, side_effect=inputs):
        import_page(mock_manager)

    created = mock_manager.create.call_args[0][0]
    assert created.path == "plain"
    assert created.title == "Plain Page"
    assert created.content == "# Plain content"
    print(f"\n  [IMPORT] From prompts: path={created.path}, title={created.title}")


def test_import_file_not_found(mock_manager, capsys):
    inputs = iter(["nonexistent.md"])

    with patch(INPUT_PATCH, side_effect=inputs):
        with patch("os.path.isfile", return_value=False):
            import_page(mock_manager)

    mock_manager.create.assert_not_called()
    output = capsys.readouterr().out
    assert "File not found" in output
    print(f"\n  [VALIDATION] File not found")


def test_import_empty_filename(mock_manager, capsys):
    inputs = iter([""])

    with patch(INPUT_PATCH, side_effect=inputs):
        import_page(mock_manager)

    mock_manager.create.assert_not_called()
    output = capsys.readouterr().out
    assert "Filename is required." in output
    print(f"\n  [VALIDATION] Empty filename rejected")
