from typing import Dict, Any

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest
from tests_integration.gateway.mocks.mock_chat_response import MockChatResponseProtocol


class MockLangChainChatCompletionsProvider(LangChainCompletionsProvider):
    def __init__(self, fn_get_response: MockChatResponseProtocol) -> None:
        self.fn_get_response: MockChatResponseProtocol = fn_get_response

    async def chat_completions(
        self,
        *,
        model_config: ChatModelConfig,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        result: Dict[str, Any] = self.fn_get_response(
            model_config=model_config,
            headers=headers,
            chat_request=chat_request,
        )
        return JSONResponse(content=result)
