from os import environ
from typing import Dict

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool

from language_model_gateway.configs.config_schema import ToolChoice
from language_model_gateway.gateway.tools.current_time_tool import CurrentTimeTool
from langchain_community.tools.pubmed.tool import PubmedQueryRun

from language_model_gateway.gateway.tools.google_search_tool import GoogleSearchTool


class ToolProvider:
    def __init__(self) -> None:
        web_search_tool: BaseTool
        default_web_search_tool: str = environ.get(
            "DEFAULT_WEB_SEARCH_TOOL", "duckduckgo"
        )
        match default_web_search_tool:
            case "duckduckgo_search":
                web_search_tool = DuckDuckGoSearchRun()
            case "google_search":
                web_search_tool = GoogleSearchTool()
            case _:
                raise ValueError(
                    f"Unknown default web search tool: {default_web_search_tool}"
                )

        self.tools: Dict[str, BaseTool] = {
            "current_date": CurrentTimeTool(),
            "web_search": web_search_tool,
            "pubmed": PubmedQueryRun(),
            "google_search": GoogleSearchTool(),
            "duckduckgo_search": DuckDuckGoSearchRun(),
        }

    def get_tool_by_name(self, *, tool: ToolChoice) -> BaseTool:
        if tool.name in self.tools:
            return self.tools[tool.name]
        raise ValueError(f"Tool with name {tool.name} not found")

    def get_tools(self, *, tools: list[ToolChoice]) -> list[BaseTool]:
        return [self.get_tool_by_name(tool=tool) for tool in tools]
