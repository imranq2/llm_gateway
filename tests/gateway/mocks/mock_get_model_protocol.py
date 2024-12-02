from typing import Protocol, runtime_checkable

from langchain_core.language_models import BaseChatModel

from language_model_gateway.configs.config_schema import ModelConfig


@runtime_checkable
class MockGetModelProtocol(Protocol):
    def __call__(self, *, model_config: ModelConfig) -> BaseChatModel: ...
