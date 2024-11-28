import json
from pathlib import Path

from typing import List

from language_model_gateway.configs.config_schema import ChatModelConfig


class ConfigReader:
    # noinspection PyMethodMayBeStatic
    def read_model_config(self) -> List[ChatModelConfig]:
        config_folder: Path = Path(__file__).parent.joinpath("chat_completions")
        # read all the .json files recursively in the config folder
        # for each file, parse the json data into ModelConfig
        configs: List[ChatModelConfig] = []

        # Read all the .json files recursively in the config folder
        for json_file in config_folder.rglob("*.json"):
            with open(json_file, "r") as file:
                data = json.load(file)
                configs.append(ChatModelConfig(**data))

        return configs
