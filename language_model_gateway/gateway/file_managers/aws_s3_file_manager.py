import logging
import os
from typing import Optional

import boto3
from botocore.exceptions import ClientError

from language_model_gateway.gateway.utilities.url_parser import UrlParser

logger = logging.getLogger(__name__)


class AwsS3FileManager:
    # noinspection PyMethodMayBeStatic
    def _create_s3_client(self) -> boto3.client:
        """Create and return a Bedrock client"""
        session1 = boto3.Session(profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"))
        bedrock_client = session1.client(
            service_name="s3",
            region_name="us-east-1",
        )
        return bedrock_client

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
        bucket_name: str
        prefix: str
        full_path = folder + "/" + filename
        bucket_name, prefix = UrlParser.parse_s3_uri(full_path)

        assert bucket_name
        assert prefix

        s3_client = self._create_s3_client()
        if not image_data:
            logger.error("No image to save")
            return None

        try:
            # Convert Path to string for S3 key
            s3_key = str(filename)

            # Upload the image to S3
            s3_client.put_object(
                Bucket=bucket_name,
                Key=s3_key,
                Body=image_data,
                ContentType="image/png",  # Adjust content type as needed
            )

            logger.info(f"Image saved to S3: s3://{bucket_name}/{s3_key}")
            return f"s3://{bucket_name}/{s3_key}"

        except ClientError as e:
            logger.error(f"Error saving image to S3: {e}")
            raise
