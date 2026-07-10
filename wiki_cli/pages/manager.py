"""PagesManager — handles all page operations against the Wiki.js GraphQL API."""

from __future__ import annotations

from wiki_cli.client import WikiJSClient
from wiki_cli.exceptions import WikiJSError
from wiki_cli.models import Page, PageHistory, PageResponse, PageVersion
from wiki_cli.pages.history import (
    GET_PAGE_HISTORY,
    GET_PAGE_VERSION,
    RESTORE_PAGE_VERSION,
)
from wiki_cli.pages.queries import (
    CREATE_PAGE,
    DELETE_PAGE,
    GET_PAGE_BY_ID,
    GET_PAGE_BY_PATH,
    LIST_PAGES,
    SEARCH_PAGES,
    UPDATE_PAGE,
)


class PagesManager:
    """Handles page CRUD, search, and history operations against the Wiki.js GraphQL API.

    Attributes:
        client: An initialized WikiJSClient instance.
    """

    def __init__(self, client: WikiJSClient) -> None:
        self.client = client

    # ── CRUD ──────────────────────────────────────────────────────────

    def create(self, page: Page) -> PageResponse:
        variables = {
            "content": page.content,
            "description": page.description or "",
            "editor": page.editor,
            "isPrivate": page.isPrivate,
            "isPublished": page.isPublished,
            "locale": page.locale,
            "path": page.path,
            "tags": page.tags,
            "title": page.title,
        }
        result = self.client.execute(CREATE_PAGE, variable_values=variables)
        return self._parse_response(result, "create")

    def update(self, page: Page) -> PageResponse:
        if page.id is None:
            raise WikiJSError("Page id is required for update operations.")

        variables = {
            "id": page.id,
            "content": page.content,
            "description": page.description or "",
            "editor": page.editor,
            "isPrivate": page.isPrivate,
            "isPublished": page.isPublished,
            "tags": page.tags,
            "title": page.title,
            "path": page.path,
        }
        result = self.client.execute(UPDATE_PAGE, variable_values=variables)
        return self._parse_response(result, "update")

    def delete(self, page_id: int) -> bool:
        result = self.client.execute(DELETE_PAGE, variable_values={"id": page_id})
        response = result.get("pages", {}).get("delete", {}).get("responseResult", {})
        if not response.get("succeeded"):
            raise WikiJSError(
                f"Failed to delete page {page_id}: {response.get('message', 'Unknown error')}"
            )
        return True

    def get_by_id(self, page_id: int) -> Page:
        result = self.client.execute(GET_PAGE_BY_ID, variable_values={"id": page_id})
        return self._parse_single_page(result)

    def get_by_path(self, path: str, locale: str = "en") -> Page:
        result = self.client.execute(
            GET_PAGE_BY_PATH, variable_values={"path": path, "locale": locale}
        )
        return self._parse_single_page(result, key="singleByPath")

    def list_all(self, order_by: str = "TITLE") -> list[Page]:
        result = self.client.execute(LIST_PAGES, variable_values={"orderBy": order_by})
        raw_pages = result.get("pages", {}).get("list", [])
        return [
            Page(
                id=r.get("id"),
                path=r.get("path", ""),
                title=r.get("title", ""),
                description=r.get("description", ""),
                isPublished=r.get("isPublished", True),
                isPrivate=r.get("isPrivate", False),
                locale=r.get("locale", "en"),
                tags=r.get("tags", []),
            )
            for r in raw_pages
        ]

    def search(self, query: str, locale: str = "en") -> list[Page]:
        result = self.client.execute(
            SEARCH_PAGES, variable_values={"query": query, "locale": locale}
        )
        search_data = result.get("pages", {}).get("search", {})
        return [
            Page(
                id=r.get("id"),
                path=r.get("path", ""),
                title=r.get("title", ""),
                description=r.get("description", ""),
                locale=r.get("locale", "en"),
            )
            for r in search_data.get("results", [])
        ]

    def move_or_rename(self, page_id: int, new_path: str) -> PageResponse:
        page = self.get_by_id(page_id)
        page.path = new_path
        return self.update(page)

    def clone_page(self, source_id: int, new_path: str, new_title: str) -> PageResponse:
        source = self.get_by_id(source_id)
        new_page = Page(
            path=new_path,
            title=new_title,
            content=source.content,
            description=source.description,
            editor=source.editor,
            isPublished=source.isPublished,
            isPrivate=source.isPrivate,
            locale=source.locale,
            tags=source.tags,
        )
        return self.create(new_page)

    # ── History ───────────────────────────────────────────────────────

    def get_history(
        self, page_id: int, offset_page: int = 0, offset_size: int = 100
    ) -> tuple[list[PageHistory], int]:
        result = self.client.execute(
            GET_PAGE_HISTORY,
            variable_values={
                "id": page_id,
                "offsetPage": offset_page,
                "offsetSize": offset_size,
            },
        )
        history_data = result.get("pages", {}).get("history", {})
        trail = history_data.get("trail", [])
        total = history_data.get("total", 0)
        entries = [
            PageHistory(
                versionId=h["versionId"],
                versionDate=h.get("versionDate", ""),
                authorId=h.get("authorId", 0),
                authorName=h.get("authorName", ""),
                actionType=h.get("actionType", ""),
                valueBefore=h.get("valueBefore"),
                valueAfter=h.get("valueAfter"),
            )
            for h in trail
        ]
        return entries, total

    def get_version(self, page_id: int, version_id: int) -> PageVersion:
        result = self.client.execute(
            GET_PAGE_VERSION,
            variable_values={"pageId": page_id, "versionId": version_id},
        )
        raw = result.get("pages", {}).get("version")
        if not raw:
            raise WikiJSError(f"Version {version_id} not found for page {page_id}.")
        return PageVersion(
            versionId=raw.get("versionId", 0),
            pageId=raw.get("pageId", 0),
            path=raw.get("path", ""),
            title=raw.get("title", ""),
            description=raw.get("description", ""),
            content=raw.get("content", ""),
            contentType=raw.get("contentType", ""),
            editor=raw.get("editor", ""),
            locale=raw.get("locale", ""),
            isPublished=raw.get("isPublished", True),
            isPrivate=raw.get("isPrivate", False),
            tags=raw.get("tags", []),
            authorId=raw.get("authorId", ""),
            authorName=raw.get("authorName", ""),
            action=raw.get("action", ""),
            versionDate=raw.get("versionDate", ""),
            createdAt=raw.get("createdAt", ""),
        )

    def restore_version(self, page_id: int, version_id: int) -> bool:
        result = self.client.execute(
            RESTORE_PAGE_VERSION,
            variable_values={"pageId": page_id, "versionId": version_id},
        )
        response = (
            result.get("pages", {}).get("restore", {}).get("responseResult", {})
        )
        if not response.get("succeeded"):
            raise WikiJSError(
                f"Failed to restore version: {response.get('message', 'Unknown error')}"
            )
        return True

    # ── Internal helpers ──────────────────────────────────────────────

    def _parse_response(self, result: dict, operation: str) -> PageResponse:
        page_data = result.get("pages", {}).get(operation, {})
        response_result = page_data.get("responseResult", {})

        if not response_result.get("succeeded"):
            raise WikiJSError(
                f"Page {operation} failed: {response_result.get('message', 'Unknown error')}"
            )

        raw_page = page_data.get("page")
        page = None
        if raw_page:
            page = Page(
                id=raw_page.get("id"),
                path=raw_page.get("path", ""),
                title=raw_page.get("title", ""),
            )

        return PageResponse(
            succeeded=True,
            message=response_result.get("message", ""),
            page=page,
        )

    def _parse_single_page(self, result: dict, key: str = "single") -> Page:
        raw_page = result.get("pages", {}).get(key)
        if not raw_page:
            raise WikiJSError("Page not found.")

        raw_tags = raw_page.get("tags", [])
        if raw_tags and isinstance(raw_tags[0], dict):
            tags = [t["tag"] for t in raw_tags if "tag" in t]
        else:
            tags = raw_tags

        return Page(
            id=raw_page.get("id"),
            path=raw_page.get("path", ""),
            title=raw_page.get("title", ""),
            content=raw_page.get("content", ""),
            description=raw_page.get("description", ""),
            editor=raw_page.get("editor", "markdown"),
            isPublished=raw_page.get("isPublished", True),
            isPrivate=raw_page.get("isPrivate", False),
            locale=raw_page.get("locale", "en"),
            tags=tags,
        )
