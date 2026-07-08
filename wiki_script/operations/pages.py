"""Page operations for Wiki.js (create, update, delete, fetch)."""

from __future__ import annotations

from wiki_script.exceptions import WikiJSError
from wiki_script.models import Page, PageResponse
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
      tags
    }
  }
}
"""

_GET_PAGE_BY_PATH = """
query GetPageByPath($path: String, $locale: String) {
  pages {
    single(path: $path, locale: $locale) {
      id
      path
      title
      description
      content
      editor
      isPublished
      isPrivate
      locale
      tags
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
        return self._parse_single_page(result)

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

    def _parse_single_page(self, result: dict) -> Page:
        """Parse the response from a single page query.

        Args:
            result: Raw GraphQL response data.

        Returns:
            Page object populated with data.

        Raises:
            WikiJSError: If no page data is found.
        """
        raw_page = result.get("pages", {}).get("single")

        if not raw_page:
            raise WikiJSError("Page not found.")

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
            tags=raw_page.get("tags", []),
        )
