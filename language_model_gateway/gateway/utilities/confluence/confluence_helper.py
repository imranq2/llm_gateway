import base64
import csv
import logging
from datetime import datetime
from typing import List, Optional
from urllib.parse import urlencode

from language_model_gateway.gateway.utilities.confluence.confluence_document import ConfluenceDocument
from language_model_gateway.gateway.utilities.confluence.confluence_search_result import ConfluenceSearchResult


class ConfluenceHelper:
    def __init__(self, *, http_client_factory, confluence_base_url: str, access_token: str, username: str):
        self.http_client_factory = http_client_factory
        self.logger = logging.getLogger(__name__)
        self.confluence_base_url = confluence_base_url.rstrip("/")
        self.confluence_access_token = access_token
        self.username = username

        credentials = base64.b64encode(f"{username}:{access_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AsyncConfluenceHelper",
        }

    async def search_content(self, search_string: str, limit: int = 10, space: Optional[str] = None) -> List[ConfluenceSearchResult]:
        async with self.http_client_factory.create_http_client(
            base_url=self.confluence_base_url, headers=self.headers, timeout=30.0
        ) as client:
            try:
                self.logger.info(f"Searching Confluence for: {search_string}")
                cql_query = f'text ~ "{search_string}"'
                if space:
                    cql_query += f' AND space="{space}"'

                base_url = f"{self.confluence_base_url}/wiki/rest/api/search"
                params = {"cql": cql_query, "limit": limit}

                # Combine them to create the full URL for logging
                full_url = f"{base_url}?{urlencode(params)}"
                self.logger.info(f"Making Confluence request to: {full_url}")

                # Make the actual request
                response = await client.get(base_url, params=params)

                response.raise_for_status()

                results = response.json().get("results", [])
                self.logger.info(f"Confluence raw response:\n{results}")
                search_results = []
                for result in results:
                    content = result.get('content', {})
                    search_results.append(ConfluenceSearchResult(
                        id=content.get('id'),
                        title=content.get('title'),
                        url=f"{self.confluence_base_url}/wiki/{content.get('_links', {}).get('webui')}",
                        updated_at=datetime.fromisoformat(result.get('lastModified').replace("Z", "+00:00")),
                        excerpt=result.get('excerpt'),
                    ))
                return search_results
            except Exception as e:
                self.logger.error(f"Error searching Confluence content: {str(e)}")
                return []

    def write_results_to_csv(self, search_results: List[ConfluenceSearchResult], output_file: str) -> None:
        """
        Export search results to a CSV file.

        Args:
            search_results (List[ConfluenceSearchResult]): List of search results
            output_file (str): Path to the output CSV file
        """
        assert output_file, "Output file path is required"
        assert search_results, "Search results are required"

        try:
            with open(output_file, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Id", "Title", "URL", "Updated", "Excerpt"])
                for result in search_results:
                    writer.writerow([
                        result.id,
                        result.title,
                        result.url,
                        result.updated_at.isoformat(),
                        result.excerpt
                    ])
            self.logger.info(f"Results exported to {output_file}")
        except IOError as e:
            self.logger.error(f"Failed to export results: {e}")

    def format_results_as_csv(self, search_results: List[ConfluenceSearchResult]) -> str:
        """
        Export search results to a CSV formatted string.

        Args:
            search_results (List[ConfluenceSearchResult]): List of search results

        Returns:
            str: CSV formatted string of search results
        """
        assert search_results, "Search results are required"

        output = "Id,Title,URL,Updated,Excerpt\n"
        for result in search_results:
            output += f'{result.id},"{result.title}",{result.url},{result.updated_at.isoformat()},"{result.excerpt}"\n'
        return output

    def format_results_as_csv_for_display(self, search_results: List[ConfluenceSearchResult]) -> str:
        """
        Export search results to a CSV formatted string.

        Args:
            search_results (List[ConfluenceSearchResult]): List of search results

        Returns:
            str: CSV formatted string of search results
        """
        assert search_results, "Search results are required"

        output = "Id,Title,URL,Updated\n"
        for result in search_results:
            output += f'{result.id},"{result.title}",{result.url},{result.updated_at.isoformat()}"\n'
        return output

    async def retrieve_page_by_id(self, page_id: str) -> Optional[ConfluenceDocument]:
        async with self.http_client_factory.create_http_client(
                base_url=self.confluence_base_url, headers=self.headers, timeout=30.0
        ) as client:
            try:
                url = f"{self.confluence_base_url}/wiki/rest/api/content/{page_id}?expand=body.storage,version.by"
                self.logger.info(f"Retrieving Confluence page with ID: {page_id}, full URL: {url}")

                response = await client.get(url)
                response.raise_for_status()

                result = response.json()
                content = result.get('body', {}).get('storage', {}).get('value', '')
                updated_at = datetime.fromisoformat(result.get('version', {}).get('when').replace("Z", "+00:00"))
                author_name = result.get('version', {}).get('by', {}).get('displayName', 'Unknown')

                page = ConfluenceDocument(
                    id=result.get('id'),
                    title=result.get('title'),
                    url=f"{self.confluence_base_url}/wiki/{result.get('_links', {}).get('webui')}",
                    updated_at=updated_at,
                    author_name=author_name,
                    content=content
                )
                return page
            except Exception as e:
                self.logger.error(f"Error retrieving Confluence page: {str(e)}")
                return None