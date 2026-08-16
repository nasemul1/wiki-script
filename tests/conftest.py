from unittest.mock import MagicMock

import pytest

from wiki_cli import ai, wikis
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


@pytest.fixture
def tmp_wiki_config(tmp_path, monkeypatch):
    f1 = tmp_path / "wikis.json"
    f2 = tmp_path / "active_wiki.txt"
    monkeypatch.setattr(wikis, "WIKIS_FILE", f1)
    monkeypatch.setattr(wikis, "ACTIVE_FILE", f2)
    return f1, f2


@pytest.fixture
def tmp_sessions_dir(tmp_path, monkeypatch):
    sessions_dir = tmp_path / "sessions"
    sessions_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(ai.sessions, "SESSIONS_DIR", sessions_dir)
    return sessions_dir
