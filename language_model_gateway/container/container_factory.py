import os

from language_model_gateway.configs.config_reader.config_reader import ConfigReader
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.converters.langgraph_to_openai_converter import (
    LangGraphToOpenAIConverter,
)
from language_model_gateway.gateway.http.http_client_factory import HttpClientFactory
from language_model_gateway.gateway.image_generation.image_generator_factory import (
    ImageGeneratorFactory,
)
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.image_generation_manager import (
    ImageGenerationManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.models.model_factory import ModelFactory
from language_model_gateway.gateway.providers.image_generation_provider import (
    ImageGenerationProvider,
)

from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
)
from language_model_gateway.gateway.providers.openai_chat_completions_provider import (
    OpenAiChatCompletionsProvider,
)
from language_model_gateway.gateway.tools.tool_provider import ToolProvider
from language_model_gateway.gateway.utilities.expiring_cache import ExpiringCache


class ContainerFactory:
    # noinspection PyMethodMayBeStatic
    async def create_container_async(self) -> SimpleContainer:
        container = SimpleContainer()

        # register services here
        container.register(HttpClientFactory, lambda c: HttpClientFactory())

        container.register(
            OpenAiChatCompletionsProvider,
            lambda c: OpenAiChatCompletionsProvider(
                http_client_factory=c.resolve(HttpClientFactory)
            ),
        )
        container.register(ModelFactory, lambda c: ModelFactory())

        container.register(ImageGeneratorFactory, lambda c: ImageGeneratorFactory())

        container.register(
            LangGraphToOpenAIConverter, lambda c: LangGraphToOpenAIConverter()
        )
        container.register(
            ToolProvider,
            lambda c: ToolProvider(
                image_generator_factory=c.resolve(ImageGeneratorFactory)
            ),
        )
        container.register(
            LangChainCompletionsProvider,
            lambda c: LangChainCompletionsProvider(
                model_factory=c.resolve(ModelFactory),
                lang_graph_to_open_ai_converter=c.resolve(LangGraphToOpenAIConverter),
                tool_provider=c.resolve(ToolProvider),
            ),
        )
        # we want only one instance of the cache so we use singleton
        container.singleton(
            ExpiringCache,
            ExpiringCache(
                ttl_seconds=(
                    int(os.environ["CONFIG_CACHE_TIMEOUT_SECONDS"])
                    if os.environ.get("CONFIG_CACHE_TIMEOUT_SECONDS")
                    else 60 * 60
                )
            ),
        )

        container.register(
            ConfigReader, lambda c: ConfigReader(cache=c.resolve(ExpiringCache))
        )
        container.register(
            ChatCompletionManager,
            lambda c: ChatCompletionManager(
                open_ai_provider=c.resolve(OpenAiChatCompletionsProvider),
                langchain_provider=c.resolve(LangChainCompletionsProvider),
                config_reader=c.resolve(ConfigReader),
            ),
        )

        container.register(
            ImageGenerationProvider,
            lambda c: ImageGenerationProvider(
                image_generator_factory=c.resolve(ImageGeneratorFactory)
            ),
        )
        container.register(
            ImageGenerationManager,
            lambda c: ImageGenerationManager(
                image_generation_provider=c.resolve(ImageGenerationProvider)
            ),
        )

        container.register(
            ModelManager, lambda c: ModelManager(config_reader=c.resolve(ConfigReader))
        )
        return container
