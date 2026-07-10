"""Custom exceptions for Wiki.js client operations."""


class WikiJSError(Exception):
    """Base exception for all Wiki.js API errors.

    Attributes:
        message: Human-readable error description.
        errors: List of GraphQL error objects returned by the API, if any.
    """

    def __init__(self, message: str, errors: list[dict] | None = None):
        self.message = message
        self.errors = errors or []
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.errors:
            details = "; ".join(
                err.get("message", "Unknown error") for err in self.errors
            )
            return f"{self.message}: {details}"
        return self.message
