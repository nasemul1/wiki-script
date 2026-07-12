"""GraphQL queries and mutations for page CRUD operations."""

CREATE_PAGE = """
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

UPDATE_PAGE = """
mutation UpdatePage(
  $id: Int!
  $content: String!
  $description: String!
  $editor: String!
  $isPrivate: Boolean!
  $isPublished: Boolean!
  $locale: String!
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
      locale: $locale
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

DELETE_PAGE = """
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

GET_PAGE_BY_ID = """
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

GET_PAGE_BY_PATH = """
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

LIST_PAGES = """
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

SEARCH_PAGES = """
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
