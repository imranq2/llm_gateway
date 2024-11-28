import logging
from typing import Dict, List

from openai.types.chat import ChatCompletionSystemMessageParam
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.configs.config_reader import ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig, PromptConfig
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

logger = logging.getLogger(__name__)


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

        chat_request = self.add_system_messages(
            chat_request=chat_request, system_prompts=model_config.prompts
        )

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

        logger.info(f"Running chat completion for {chat_request}")
        # Use the provider to get the completions
        return await provider.chat_completions(
            model_config=model_config, headers=headers, chat_request=chat_request
        )

    # noinspection PyMethodMayBeStatic
    def add_system_messages(
        self, chat_request: ChatRequest, system_prompts: List[PromptConfig] | None
    ) -> ChatRequest:
        # see if there are any system prompts in chat_request
        has_system_messages_in_chat_request: bool = any(
            [
                message
                for message in chat_request["messages"]
                if message["role"] == "system"
            ]
        )
        if (
            not has_system_messages_in_chat_request
            and system_prompts is not None
            and len(system_prompts) > 0
        ):
            system_messages: List[ChatCompletionSystemMessageParam] = [
                ChatCompletionSystemMessageParam(role="system", content=message.content)
                for message in system_prompts
                if message.role == "system" and message.content is not None
            ]
            chat_request["messages"] = system_messages + [
                r for r in chat_request["messages"]
            ]

        return chat_request
