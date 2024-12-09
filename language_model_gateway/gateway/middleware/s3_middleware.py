from typing import List, Callable, Awaitable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from language_model_gateway.gateway.file_managers.aws_s3_file_manager import (
    AwsS3FileManager,
)
from language_model_gateway.gateway.utilities.url_parser import UrlParser


class S3Middleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
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

            return await self.handle_s3_request(request)

        return await call_next(request)

    async def handle_s3_request(self, request: Request) -> Response:

        if self.image_generation_path.startswith("s3"):
            bucket_name, prefix = UrlParser.parse_s3_uri(self.image_generation_path)
            # Check file extension
            if not self.check_extension(str(request.url.path)):
                return Response(status_code=403, content="File type not allowed")

            s3_key = str(prefix) + str(request.url.path)

            return await AwsS3FileManager().handle_s3_request(
                bucket_name=bucket_name,
                s3_key=s3_key,
            )
        else:
            # read and return file
            full_path: str = self.image_generation_path + request.url.path
            return await self.read_file_async(full_path)

    async def read_file_async(self, full_path: str) -> Response:
        # read and return file
        try:
            with open(full_path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            return Response(status_code=404, content="File not found")
        return Response(content=content)
