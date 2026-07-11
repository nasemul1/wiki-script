from unittest.mock import patch

from wiki_cli.cli_pages import update_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def _existing_page():
    return Page(
        id=1,
        path="docs/intro",
        title="Introduction",
        content="# Original content",
        description="Old description",
        locale="en",
        isPublished=True,
        isPrivate=False,
        tags=["wiki"],
    )


def test_replace_content(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    mock_manager.update.return_value = PageResponse(
        succeeded=True, message="Page updated"
    )
    inputs = iter(["1", "New Title", "New desc", "1", "Brand new content", "wiki,updated", "y"])

    with patch(INPUT_PATCH, side_effect=inputs):
        update_page(mock_manager)

    updated = mock_manager.update.call_args[0][0]
    assert updated.content == "Brand new content"
    assert updated.title == "New Title"
    assert updated.description == "New desc"
    assert updated.tags == ["wiki", "updated"]
    assert updated.isPublished is True
    output = capsys.readouterr().out
    assert "Updated page 1" in output
    print(f"\n  [CONTENT] Replaced: '{updated.content}'")


def test_append_content(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    mock_manager.update.return_value = PageResponse(
        succeeded=True, message="Page updated"
    )
    inputs = iter(["1", "", "", "2", "Appended text", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        update_page(mock_manager)

    updated = mock_manager.update.call_args[0][0]
    assert updated.content == "# Original contentAppended text"
    print(f"\n  [CONTENT] Appended: '{updated.content}'")


def test_keep_content_unchanged(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    mock_manager.update.return_value = PageResponse(
        succeeded=True, message="Page updated"
    )
    inputs = iter(["1", "", "", "3", "", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        update_page(mock_manager)

    updated = mock_manager.update.call_args[0][0]
    assert updated.content == "# Original content"
    print(f"\n  [CONTENT] Kept unchanged: '{updated.content}'")


def test_update_with_new_tags(mock_manager, capsys):
    mock_manager.get_by_id.return_value = _existing_page()
    mock_manager.update.return_value = PageResponse(
        succeeded=True, message="Page updated"
    )
    inputs = iter(["1", "", "", "3", "new1, new2, new3", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        update_page(mock_manager)

    updated = mock_manager.update.call_args[0][0]
    assert updated.tags == ["new1", "new2", "new3"]
    print(f"\n  [TAGS] Updated to: {updated.tags}")
