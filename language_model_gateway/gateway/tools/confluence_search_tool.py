import logging
from typing import Type, Literal, Optional, Tuple
from pydantic import BaseModel, Field

from language_model_gateway.gateway.tools.resilient_base_tool import ResilientBaseTool
from language_model_gateway.gateway.utilities.confluence.confluence_helper import ConfluenceHelper
from language_model_gateway.gateway.utilities.csv_to_markdown_converter import CsvToMarkdownConverter

logger = logging.getLogger(__name__)


class ConfluenceSearchToolInput(BaseModel):
    """
    Input model for configuring Confluence search and analysis.

    IMPORTANT LLM PARSING GUIDANCE:
    - When a query mentions a specific space, extract the space name exactly as written
    - If there are no search results returned when 'space' is used, try the same query without the 'space'
    - Examples of parsing:
      * "what is PSS in ATC space"
        -> space = "atc"
      * "how are vitals processed in athd space"
        -> space = "athd"

    Attributes:
        space (Optional[str]):
            Specific Confluence space where the search must be constrained in.
            PARSING HINT: Directly use the repository name mentioned in the query.
            Can include organization prefix (e.g., "org/repo").
            Example: "atc", "athd"

        # ... (rest of the attributes remain the same)
    """
    search_string: str = Field(..., description="The search string to use for querying Confluence content.")
    space: Optional[str] = Field(..., description="The Confluence space where the user is asking to search in.")
    limit: Optional[int] = Field(default=10, description="Maximum number of search results to retrieve.")


class ConfluenceSearchTool(ResilientBaseTool):
    name: str = "confluence_search_tool"
    description: str = (
        "Tool for searching content in Confluence. "
        "USAGE TIPS: "
        "- Provide a search string to search content in Confluence."
        "- Indicate the Confluence space to limit the search results."
    )

    args_schema: Type[BaseModel] = ConfluenceSearchToolInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    confluence_helper: ConfluenceHelper

    async def _arun(self, search_string: str, space: Optional[str] = None, limit: Optional[int] = 10) -> Tuple[str, str]:
        try:
            search_results = await self.confluence_helper.search_content(search_string, limit, space)

            logger.info(f"CONFLUENCE SEARCH TOOL, RESULTS:\n{search_results}")

            if not search_results:
                return "No results found.", "No results found."

            csv_results = self.confluence_helper.format_results_as_csv(search_results)
            csv_results_display = self.confluence_helper.format_results_as_csv_for_display(search_results)
            markdown_results = CsvToMarkdownConverter.csv_to_markdown_table(csv_results_display)

            artifact = f"Search results for query: {search_string}\n\nResults:\n{markdown_results}"
            return csv_results, artifact
        except Exception as e:
            error_msg = f"Error searching Confluence content: {str(e)}"
            return error_msg, error_msg

    def _run(self, search_string: str, limit: Optional[int] = 10) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).

        Raises:
            NotImplementedError: Always raises to enforce async usage
        """
        raise NotImplementedError("Use async version of this tool")