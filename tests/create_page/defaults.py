from unittest.mock import patch

from wiki_cli.cli_pages import create_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def test_uses_default_values_when_blanks(mock_manager, capsys):
    response = PageResponse(
        succeeded=True,
        message="OK",
        page=Page(id=30, path="x", title="X"),
    )
    mock_manager.create.return_value = response
    inputs = iter(["x", "X", "content", "", "", "", "", ""])

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    created = mock_manager.create.call_args[0][0]
    assert created.description == ""
    assert created.tags == []
    assert created.locale == "en"
    assert created.isPrivate is False
    assert created.isPublished is True

    assert response.succeeded is True
    assert response.page.id == 30
    output = capsys.readouterr().out
    assert "Created page (id=30)" in output


def test_empty_tag_string_becomes_empty_list(mock_manager):
    response = PageResponse(
        succeeded=True,
        message="OK",
        page=Page(id=1, path="p", title="T"),
    )
    mock_manager.create.return_value = response
    inputs = iter(["p", "T", "c", "", "  ,  ,  ", "en", "n", "y"])

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    created = mock_manager.create.call_args[0][0]
    assert created.tags == []
    assert response.succeeded is True
