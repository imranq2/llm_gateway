import logging
from typing import Optional

from starlette.responses import Response, StreamingResponse

logger = logging.getLogger(__name__)


class FileManager:
    # noinspection PyMethodMayBeStatic
    async def save_file_async(
        self, *, image_data: bytes, folder: str, filename: str
    ) -> Optional[str]:
        raise NotImplementedError("Must be implemented in a subclass")

    # noinspection PyMethodMayBeStatic
    def get_full_path(self, *, filename: str, folder: str) -> str:
        raise NotImplementedError("Must be implemented in a subclass")

    async def read_file_async(
        self, *, folder: str, file_path: str
    ) -> StreamingResponse | Response:
        raise NotImplementedError("Must be implemented in a subclass")
