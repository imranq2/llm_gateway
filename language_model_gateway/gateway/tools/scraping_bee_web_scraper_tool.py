import asyncio
import logging
from typing import Optional

import httpx
from httpx._types import QueryParamTypes
from langchain_core.tools import BaseTool

from language_model_gateway.gateway.utilities.html_to_markdown_converter import (
    HtmlToMarkdownConverter,
)

logger = logging.getLogger(__name__)


class ScrapingBeeWebScraperTool(BaseTool):
    """Tool that scrapes websites using ScrapingBee API"""

    name: str = "scraping_bee_web_scraper"
    description: str = """
        Useful for scraping web pages and extracting their content.
        Input should be a URL.
        Returns the content of the webpage.
        Use this when you need to get content from a website.
        """

    api_key: str
    """API key for ScrapingBee"""

    base_url: str = "https://app.scrapingbee.com/api/v1/"
    """Base URL for ScrapingBee API"""

    render_js: bool = True
    """Whether to render JavaScript on the page"""

    premium_proxy: bool = False
    """ Whether to use a premium proxy. https://www.scrapingbee.com/documentation/#proxies """

    wait_browser: str = "networkidle0"
    """Wait until there are no more than 0 network connections for at least 500 ms."""

    return_markdown: bool = False
    """Whether to return the content as markdown or plain text (default)"""

    async def _async_scrape(self, url: str) -> Optional[str]:
        """Async method to scrape URL using ScrapingBee"""

        # https://www.scrapingbee.com/documentation/
        params: QueryParamTypes = {
            "api_key": self.api_key,
            "url": url,
            "render_js": self.render_js,
            "premium_proxy": self.premium_proxy,
            "wait_browser": self.wait_browser,
            # 'wait': 5000,  # wait in milliseconds (5 seconds) for the page to render
        }

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.base_url, params=params, timeout=30.0)

                if response.status_code == 200:
                    logger.info(
                        f"====== Scraped {url} ======\n{response.text}\n====== End of Scraped Content ======"
                    )
                    return response.text
                else:
                    logger.error(
                        f"ScrapingBee error: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error scraping {url}: {str(e)}")
            return None

    async def _extract_text_content_async(self, html_content: str) -> str:
        if self.return_markdown:
            return await HtmlToMarkdownConverter.get_markdown_from_html_async(
                html_content=html_content
            )
        else:
            return await HtmlToMarkdownConverter.get_plain_text_from_html_async(
                html_content=html_content
            )

    def _run(self, url: str) -> str:
        """Synchronous run method required by LangChain"""
        # Create event loop and run async method
        loop = asyncio.get_event_loop()
        content = loop.run_until_complete(self._async_scrape(url))

        if content:
            return loop.run_until_complete(self._extract_text_content_async(content))
        return "Error: Failed to scrape the webpage."

    async def _arun(self, url: str) -> str:
        """Async run method"""

        content: Optional[str] = await self._async_scrape(url)
        if content:
            return await self._extract_text_content_async(content)
        return "Error: Failed to scrape the webpage."
