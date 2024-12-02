import os

from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from language_model_gateway.configs.config_schema import ModelConfig


class ModelFactory:
    # noinspection PyMethodMayBeStatic
    def get_model(self, model_config: ModelConfig) -> BaseChatModel:
        assert model_config is not None
        model_vendor: str = model_config.provider
        model_name: str = model_config.model

        # noinspection PyArgumentList
        llm: BaseChatModel = (
            ChatOpenAI(model=model_name, temperature=0)
            if model_vendor == "openai"
            else ChatBedrockConverse(
                client=None,
                provider="anthropic",
                credentials_profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"),
                # Setting temperature to 0 for deterministic results
                temperature=0,
                model=model_name,
            )
        )
        return llm
