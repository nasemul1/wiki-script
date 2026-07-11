from unittest.mock import MagicMock

import pytest

from wiki_cli.models import Page, PageResponse
from wiki_cli.pages import PagesManager

INPUT_PATCH = "builtins.input"


@pytest.fixture
def mock_manager():
    return MagicMock(spec=PagesManager)


@pytest.fixture
def sample_page():
    return Page(
        id=1,
        path="docs/intro",
        title="Introduction",
        content="# Welcome\nThis is the intro page.",
        description="A brief introduction",
        locale="en",
        isPublished=True,
        isPrivate=False,
        tags=["wiki", "docs"],
    )


@pytest.fixture
def sample_page_response(sample_page):
    return PageResponse(
        succeeded=True,
        message="Page created successfully",
        page=sample_page,
    )
