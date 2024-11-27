from typing import Dict, List

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.configs.config_reader import ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.gateway.providers.base_chat_completions_provider import (
    BaseChatCompletionsProvider,
)
from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
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
        assert model is not None

        configs: List[ChatModelConfig] = ConfigReader().read_model_config()

        # Find the model config
        model_config: ChatModelConfig | None = next(
            (config for config in configs if config.name.lower() == model.lower()), None
        )
        if model_config is None:
            return JSONResponse(content=f"Model {model} not found in the config")

        provider: BaseChatCompletionsProvider
        match model_config.type:
            case "openai":
                provider = OpenAiChatCompletionsProvider()
            case "langchain":
                provider = LangChainCompletionsProvider()
            case _:
                return JSONResponse(
                    content=f"Model type {model_config.type} not supported"
                )

        # Use the provider to get the completions
        return await provider.chat_completions(
            model_config=model_config, headers=headers, chat_request=chat_request
        )
