"""Data models for Wiki.js resources."""

from pydantic import BaseModel


class Page(BaseModel):
    """Represents a Wiki.js page.

    Attributes:
        id: Unique page identifier.
        path: URL path of the page (e.g. 'projects/alpha/overview').
        title: Page title.
        content: Page content in the editor's format.
        description: Optional page description.
        editor: Editor used (e.g. 'markdown').
        isPublished: Whether the page is published.
        isPrivate: Whether the page is private.
        locale: Language locale (e.g. 'en').
        tags: List of tags associated with the page.
    """

    id: int | None = None
    path: str
    title: str
    content: str = ""
    description: str = ""
    editor: str = "markdown"
    isPublished: bool = True
    isPrivate: bool = False
    locale: str = "en"
    tags: list[str] = []


class PageResponse(BaseModel):
    """Response wrapper from page mutations.

    Attributes:
        succeeded: Whether the operation succeeded.
        errorCode: Error code if the operation failed.
        message: Human-readable message from the API.
        page: The created/updated page, if returned.
    """

    succeeded: bool
    errorCode: int | None = None
    message: str = ""
    page: Page | None = None


class Asset(BaseModel):
    """Represents a Wiki.js asset (uploaded file).

    Attributes:
        id: Unique asset identifier.
        filename: Original filename.
        folder: Folder path where the asset is stored.
        mime: MIME type of the file.
        fileSize: Size of the file in bytes.
    """

    id: int | None = None
    filename: str = ""
    folder: str = "/"
    mime: str = ""
    fileSize: int = 0
