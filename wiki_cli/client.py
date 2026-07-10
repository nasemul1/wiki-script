"""Core Wiki.js GraphQL client using the gql library."""

from __future__ import annotations

import os
from typing import Any

from dotenv import load_dotenv
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

from wiki_cli.exceptions import WikiJSError

load_dotenv()


class WikiJSClient:
    """Manages the gql client, authentication, and query execution for Wiki.js.

    Attributes:
        url: The GraphQL endpoint URL.
        client: The underlying gql Client instance.
    """

    def __init__(self, url: str | None = None, api_key: str | None = None) -> None:
        self.url = url or os.getenv("WIKIJS_URL")
        self.api_key = api_key or os.getenv("WIKIJS_API_KEY")

        if not self.url:
            raise WikiJSError(
                "WIKIJS_URL is not set. Provide it as an argument or in the environment."
            )
        if not self.api_key:
            raise WikiJSError(
                "WIKIJS_API_KEY is not set. Provide it as an argument or in the environment."
            )

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
        """Execute a GraphQL operation against the Wiki.js API.

        Returns:
            The 'data' dict from the GraphQL response.

        Raises:
            WikiJSError: If the transport fails or the response contains errors.
        """
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
