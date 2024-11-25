from typing import Dict

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.providers.base_chat_completions_provider import (
    BaseChatCompletionsProvider,
)
from language_model_gateway.gateway.providers.openai_chat_completions_provider import (
    OpenAiChatCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


class ChatCompletionManager:
    # noinspection PyMethodMayBeStatic
    async def chat_completions(
        self,
        *,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        # Use the model to choose the provider
        model: str = chat_request["model"]

        # Use the provider to get the completions
        provider: BaseChatCompletionsProvider = OpenAiChatCompletionsProvider()
        return await provider.chat_completions(
            headers=headers, chat_request=chat_request
        )
