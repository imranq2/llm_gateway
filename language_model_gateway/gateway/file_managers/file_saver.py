import logging
from typing import Optional

from language_model_gateway.gateway.file_managers.aws_s3_file_manager import (
    AwsS3FileManager,
)
from language_model_gateway.gateway.file_managers.local_file_saver import LocalFileSaver

logger = logging.getLogger(__name__)


class FileSaver:
    # noinspection PyMethodMayBeStatic
    async def save_file_async(
        self, *, image_data: bytes, folder: str, filename: str
    ) -> Optional[str]:
        if folder.startswith("s3"):
            return await AwsS3FileManager().save_file_async(
                image_data=image_data, folder=folder, filename=filename
            )
        else:
            return await LocalFileSaver().save_file_async(
                image_data=image_data, folder=folder, filename=filename
            )
