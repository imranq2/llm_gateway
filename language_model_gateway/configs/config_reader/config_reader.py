import os
from typing import List

from language_model_gateway.configs.config_reader.file_config_reader import (
    FileConfigReader,
)
from language_model_gateway.configs.config_reader.github_config_reader import (
    GitHubConfigReader,
)
from language_model_gateway.configs.config_reader.s3_config_reader import S3ConfigReader
from language_model_gateway.configs.config_schema import ChatModelConfig


class ConfigReader:
    # noinspection PyMethodMayBeStatic
    async def read_model_configs_async(self) -> List[ChatModelConfig]:
        config_path: str = os.environ["CONFIG_PATH"]
        assert config_path is not None, "CONFIG_PATH environment variable is not set"

        models: List[ChatModelConfig]
        if config_path.startswith("s3"):
            models = S3ConfigReader().read_model_configs(s3_url=config_path)
        elif "github.com" in config_path:
            models = await GitHubConfigReader(
                os.environ.get("GITHUB_TOKEN")
            ).read_model_configs(github_url=config_path)
        else:
            models = FileConfigReader().read_model_configs(config_path=config_path)

        # if we can't load models another way then try to load them from the file system
        if not models or len(models) == 0:
            config_path_backup: str = os.environ["CONFIG_PATH_BACKUP"]
            models = FileConfigReader().read_model_configs(
                config_path=config_path_backup
            )

        return models
