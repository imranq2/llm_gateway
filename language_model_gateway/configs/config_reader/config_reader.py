import os
from typing import List

from language_model_gateway.configs.config_reader.file_config_reader import (
    FileConfigReader,
)
from language_model_gateway.configs.config_reader.s3_config_reader import S3ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig


class ConfigReader:
    # noinspection PyMethodMayBeStatic
    def read_model_configs(self) -> List[ChatModelConfig]:
        config_path: str = os.environ["CONFIG_PATH"]
        assert config_path is not None, "CONFIG_PATH environment variable is not set"

        if config_path.startswith("s3"):
            return S3ConfigReader().read_model_configs(s3_url=config_path)
        else:
            return FileConfigReader().read_model_configs(config_path=config_path)
