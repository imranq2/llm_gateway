from typing import Any, cast

from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import BaseTool


class GoogleSearchTool(BaseTool):
    name: str = "google_search"
    description: str = "Search Google for recent results."

    def _run(self, *args: Any, **kwargs: Any) -> str:
        """Returns the current time in Y-m-d H:M:S format with timezone."""
        search = GoogleSearchAPIWrapper()
        return cast(str, search.run(*args, **kwargs))

    async def _arun(self, *args: Any, **kwargs: Any) -> str:
        """Async implementation of the tool (in this case, just calls _run)"""
        return self._run(*args, **kwargs)
