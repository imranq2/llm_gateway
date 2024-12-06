import logging
from typing import Dict, List

from language_model_gateway.configs.config_reader.config_reader import ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig


class ModelManager:
    # noinspection PyMethodMayBeStatic
    async def get_models(
        self, *, headers: Dict[str, str]
    ) -> Dict[str, List[Dict[str, str]]]:
        logger = logging.getLogger(__name__)
        logger.info("Received request for models")
        configs: List[ChatModelConfig] = ConfigReader().read_model_configs()
        models = [
            {"id": config.name, "description": config.description} for config in configs
        ]
        return {"data": models}
