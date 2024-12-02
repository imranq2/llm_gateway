import logging
from functools import wraps
from typing import Annotated
from typing import Callable, Awaitable

from fastapi import Depends
from typing_extensions import ParamSpec, TypeVar

from language_model_gateway.container.container_creator import ContainerCreator
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager

logger = logging.getLogger(__name__)

# Dependencies
P = ParamSpec("P")
R = TypeVar("R")


def cached(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    """Decorator to cache the result of an async function"""

    cache: R | None = None

    @wraps(f)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        nonlocal cache

        if cache is not None:
            return cache

        cache = await f(*args, **kwargs)
        return cache

    return wrapper


@cached  # makes it singleton-like
async def get_container_async() -> SimpleContainer:
    """Create the container"""
    return await ContainerCreator().create_container_async()


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
