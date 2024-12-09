import logging
import os
from typing import List, Any, Dict

from langchain_aws import ChatBedrockConverse
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from language_model_gateway.configs.config_schema import (
    ModelConfig,
    ModelParameterConfig,
    ChatModelConfig,
)

logger = logging.getLogger(__name__)


class ModelFactory:
    # noinspection PyMethodMayBeStatic
    def get_model(self, chat_model_config: ChatModelConfig) -> BaseChatModel:
        assert chat_model_config is not None
        assert isinstance(chat_model_config, ChatModelConfig)
        model_config: ModelConfig | None = chat_model_config.model
        assert model_config is not None
        model_vendor: str = model_config.provider
        model_name: str = model_config.model

        model_parameters: List[ModelParameterConfig] | None = (
            chat_model_config.model_parameters
        )

        # convert model_parameters to dict
        model_parameters_dict: Dict[str, Any] = {}
        if model_parameters is not None:
            model_parameter: ModelParameterConfig
            for model_parameter in model_parameters:
                model_parameters_dict[model_parameter.key] = model_parameter.value

        logger.debug(f"Creating ChatModel with parameters: {model_parameters_dict}")
        model_parameters_dict["model"] = model_name
        # model_parameters_dict["streaming"] = True
        llm: BaseChatModel = (
            ChatOpenAI(**model_parameters_dict)
            if model_vendor == "openai"
            else ChatBedrockConverse(
                client=None,
                provider="anthropic",
                credentials_profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"),
                region_name=os.environ.get("AWS_REGION", "us-east-1"),
                # Setting temperature to 0 for deterministic results
                **model_parameters_dict,
            )
        )
        return llm
