"""Data models for Wiki.js resources."""

from pydantic import BaseModel


class Page(BaseModel):
    """Represents a Wiki.js page."""

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
    """Response wrapper from page mutations."""

    succeeded: bool
    errorCode: int | None = None
    message: str = ""
    page: Page | None = None


class Asset(BaseModel):
    """Represents a Wiki.js asset (uploaded file)."""

    id: int | None = None
    filename: str = ""
    ext: str = ""
    kind: str = ""
    mime: str = ""
    fileSize: int = 0
    folderId: int | None = None
    folderSlug: str = ""
    createdAt: str = ""
    updatedAt: str = ""


class AssetFolder(BaseModel):
    """Represents a Wiki.js asset folder."""

    id: int | None = None
    slug: str = ""
    name: str = ""
