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


class PageHistory(BaseModel):
    """Represents a single entry in a page's revision history."""

    versionId: int = 0
    versionDate: str = ""
    authorId: int = 0
    authorName: str = ""
    actionType: str = ""
    valueBefore: str | None = None
    valueAfter: str | None = None


class PageVersion(BaseModel):
    """Represents a specific version/snapshot of a page."""

    versionId: int = 0
    pageId: int = 0
    path: str = ""
    title: str = ""
    description: str = ""
    content: str = ""
    contentType: str = ""
    editor: str = ""
    locale: str = ""
    isPublished: bool = True
    isPrivate: bool = False
    tags: list[str] = []
    authorId: str = ""
    authorName: str = ""
    action: str = ""
    versionDate: str = ""
    createdAt: str = ""
    publishStartDate: str = ""
    publishEndDate: str = ""
