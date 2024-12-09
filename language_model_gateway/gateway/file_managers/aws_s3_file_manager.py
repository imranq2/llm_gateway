import logging
from typing import Optional, Generator

from botocore.exceptions import ClientError
from starlette.responses import Response, StreamingResponse

from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory
from language_model_gateway.gateway.utilities.url_parser import UrlParser

logger = logging.getLogger(__name__)


class AwsS3FileManager:
    def __init__(self, *, aws_client_factory: AwsClientFactory) -> None:
        self.aws_client_factory = aws_client_factory
        assert self.aws_client_factory is not None
        assert isinstance(self.aws_client_factory, AwsClientFactory)

    async def save_file_async(
        self, *, image_data: bytes, folder: str, filename: str
    ) -> Optional[str]:
        """
        Save the generated image to S3

        :param image_data: Image bytes to save
        :param filename: Filename to use in S3
        :param folder: Folder to save the image in
        """
        # Parse S3 URL
        bucket_name: str = self.get_bucket(filename=filename, folder=folder)
        s3_key = str(filename)

        s3_full_path: str = self.get_full_path(bucket_name=bucket_name, s3_key=s3_key)

        s3_client = self.aws_client_factory.create_client(service_name="s3")
        if not image_data:
            logger.error("No image to save")
            return None

        try:
            # Upload the image to S3
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType="image/png",  # Adjust content type as needed
            )

            logger.info(f"Image saved to S3: {s3_full_path}")
            return s3_full_path

        except ClientError as e:
            logger.error(f"Error saving image to S3: {e}")
            raise

    # noinspection PyMethodMayBeStatic
    def get_full_path(self, *, bucket_name: str, s3_key: str) -> str:
        # Convert Path to string for S3 key
        assert bucket_name
        assert s3_key
        s3_full_path = f"s3://{bucket_name}/{s3_key}"
        return s3_full_path

    # noinspection PyMethodMayBeStatic
    def get_bucket(self, *, filename: str, folder: str) -> str:
        bucket_name: str
        prefix: str
        full_path = folder + "/" + filename
        bucket_name, prefix = UrlParser.parse_s3_uri(full_path)
        assert bucket_name
        assert prefix
        return bucket_name

    async def handle_s3_request(self, *, bucket_name: str, s3_key: str) -> Response:
        s3_client = self.aws_client_factory.create_client(service_name="s3")

        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=s3_key)

            content_type = response.get("ContentType", "application/octet-stream")

            def iterate_bytes() -> Generator[bytes, None, None]:
                for chunk in response["Body"].iter_chunks():
                    yield chunk

            return StreamingResponse(
                iterate_bytes(),
                media_type=content_type,
                headers={
                    "Content-Length": str(response["ContentLength"]),
                    "Last-Modified": response["LastModified"].strftime(
                        "%a, %d %b %Y %H:%M:%S GMT"
                    ),
                    "ETag": response["ETag"],
                    # 'Cache-Control': f'public, max-age={self.cache_max_age}',
                    "Accept-Ranges": "bytes",
                },
            )

        except ClientError as e:
            error_code = e.response["Error"]["Code"]
            if error_code == "NoSuchKey":
                return Response(status_code=404, content="File not found")
            elif error_code == "NoSuchBucket":
                return Response(status_code=500, content="Bucket not found")
            else:
                return Response(status_code=500, content="Internal server error")
