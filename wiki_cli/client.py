"""Core Wiki.js GraphQL client using the gql library."""

from __future__ import annotations

from typing import Any

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from wiki_cli.exceptions import WikiJSError


class WikiJSClient:
    """Manages the gql client, authentication, and query execution for Wiki.js.

    Attributes:
        url: The GraphQL endpoint URL.
        api_key: The API key used for Bearer auth.
        client: The underlying gql Client instance.
    """

    def __init__(self, url: str, api_key: str) -> None:
        if not url or not url.strip():
            raise WikiJSError("url is required")
        if not (url.startswith("http://") or url.startswith("https://")):
            raise WikiJSError("url must start with http:// or https://")
        if not api_key or not api_key.strip():
            raise WikiJSError("api_key is required")

        self.url = url
        self.api_key = api_key

        transport = RequestsHTTPTransport(
            url=self.url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            verify=True,
            retries=3,
        )

        self.client = Client(transport=transport, fetch_schema_from_transport=False)

    def execute(
        self,
        query: str,
        variable_values: dict[str, Any] | None = None,
        operation_name: str | None = None,
        upload_files: bool = False,
    ) -> dict[str, Any]:
        """Execute a GraphQL operation against the Wiki.js API."""
        document = gql(query)

        if variable_values:
            document.variable_values = variable_values

        try:
            result = self.client.execute(
                document,
                operation_name=operation_name,
                upload_files=upload_files,
            )
        except Exception as exc:
            raise WikiJSError(f"GraphQL request failed: {exc}") from exc

        if isinstance(result, dict) and "errors" in result:
            raise WikiJSError(
                "GraphQL returned errors",
                errors=result["errors"],
            )

        return result
