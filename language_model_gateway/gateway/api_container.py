import logging
from typing import Annotated

from fastapi import Depends

from language_model_gateway.container.container_factory import ContainerFactory
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.image_generation_manager import (
    ImageGenerationManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.utilities.cached import cached

logger = logging.getLogger(__name__)


@cached  # makes it singleton-like
async def get_container_async() -> SimpleContainer:
    """Create the container"""
    return await ContainerFactory().create_container_async()


def get_chat_manager(
    container: Annotated[SimpleContainer, Depends(get_container_async)]
) -> ChatCompletionManager:
    """helper function to get the chat manager"""
    assert isinstance(container, SimpleContainer), type(container)
    return container.resolve(ChatCompletionManager)


def get_model_manager(
    container: Annotated[SimpleContainer, Depends(get_container_async)]
) -> ModelManager:
    """helper function to get the model manager"""
    assert isinstance(container, SimpleContainer), type(container)
    return container.resolve(ModelManager)


def get_image_generation_manager(
    container: Annotated[SimpleContainer, Depends(get_container_async)]
) -> ImageGenerationManager:
    """helper function to get the model manager"""
    assert isinstance(container, SimpleContainer), type(container)
    return container.resolve(ImageGenerationManager)
