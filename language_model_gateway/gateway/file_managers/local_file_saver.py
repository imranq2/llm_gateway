import logging
from os import makedirs
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class LocalFileSaver:
    # noinspection PyMethodMayBeStatic
    async def save_file_async(
        self, *, image_data: bytes, folder: str, filename: str
    ) -> Optional[str]:
        """Save the generated image to a file"""
        file_path: str = self.get_full_path(filename=filename, folder=folder)
        if image_data:
            with open(file_path, "wb") as f:
                f.write(image_data)
            logger.info(f"Image saved as {file_path}")
            return str(file_path)
        else:
            logger.error("No image to save")
            return None

    # noinspection PyMethodMayBeStatic
    def get_full_path(self, *, filename: str, folder: str) -> str:
        image_generation_path = Path(folder)
        makedirs(image_generation_path, exist_ok=True)
        file_path: Path = image_generation_path / filename
        return str(file_path)

    # @override
    # async def save_image_async(self, image_data: bytes, filename: Path) -> None:
    #     """Save the generated image to a file asynchronously"""
    #     if not image_data:
    #         logger.warning("No image data to save")
    #         return
    #
    #     try:
    #         # Use aiofiles for async file operations
    #         async with aiofiles.open(filename, mode='wb') as f:
    #             await f.write(image_data)
    #         logger.info(f"Image saved as {filename}")
    #
    #     except Exception as e:
    #         logger.error(f"Error saving image to {filename}: {str(e)}")
    #         raise
