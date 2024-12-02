from langchain_core.language_models import BaseChatModel

from language_model_gateway.configs.config_schema import ModelConfig
from language_model_gateway.gateway.models.model_factory import ModelFactory
from tests.gateway.mocks.mock_get_model_protocol import MockGetModelProtocol


class MockModelFactory(ModelFactory):
    def __init__(self, *, fn_get_model: MockGetModelProtocol) -> None:
        super().__init__()
        self.fn_get_model: MockGetModelProtocol = fn_get_model
        assert self.fn_get_model is not None
        assert isinstance(self.fn_get_model, MockGetModelProtocol)

    def get_model(self, model_config: ModelConfig) -> BaseChatModel:
        return self.fn_get_model(model_config=model_config)
