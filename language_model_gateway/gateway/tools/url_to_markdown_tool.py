import aiohttp
from bs4 import BeautifulSoup
from langchain.tools import BaseTool


class URLToMarkdownTool(BaseTool):
    """
    LangChain-compatible tool for downloading the content of a URL and converting it to Markdown.
    """

    name: str = "url_to_markdown"
    description: str = (
        "Fetches the content of a webpage from a given URL and converts it to Markdown format. "
        "Provide the URL as input. The tool will return the main content of the page formatted as Markdown."
    )

    def _run(self, url: str) -> str:
        """
        Synchronous version of the tool (falls back to async implementation).
        :param url: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        raise NotImplementedError("Use async version of this tool")

    async def _arun(self, url: str) -> str:
        """
        Asynchronous version of the tool.
        :param url: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    response.raise_for_status()
                    html_content = await response.text()

            soup = BeautifulSoup(html_content, "html.parser")

            # Extract the main content (e.g., headings and paragraphs)
            markdown_content = ""
            for element in soup.find_all(
                ["h1", "h2", "h3", "h4", "h5", "h6", "p", "ul", "ol", "li"]
            ):
                if element.name.startswith("h"):
                    level = element.name[1]
                    markdown_content += (
                        f"{'#' * int(level)} {element.get_text().strip()}\n\n"
                    )
                elif element.name == "p":
                    markdown_content += f"{element.get_text().strip()}\n\n"
                elif element.name in ["ul", "ol"]:
                    for li in element.find_all("li"):
                        prefix = "-" if element.name == "ul" else "1."
                        markdown_content += f"{prefix} {li.get_text().strip()}\n"

            return markdown_content.strip()
        except Exception as e:
            raise ValueError(f"Failed to fetch or process the URL: {str(e)}")
