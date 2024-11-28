import logging
from os import environ
from typing import cast

from langchain_core.tools import BaseTool
from langchain_google_community import GoogleSearchAPIWrapper

logger = logging.getLogger(__file__)


class GoogleSearchTool(BaseTool):
    name: str = "google_search"
    description: str = "Search Google for recent results."

    def _run(self, query: str) -> str:
        """Returns the current time in Y-m-d H:M:S format with timezone."""
        try:
            search = GoogleSearchAPIWrapper()
            logger.info(f"Running Google search with query: {query}")
            google_api_key = environ["GOOGLE_API_KEY"]
            assert (
                google_api_key is not None
            ), "You need to specify a GOOGLE_API_KEY in docker.env to run the Google Search tool"
            google_cse_id = environ["GOOGLE_CSE_ID"]
            assert (
                google_cse_id is not None
            ), "You need to specify a GOOGLE_CSE_ID in docker.env to run the Google Search tool"
            result: str = cast(str, search.run(query=query))
            logger.info(f"Google search result: {result}")
            return result
        except Exception as e:
            logger.error(f"Error running Google search: {e}")
            return f"Error running Google search: {e}"

    async def _arun(self, query: str) -> str:
        """Async implementation of the tool (in this case, just calls _run)"""
        return self._run(query=query)
