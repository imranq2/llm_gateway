from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)


async def create_container_async() -> SimpleContainer:
    container = SimpleContainer()

    # register services here
    container.register(ChatCompletionManager, lambda c: ChatCompletionManager())
    return container
