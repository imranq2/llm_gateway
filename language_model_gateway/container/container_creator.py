from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager


class ContainerCreator:
    # noinspection PyMethodMayBeStatic
    async def create_container_async(self) -> SimpleContainer:
        container = SimpleContainer()

        # register services here
        container.register(ChatCompletionManager, lambda c: ChatCompletionManager())
        container.register(ModelManager, lambda c: ModelManager())
        return container
