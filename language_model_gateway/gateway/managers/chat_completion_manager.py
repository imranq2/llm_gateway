import logging
from typing import Dict, List

from openai.types.chat import ChatCompletionSystemMessageParam
from starlette.responses import StreamingResponse, JSONResponse

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
    """
    Implements the chat completion manager following the OpenAI API
    https://platform.openai.com/docs/overview
    https://github.com/openai/openai-python/blob/main/api.md


    """

    def __init__(
        self,
        *,
        open_ai_provider: OpenAiChatCompletionsProvider,
        langchain_provider: LangChainCompletionsProvider,
    ) -> None:
        """
        Chat completion manager

        :param open_ai_provider: provider to use for OpenAI completions
        :param langchain_provider: provider to use for LangChain completions
        :return:
        """

        self.openai_provider: OpenAiChatCompletionsProvider = open_ai_provider
        assert self.openai_provider is not None
        assert isinstance(self.openai_provider, OpenAiChatCompletionsProvider)
        self.langchain_provider: LangChainCompletionsProvider = langchain_provider
        assert self.langchain_provider is not None
        assert isinstance(self.langchain_provider, LangChainCompletionsProvider)

    # noinspection PyMethodMayBeStatic
    async def chat_completions(
        self,
        *,
        configs: List[ChatModelConfig],
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        # Use the model to choose the provider
        model: str = chat_request["model"]
        assert model is not None

        # Find the model config
        model_config: ChatModelConfig | None = next(
            (config for config in configs if config.name.lower() == model.lower()), None
        )
        if model_config is None:
            return JSONResponse(content=f"Model {model} not found in the config")

        chat_request = self.add_system_messages(
            chat_request=chat_request, system_prompts=model_config.system_prompts
        )

        provider: BaseChatCompletionsProvider
        match model_config.type:
            case "openai":
                provider = self.openai_provider
            case "langchain":
                provider = self.langchain_provider
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
