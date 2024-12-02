from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
)
from language_model_gateway.gateway.providers.openai_chat_completions_provider import (
    OpenAiChatCompletionsProvider,
)


class ContainerCreator:
    # noinspection PyMethodMayBeStatic
    async def create_container_async(self) -> SimpleContainer:
        container = SimpleContainer()

        # register services here
        container.register(
            OpenAiChatCompletionsProvider, lambda c: OpenAiChatCompletionsProvider()
        )
        container.register(
            LangChainCompletionsProvider, lambda c: LangChainCompletionsProvider()
        )
        container.register(
            ChatCompletionManager,
            lambda c: ChatCompletionManager(
                open_ai_provider=c.resolve(OpenAiChatCompletionsProvider),
                langchain_provider=c.resolve(LangChainCompletionsProvider),
            ),
        )
        container.register(ModelManager, lambda c: ModelManager())
        return container
