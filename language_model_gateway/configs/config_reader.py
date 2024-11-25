import json
from pathlib import Path

from typing import List

from language_model_gateway.configs.config_schema import ModelConfig


class ConfigReader:
    # noinspection PyMethodMayBeStatic
    def read_model_config(self) -> List[ModelConfig]:
        config_folder: Path = Path(__file__).parent
        # Read the JSON file
        with open(config_folder.joinpath("chat_completions.json"), "r") as file:
            data = json.load(file)

        # Parse the JSON data into ModelConfig objects
        configs = [ModelConfig(**config) for config in data]
        return configs
