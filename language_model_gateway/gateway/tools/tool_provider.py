from typing import Dict

from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import BaseTool

from language_model_gateway.configs.config_schema import ToolChoice
from language_model_gateway.gateway.tools.current_time_tool import CurrentTimeTool
from langchain_community.tools.pubmed.tool import PubmedQueryRun


class ToolProvider:
    tools: Dict[str, BaseTool] = {
        "current_date": CurrentTimeTool(),
        "web_search": DuckDuckGoSearchRun(),
        "pubmed": PubmedQueryRun(),
    }

    def get_tool_by_name(self, *, tool: ToolChoice) -> BaseTool:
        if tool.name in self.tools:
            return self.tools[tool.name]
        raise ValueError(f"Tool with name {tool.name} not found")

    def get_tools(self, *, tools: list[ToolChoice]) -> list[BaseTool]:
        return [self.get_tool_by_name(tool=tool) for tool in tools]
