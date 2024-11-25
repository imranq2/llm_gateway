import logging
from typing import Dict, List

from language_model_gateway.configs.config_reader import ConfigReader
from language_model_gateway.configs.config_schema import ModelConfig


class ModelManager:
    @staticmethod
    async def get_models() -> Dict[str, List[Dict[str, str]]]:
        logger = logging.getLogger(__name__)
        logger.info("Received request for models")
        configs: List[ModelConfig] = ConfigReader().read_model_config()
        models = [
            {"id": config.model, "description": config.description}
            for config in configs
        ]
        return {"data": models}
