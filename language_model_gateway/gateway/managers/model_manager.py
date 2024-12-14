import logging
from typing import Dict, List

from language_model_gateway.configs.config_reader.config_reader import ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig


class ModelManager:
    def __init__(self, *, config_reader: ConfigReader) -> None:
        self.config_reader: ConfigReader = config_reader
        assert self.config_reader is not None
        assert isinstance(self.config_reader, ConfigReader)

    # noinspection PyMethodMayBeStatic
    async def get_models(
        self,
        *,
        headers: Dict[str, str],
    ) -> Dict[str, List[Dict[str, str]]]:
        configs: List[ChatModelConfig] = (
            await self.config_reader.read_model_configs_async()
        )
        logger = logging.getLogger(__name__)
        logger.info("Received request for models")
        models = [
            {"id": config.name, "description": config.description} for config in configs
        ]
        return {"data": models}
