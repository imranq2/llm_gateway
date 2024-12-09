import os
from typing import List, Callable, Awaitable, Annotated

from fastapi import FastAPI, Request, Response
from fastapi.params import Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from language_model_gateway.gateway.api_container import (
    get_file_manager_factory,
)
from language_model_gateway.gateway.file_managers.file_manager import FileManager
from language_model_gateway.gateway.file_managers.file_manager_factory import (
    FileManagerFactory,
)

from language_model_gateway.gateway.utilities.url_parser import UrlParser


class S3Middleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        file_manager_factory: Annotated[
            FileManagerFactory, Depends(get_file_manager_factory)
        ],
        *,
        image_generation_path: str,
        target_path: str = "/image_generation/",
        allowed_extensions: List[str] | None = None,
        cache_max_age: int = 3600,  # 1 hour default cache
    ):
        super().__init__(app)
        self.image_generation_path = image_generation_path
        self.target_path = target_path
        self.allowed_extensions = allowed_extensions
        self.cache_max_age = cache_max_age
        self.file_manager_factory = file_manager_factory

    def check_extension(self, filename: str) -> bool:
        if not self.allowed_extensions:
            return True
        return any(
            filename.lower().endswith(ext.lower()) for ext in self.allowed_extensions
        )

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path.startswith(self.target_path):
            # Optional: Add authentication check here
            # if not await self.is_authenticated(request):
            #     return Response(status_code=401, content='Unauthorized')

            return await self.handle_request(request)

        return await call_next(request)

    async def handle_request(self, request: Request) -> Response | StreamingResponse:

        request_url_path = request.url.path
        folder: str
        file_path: str
        if self.image_generation_path.startswith("s3"):
            bucket_name, prefix = UrlParser.parse_s3_uri(self.image_generation_path)
            # Check file extension
            file_path = str(request_url_path)
            # remove the target path
            file_path = file_path[len(self.target_path) :]

            if not self.check_extension(file_path):
                return Response(status_code=403, content="File type not allowed")

            # combine the prefix and file path and include / if needed
            s3_key = os.path.join(prefix.rstrip("/"), file_path.lstrip("/")).replace(
                "\\", "/"
            )
            folder = bucket_name
            file_path = s3_key
        else:
            # read and return file
            request_url_path = request_url_path[len(self.target_path) :]
            folder = self.image_generation_path
            file_path = request_url_path

        # now stream the file
        file_manager: FileManager = self.file_manager_factory.get_file_manager(
            folder=self.image_generation_path
        )
        return await file_manager.read_file_async(
            folder=folder,
            file_path=file_path,
        )
