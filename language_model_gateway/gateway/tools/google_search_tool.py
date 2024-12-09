import logging
from os import environ
from typing import Optional, Dict, Any, List, cast, Type

import httpx
from langchain_core.tools import BaseTool
from pydantic import PrivateAttr, Field, BaseModel

logger = logging.getLogger(__file__)


class GoogleSearchToolInput(BaseModel):
    query: str = Field(description="The search query to send to Google Search")


class GoogleSearchTool(BaseTool):
    """
    2. Enable the Custom Search API
    - Navigate to the APIs & Services→Dashboard panel in Cloud Console.
    - Click Enable APIs and Services.
    - Search for Custom Search API and click on it.
    - Click Enable.
    URL for it: https://console.cloud.google.com/apis/library/customsearch.googleapis
    .com

    3. To create an API key:
    - Navigate to the APIs & Services → Credentials panel in Cloud Console.
    - Select Create credentials, then select API key from the drop-down menu.
    - The API key created dialog box displays your newly created key.
    - You now have an API_KEY

    Alternatively, you can just generate an API key here:
    https://developers.google.com/custom-search/docs/paid_element#api_key

    4. Setup Custom Search Engine so you can search the entire web
    - Create a custom search engine here: https://programmablesearchengine.google.com/.
    - In `What to search` to search, pick the `Search the entire Web` option.
    After search engine is created, you can click on it and find `Search engine ID`
      on the Overview page.

    """

    name: str = "google_search"
    description: str = "Search Google for recent results."

    args_schema: Type[BaseModel] = GoogleSearchToolInput

    # Private attributes
    _client: httpx.AsyncClient = PrivateAttr()
    _api_key: str = PrivateAttr()
    _cse_id: str = PrivateAttr()

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._client = httpx.AsyncClient()
        api_key: Optional[str] = environ.get("GOOGLE_API_KEY")
        assert api_key, "GOOGLE_API_KEY environment variable is required"
        cse_id: Optional[str] = environ.get("GOOGLE_CSE_ID")
        assert cse_id, "GOOGLE_CSE_ID environment variable is required"
        self._api_key = api_key
        self._cse_id = cse_id

    async def aclose(self) -> None:
        """Close the HTTP client."""
        await self._client.aclose()

    def _run(self, query: str) -> str:
        """Use async version of this tool."""
        raise NotImplementedError("Use async version of this tool")

    async def _arun(self, query: str) -> str:
        """Async implementation of the Google search tool."""
        snippets: List[str] = []
        try:
            # Result follows https://developers.google.com/custom-search/v1/reference/rest/v1/Search
            results: List[Dict[str, Any]] = await self._search_async(q=query)
            if len(results) == 0:
                return "No good Google Search Result was found"

            for result in results:
                if "snippet" in result:
                    snippets.append(f"- {result['snippet']} ({result.get('link')})")

            response: str = "\n".join(snippets)
            logger.info(f"Google Search results: {response}")
            return response
        except Exception as e:
            logger.exception(e, stack_info=True)
            return "Ran into an error while running Google Search"

    # noinspection PyPep8Naming,PyShadowingBuiltins
    async def _search_async(
        self,
        q: str,
        c2coff: Optional[str] = None,
        cr: Optional[str] = None,
        dateRestrict: Optional[str] = None,
        exactTerms: Optional[str] = None,
        excludeTerms: Optional[str] = None,
        fileType: Optional[str] = None,
        filter: Optional[str] = None,
        gl: Optional[str] = None,
        googleHost: Optional[str] = None,
        highRange: Optional[str] = None,
        hl: Optional[str] = None,
        hq: Optional[str] = None,
        imgColorType: Optional[str] = None,
        imgDominantColor: Optional[str] = None,
        imgSize: Optional[str] = None,
        imgType: Optional[str] = None,
        linkSite: Optional[str] = None,
        lowRange: Optional[str] = None,
        lr: Optional[str] = None,
        num: Optional[int] = None,
        orTerms: Optional[str] = None,
        rights: Optional[str] = None,
        safe: Optional[str] = None,
        searchType: Optional[str] = None,
        siteSearch: Optional[str] = None,
        siteSearchFilter: Optional[str] = None,
        sort: Optional[str] = None,
        start: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Execute the Google search query."""
        logger.info(f"Running Google search with query: {q}")

        params = {"key": self._api_key, "cx": self._cse_id, "q": q}

        # Add optional parameters if they are provided
        optional_params = locals()
        for param, value in optional_params.items():
            if param not in ["self", "q"] and value is not None:
                params[param] = value

        url: str = "https://customsearch.googleapis.com/customsearch/v1"
        # parameters follow https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
        response = await self._client.get(url, params=params)
        response.raise_for_status()
        # Result follows https://developers.google.com/custom-search/v1/reference/rest/v1/Search
        result = response.json()
        return cast(List[Dict[str, Any]], result.get("items", []))
