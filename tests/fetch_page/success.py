from unittest.mock import patch

from wiki_cli.cli_pages import fetch_page
from wiki_cli.models import Page

INPUT_PATCH = "builtins.input"


def test_fetch_by_id(mock_manager, capsys):
    page = Page(
        id=5,
        path="docs/intro",
        title="Introduction",
        content="# Welcome",
        description="A brief intro",
        locale="en",
        isPublished=True,
        isPrivate=False,
        tags=["wiki", "docs"],
    )
    mock_manager.get_by_id.return_value = page
    inputs = iter(["1", "5"])

    with patch(INPUT_PATCH, side_effect=inputs):
        fetch_page(mock_manager)

    mock_manager.get_by_id.assert_called_once_with(5)

    output = capsys.readouterr().out
    assert "ID:          5" in output
    assert "Path:        docs/intro" in output
    assert "Title:       Introduction" in output
    assert "Description: A brief intro" in output
    assert "Tags:        ['wiki', 'docs']" in output
    assert "Published:   True" in output
    assert "Private:     False" in output
    assert "# Welcome" in output
    print(f"\n  [CALL] get_by_id(5)")
    print(f"  [OUTPUT]\n{output}")


def test_fetch_by_path(mock_manager, capsys):
    page = Page(
        id=8,
        path="projects/app",
        title="App Overview",
        content="# App",
        description="App docs",
        locale="bn",
        isPublished=True,
        isPrivate=False,
        tags=["project"],
    )
    mock_manager.get_by_path.return_value = page
    inputs = iter(["2", "projects/app", "bn"])

    with patch(INPUT_PATCH, side_effect=inputs):
        fetch_page(mock_manager)

    mock_manager.get_by_path.assert_called_once_with("projects/app", locale="bn")

    output = capsys.readouterr().out
    assert "ID:          8" in output
    assert "Path:        projects/app" in output
    assert "Title:       App Overview" in output
    print(f"\n  [CALL] get_by_path('projects/app', locale='bn')")
    print(f"  [OUTPUT]\n{output}")


def test_fetch_default_choice_is_id(mock_manager, capsys):
    page = Page(id=1, path="x", title="X", content="hi")
    mock_manager.get_by_id.return_value = page
    inputs = iter(["", "1"])

    with patch(INPUT_PATCH, side_effect=inputs):
        fetch_page(mock_manager)

    mock_manager.get_by_id.assert_called_once_with(1)
    output = capsys.readouterr().out
    assert "ID:          1" in output
    print(f"\n  [DEFAULT] Empty choice defaults to by-ID")
