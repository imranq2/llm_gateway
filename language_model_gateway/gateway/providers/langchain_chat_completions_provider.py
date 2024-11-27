import datetime
import os
import random
from typing import Dict, Any, Sequence

from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_core.tools import Tool, BaseTool
from langchain_openai import ChatOpenAI
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.converters.langgraph_to_openai_converter import (
    LangGraphToOpenAIConverter,
)
from language_model_gateway.gateway.providers.base_chat_completions_provider import (
    BaseChatCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


class LangChainCompletionsProvider(BaseChatCompletionsProvider):
    async def chat_completions(
        self, *, headers: Dict[str, str], chat_request: ChatRequest
    ) -> StreamingResponse | JSONResponse:
        model_vendor: str = "openai"

        # noinspection PyArgumentList
        llm: BaseChatModel = (
            ChatOpenAI(model="gpt-4o", temperature=0)
            if model_vendor == "openai"
            else ChatBedrockConverse(
                client=None,
                provider="anthropic",
                credentials_profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"),
                # Setting temperature to 0 for deterministic results
                temperature=0,
                model=os.environ["AWS_CLAUDE3_5_MODEL"],
            )
        )

        # noinspection PyUnusedLocal
        def get_current_time(*args: Any, **kwargs: Any) -> str:
            """Returns the current time in H:MM AM/PM format."""
            now = datetime.datetime.now()  # Get current time
            return now.strftime("%Y-%m-%d %H:%M:%S%Z%z")

        # Initialize tools
        tools: Sequence[BaseTool] = [
            Tool(
                name="Time",  # Name of the tool
                func=get_current_time,  # Function that the tool will execute
                # Description of the tool
                description="Useful for when you need to know the current time",
            )
        ]
        converter: LangGraphToOpenAIConverter = LangGraphToOpenAIConverter()
        compiled_state_graph = LangGraphToOpenAIConverter.create_graph_for_llm(
            llm=llm,
            tools=tools,
        )
        request_id = random.randint(1, 1000)

        return await converter.call_agent_with_input(
            request_id=str(request_id),
            compiled_state_graph=compiled_state_graph,
            request=chat_request,
            system_messages=[],
        )
