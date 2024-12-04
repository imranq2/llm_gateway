import os
from os import makedirs
from pathlib import Path
from uuid import uuid4


class ImageGenerationHelper:
    @staticmethod
    def get_full_path() -> Path:
        """
        Get the full path for a new file to be generated

        :return:
        """
        image_generation_path_ = os.environ["IMAGE_GENERATION_PATH"]
        assert (
            image_generation_path_
        ), "IMAGE_GENERATION_PATH environment variable is not set"
        image_generation_path = Path(image_generation_path_)
        makedirs(image_generation_path, exist_ok=True)
        image_file_name = f"{uuid4()}.png"
        image_generation_full_path: Path = image_generation_path.joinpath(
            image_file_name
        )
        return image_generation_full_path

    @staticmethod
    def get_url_for_file_name(image_file_path: Path) -> str:
        """
        Get the URL for a given image file name

        :param image_file_path:
        :return:
        """

        # get just the image file name
        image_file_name: str = image_file_path.name

        image_generation_url = os.environ["IMAGE_GENERATION_URL"]
        url = f"{image_generation_url}/{image_file_name}"
        return url
