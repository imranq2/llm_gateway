from typing import List, Callable, Awaitable, Annotated

from fastapi import FastAPI, Request, Response
from fastapi.params import Depends
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse

from language_model_gateway.gateway.api_container import get_aws_client_factory
from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory
from language_model_gateway.gateway.file_managers.aws_s3_file_manager import (
    AwsS3FileManager,
)
from language_model_gateway.gateway.utilities.url_parser import UrlParser


class S3Middleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: FastAPI,
        aws_client_factory: Annotated[
            AwsClientFactory, Depends(get_aws_client_factory)
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
        self.aws_client_factory = aws_client_factory

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

    async def handle_s3_request(self, request: Request) -> Response | StreamingResponse:

        if self.image_generation_path.startswith("s3"):
            bucket_name, prefix = UrlParser.parse_s3_uri(self.image_generation_path)
            # Check file extension
            file_path = str(request.url.path)
            # remove the target path
            file_path = file_path[len(self.target_path) :]

            if not self.check_extension(file_path):
                return Response(status_code=403, content="File type not allowed")

            # combine the prefix and file path and include / if needed
            if prefix and not prefix.endswith("/"):
                prefix += "/"
            # remove / from file path if it exists
            if file_path.startswith("/"):
                file_path = file_path[1:]
            s3_key = str(prefix) + file_path

            return await AwsS3FileManager(
                aws_client_factory=self.aws_client_factory
            ).handle_s3_request(
                bucket_name=bucket_name,
                s3_key=s3_key,
            )
        else:
            # read and return file
            full_path: str = self.image_generation_path + request.url.path
            return await self.read_file_async(full_path)

    # noinspection PyMethodMayBeStatic
    async def read_file_async(self, full_path: str) -> Response:
        # read and return file
        try:
            with open(full_path, "rb") as f:
                content = f.read()
        except FileNotFoundError:
            return Response(status_code=404, content="File not found")
        return Response(content=content)
