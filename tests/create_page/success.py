from unittest.mock import patch

from wiki_cli.cli_pages import create_page
from wiki_cli.models import Page, PageResponse

INPUT_PATCH = "builtins.input"


def test_valid_inputs(mock_manager, capsys):
    response = PageResponse(
        succeeded=True,
        message="Page created successfully",
        page=Page(id=10, path="test/path", title="Test Page"),
    )
    mock_manager.create.return_value = response
    inputs = iter(["test/path", "Test Page", "Hello world", "", "", "en", "n", "y"])

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    mock_manager.create.assert_called_once()

    created = mock_manager.create.call_args[0][0]
    assert created.path == "test/path"
    assert created.title == "Test Page"
    assert created.content == "Hello world"
    print(f"\n  [CREATE] Page sent: path={created.path}, title={created.title}, content={created.content}")

    assert response.succeeded is True
    assert response.page is not None
    assert response.page.id == 10
    assert response.page.path == "test/path"
    assert response.page.title == "Test Page"
    assert response.message == "Page created successfully"
    print(f"  [RESPONSE] succeeded={response.succeeded}, page_id={response.page.id}, message={response.message}")

    output = capsys.readouterr().out
    assert "Created page (id=10)" in output
    print(f"  [OUTPUT] {output.strip()}")


def test_all_fields_set_correctly(mock_manager):
    response = PageResponse(
        succeeded=True,
        message="OK",
        page=Page(id=20, path="proj/alpha", title="Alpha"),
    )
    mock_manager.create.return_value = response
    inputs = iter(
        ["proj/alpha", "Alpha", "Some content", "A description", "tag1, tag2", "bn", "y", "y"]
    )

    with patch(INPUT_PATCH, side_effect=inputs):
        create_page(mock_manager)

    created = mock_manager.create.call_args[0][0]
    assert created.path == "proj/alpha"
    assert created.title == "Alpha"
    assert created.content == "Some content"
    assert created.description == "A description"
    assert created.tags == ["tag1", "tag2"]
    assert created.locale == "bn"
    assert created.isPrivate is True
    assert created.isPublished is True

    assert response.succeeded is True
    assert response.page.id == 20
    assert response.page.path == "proj/alpha"
