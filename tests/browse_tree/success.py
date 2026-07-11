from unittest.mock import patch

from wiki_cli.cli_pages import browse_tree
from wiki_cli.models import Page

INPUT_PATCH = "builtins.input"


def test_browse_tree_structure(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="docs/intro", title="Intro", isPublished=True),
        Page(id=2, path="docs/setup", title="Setup", isPublished=True),
        Page(id=3, path="projects/app", title="App", isPublished=False),
    ]
    inputs = iter([""])

    with patch(INPUT_PATCH, side_effect=inputs):
        browse_tree(mock_manager)

    output = capsys.readouterr().out
    assert "/ (root)" in output
    assert "docs/" in output
    assert "intro (id=1)" in output
    assert "setup (id=2)" in output
    assert "projects/" in output
    assert "app (id=3) [draft]" in output
    print(f"\n  [TREE] 3 pages in tree structure")


def test_browse_empty(mock_manager, capsys):
    mock_manager.list_all.return_value = []
    inputs = iter([])

    with patch(INPUT_PATCH, side_effect=inputs):
        browse_tree(mock_manager)

    output = capsys.readouterr().out
    assert "No pages found." in output
    print(f"\n  [TREE] Empty")


def test_browse_view_page(mock_manager, capsys):
    tree_page = Page(id=1, path="docs/intro", title="Intro", isPublished=True)
    detail_page = Page(
        id=1, path="docs/intro", title="Intro",
        content="# Hello", description="Desc", isPublished=True, isPrivate=False, tags=["wiki"],
    )
    mock_manager.list_all.return_value = [tree_page]
    mock_manager.get_by_id.return_value = detail_page
    inputs = iter(["1"])

    with patch(INPUT_PATCH, side_effect=inputs):
        browse_tree(mock_manager)

    mock_manager.get_by_id.assert_called_once_with(1)
    output = capsys.readouterr().out
    assert "ID:          1" in output
    assert "# Hello" in output
    print(f"\n  [TREE] Viewed page details")


def test_browse_skip_view(mock_manager, capsys):
    mock_manager.list_all.return_value = [
        Page(id=1, path="x", title="X", isPublished=True),
    ]
    inputs = iter([""])

    with patch(INPUT_PATCH, side_effect=inputs):
        browse_tree(mock_manager)

    mock_manager.get_by_id.assert_not_called()
    print(f"\n  [TREE] Skipped page view")
