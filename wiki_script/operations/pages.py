"""Page operations for Wiki.js (create, update, delete, fetch)."""

from __future__ import annotations

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page, PageHistory, PageResponse, PageVersion
from wiki_script.wiki_client import WikiJSClient

_CREATE_PAGE = """
mutation CreatePage(
  $content: String!
  $description: String!
  $editor: String!
  $isPrivate: Boolean!
  $isPublished: Boolean!
  $locale: String!
  $path: String!
  $tags: [String!]!
  $title: String!
) {
  pages {
    create(
      content: $content
      description: $description
      editor: $editor
      isPrivate: $isPrivate
      isPublished: $isPublished
      locale: $locale
      path: $path
      tags: $tags
      title: $title
    ) {
      responseResult {
        succeeded
        errorCode
        message
      }
      page {
        id
        path
        title
      }
    }
  }
}
"""

_UPDATE_PAGE = """
mutation UpdatePage(
  $id: Int!
  $content: String!
  $description: String!
  $editor: String!
  $isPrivate: Boolean!
  $isPublished: Boolean!
  $tags: [String!]!
  $title: String!
  $path: String!
) {
  pages {
    update(
      id: $id
      content: $content
      description: $description
      editor: $editor
      isPrivate: $isPrivate
      isPublished: $isPublished
      tags: $tags
      title: $title
      path: $path
    ) {
      responseResult {
        succeeded
        errorCode
        message
      }
      page {
        id
        path
        title
      }
    }
  }
}
"""

_DELETE_PAGE = """
mutation DeletePage($id: Int!) {
  pages {
    delete(id: $id) {
      responseResult {
        succeeded
        errorCode
        message
      }
    }
  }
}
"""

_GET_PAGE_BY_ID = """
query GetPageById($id: Int!) {
  pages {
    single(id: $id) {
      id
      path
      title
      description
      content
      editor
      isPublished
      isPrivate
      locale
      tags {
        tag
      }
    }
  }
}
"""

_GET_PAGE_BY_PATH = """
query GetPageByPath($path: String!, $locale: String!) {
  pages {
    singleByPath(path: $path, locale: $locale) {
      id
      path
      title
      description
      content
      editor
      isPublished
      isPrivate
      locale
      tags {
        tag
      }
    }
  }
}
"""

_LIST_PAGES = """
query ListPages($orderBy: PageOrderBy) {
  pages {
    list(orderBy: $orderBy) {
      id
      path
      title
      description
      isPublished
      isPrivate
      locale
      tags
    }
  }
}
"""

_SEARCH_PAGES = """
query SearchPages($query: String!, $locale: String) {
  pages {
    search(query: $query, locale: $locale) {
      results {
        id
        path
        title
        description
        locale
      }
      suggestions
      totalHits
    }
  }
}
"""

_GET_PAGE_HISTORY = """
query GetPageHistory($id: Int!, $offsetPage: Int, $offsetSize: Int) {
  pages {
    history(id: $id, offsetPage: $offsetPage, offsetSize: $offsetSize) {
      trail {
        versionId
        versionDate
        authorId
        authorName
        actionType
        valueBefore
        valueAfter
      }
      total
    }
  }
}
"""

_GET_PAGE_VERSION = """
query GetPageVersion($pageId: Int!, $versionId: Int!) {
  pages {
    version(pageId: $pageId, versionId: $versionId) {
      versionId
      pageId
      path
      title
      description
      content
      contentType
      editor
      locale
      isPublished
      isPrivate
      tags
      authorId
      authorName
      action
      versionDate
      createdAt
    }
  }
}
"""

_RESTORE_PAGE_VERSION = """
mutation RestorePageVersion($pageId: Int!, $versionId: Int!) {
  pages {
    restore(pageId: $pageId, versionId: $versionId) {
      responseResult {
        succeeded
        message
      }
    }
  }
}
"""


class PagesManager:
    """Handles page CRUD operations against the Wiki.js GraphQL API.

    Attributes:
        client: An initialized WikiJSClient instance.
    """

    def __init__(self, client: WikiJSClient) -> None:
        """Initialize the PagesManager.

        Args:
            client: A WikiJSClient configured with valid credentials.
        """
        self.client = client

    def create(self, page: Page) -> PageResponse:
        """Create a new page via the pages.create mutation.

        Folders are created implicitly by using slashes in the path
        (e.g. 'projects/alpha/overview' creates the 'projects/alpha' folder).

        Args:
            page: Page object with at least path, title, and content set.

        Returns:
            PageResponse containing success status and the created page.

        Raises:
            WikiJSError: If the mutation fails or returns an error.
        """
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

        result = self.client.execute(_CREATE_PAGE, variable_values=variables)
        return self._parse_response(result, "create")

    def update(self, page: Page) -> PageResponse:
        """Update an existing page via the pages.update mutation.

        The page must have a valid id set. Fields not provided will retain
        their existing values on the server.

        Args:
            page: Page object with id set and fields to update.

        Returns:
            PageResponse containing success status and the updated page.

        Raises:
            WikiJSError: If the page id is missing, the mutation fails, or
                returns an error.
        """
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

        result = self.client.execute(_UPDATE_PAGE, variable_values=variables)
        return self._parse_response(result, "update")

    def delete(self, page_id: int) -> bool:
        """Delete a page via the pages.delete mutation.

        Args:
            page_id: The numeric ID of the page to delete.

        Returns:
            True if the deletion succeeded.

        Raises:
            WikiJSError: If the mutation fails or returns an error.
        """
        result = self.client.execute(_DELETE_PAGE, variable_values={"id": page_id})
        response = result.get("pages", {}).get("delete", {}).get("responseResult", {})

        if not response.get("succeeded"):
            error_msg = response.get("message", "Unknown error")
            raise WikiJSError(f"Failed to delete page {page_id}: {error_msg}")

        return True

    def get_by_id(self, page_id: int) -> Page:
        """Fetch a single page by its numeric ID.

        Args:
            page_id: The numeric ID of the page.

        Returns:
            Page object populated with data from the API.

        Raises:
            WikiJSError: If the query fails or the page is not found.
        """
        result = self.client.execute(
            _GET_PAGE_BY_ID, variable_values={"id": page_id}
        )
        return self._parse_single_page(result)

    def get_by_path(self, path: str, locale: str = "en") -> Page:
        """Fetch a single page by its URL path and locale.

        Args:
            path: The page path (e.g. 'projects/alpha/overview').
            locale: The language locale (default: 'en').

        Returns:
            Page object populated with data from the API.

        Raises:
            WikiJSError: If the query fails or the page is not found.
        """
        result = self.client.execute(
            _GET_PAGE_BY_PATH, variable_values={"path": path, "locale": locale}
        )
        return self._parse_single_page(result, key="singleByPath")

    def list_all(self, order_by: str = "TITLE") -> list[Page]:
        """Fetch a list of all pages.

        Args:
            order_by: Sort order - TITLE, PATH, CREATED, UPDATED (default: TITLE).

        Returns:
            List of Page objects.

        Raises:
            WikiJSError: If the query fails.
        """
        result = self.client.execute(
            _LIST_PAGES, variable_values={"orderBy": order_by}
        )
        raw_pages = result.get("pages", {}).get("list", [])
        pages = []
        for raw in raw_pages:
            pages.append(Page(
                id=raw.get("id"),
                path=raw.get("path", ""),
                title=raw.get("title", ""),
                description=raw.get("description", ""),
                isPublished=raw.get("isPublished", True),
                isPrivate=raw.get("isPrivate", False),
                locale=raw.get("locale", "en"),
                tags=raw.get("tags", []),
            ))
        return pages

    def search(self, query: str, locale: str = "en") -> list[Page]:
        """Search pages by keyword.

        Args:
            query: Search query string.
            locale: Locale to search in (default: 'en').

        Returns:
            List of matching Page objects.

        Raises:
            WikiJSError: If the query fails.
        """
        result = self.client.execute(
            _SEARCH_PAGES, variable_values={"query": query, "locale": locale}
        )
        search_data = result.get("pages", {}).get("search", {})
        raw_results = search_data.get("results", [])
        return [
            Page(
                id=r.get("id"),
                path=r.get("path", ""),
                title=r.get("title", ""),
                description=r.get("description", ""),
                locale=r.get("locale", "en"),
            )
            for r in raw_results
        ]

    def get_history(self, page_id: int, offset_page: int = 0, offset_size: int = 100) -> tuple[list[PageHistory], int]:
        """Fetch the revision history of a page.

        Args:
            page_id: The numeric ID of the page.
            offset_page: Page number for pagination (0-based).
            offset_size: Number of entries per page.

        Returns:
            Tuple of (list of PageHistory entries, total count).

        Raises:
            WikiJSError: If the query fails.
        """
        result = self.client.execute(
            _GET_PAGE_HISTORY,
            variable_values={"id": page_id, "offsetPage": offset_page, "offsetSize": offset_size},
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
        """Fetch a specific version/snapshot of a page.

        Args:
            page_id: The numeric ID of the page.
            version_id: The version ID to fetch.

        Returns:
            PageVersion object with full content.

        Raises:
            WikiJSError: If the query fails or version not found.
        """
        result = self.client.execute(
            _GET_PAGE_VERSION,
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
        """Restore a page to a specific version.

        Args:
            page_id: The numeric ID of the page.
            version_id: The version ID to restore.

        Returns:
            True on success.

        Raises:
            WikiJSError: If the restore fails.
        """
        result = self.client.execute(
            _RESTORE_PAGE_VERSION,
            variable_values={"pageId": page_id, "versionId": version_id},
        )
        response = result.get("pages", {}).get("restore", {}).get("responseResult", {})
        if not response.get("succeeded"):
            raise WikiJSError(f"Failed to restore version: {response.get('message', 'Unknown error')}")
        return True

    def move_or_rename(self, page_id: int, new_path: str) -> PageResponse:
        """Move or rename a page by updating its path.

        Fetches the page first, then updates with the new path.

        Args:
            page_id: The numeric ID of the page.
            new_path: The new path for the page.

        Returns:
            PageResponse with the updated page.

        Raises:
            WikiJSError: If the fetch or update fails.
        """
        page = self.get_by_id(page_id)
        page.path = new_path
        return self.update(page)

    def clone_page(self, source_id: int, new_path: str, new_title: str) -> PageResponse:
        """Clone a page to a new path with a new title.

        Fetches the source page and creates a copy at the new path.

        Args:
            source_id: The numeric ID of the source page.
            new_path: The path for the new cloned page.
            new_title: The title for the new cloned page.

        Returns:
            PageResponse with the created clone.

        Raises:
            WikiJSError: If the fetch or create fails.
        """
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

    def _parse_response(self, result: dict, operation: str) -> PageResponse:
        """Parse the response from a page create/update mutation.

        Args:
            result: Raw GraphQL response data.
            operation: Name of the operation for error messages.

        Returns:
            PageResponse with parsed data.

        Raises:
            WikiJSError: If the mutation did not succeed.
        """
        page_data = result.get("pages", {}).get(operation, {})
        response_result = page_data.get("responseResult", {})

        if not response_result.get("succeeded"):
            error_msg = response_result.get("message", "Unknown error")
            raise WikiJSError(f"Page {operation} failed: {error_msg}")

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
        """Parse the response from a single page query.

        Args:
            result: Raw GraphQL response data.
            key: The response key to look up ('single' or 'singleByPath').

        Returns:
            Page object populated with data.

        Raises:
            WikiJSError: If no page data is found.
        """
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
