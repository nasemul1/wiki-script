"""GraphQL queries and mutations for page history and versioning."""

GET_PAGE_HISTORY = """
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

GET_PAGE_VERSION = """
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

RESTORE_PAGE_VERSION = """
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
