from urllib.parse import urlparse

import boto3
import json
from typing import List, Tuple
from botocore.exceptions import ClientError
from cachetools.func import ttl_cache

from language_model_gateway.configs.config_schema import ChatModelConfig


class S3ConfigReader:
    @staticmethod
    def parse_s3_uri(uri: str) -> Tuple[str, str]:
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI scheme: {uri}")

        bucket = parsed.netloc
        path = parsed.path.lstrip("/")  # Remove leading slash

        return bucket, path

    def read_model_configs(self, *, s3_url: str) -> List[ChatModelConfig]:
        bucket_name, prefix = self.parse_s3_uri(s3_url)
        return self._read_model_configs(bucket_name=bucket_name, prefix=prefix)

    # noinspection PyMethodMayBeStatic
    @ttl_cache(ttl=60 * 60)
    def _read_model_configs(
        self, *, bucket_name: str, prefix: str
    ) -> List[ChatModelConfig]:
        """
        Read model configurations from JSON files stored in an S3 bucket

        Args:
            bucket_name: The name of the S3 bucket
            prefix: The prefix (folder path) where the config files are stored
        """
        configs: List[ChatModelConfig] = []

        # Initialize S3 client
        s3_client = boto3.client("s3")

        try:
            # List all objects in the specified prefix
            paginator = s3_client.get_paginator("list_objects_v2")
            page_iterator = paginator.paginate(Bucket=bucket_name, Prefix=prefix)

            # Iterate through all objects with .json extension
            for page in page_iterator:
                if "Contents" in page:
                    for obj in page["Contents"]:
                        if obj["Key"].endswith(".json"):
                            try:
                                # Get the JSON file content
                                response = s3_client.get_object(
                                    Bucket=bucket_name, Key=obj["Key"]
                                )

                                # Parse JSON content
                                data = json.loads(
                                    response["Body"].read().decode("utf-8")
                                )
                                configs.append(ChatModelConfig(**data))

                            except ClientError as e:
                                print(f"Error reading file {obj['Key']}: {str(e)}")
                            except json.JSONDecodeError as e:
                                print(f"Error parsing JSON from {obj['Key']}: {str(e)}")
                            except Exception as e:
                                print(
                                    f"Unexpected error processing {obj['Key']}: {str(e)}"
                                )

        except ClientError as e:
            print(f"Error accessing S3 bucket: {str(e)}")
            raise

        # Sort configs by name
        configs.sort(key=lambda x: x.name)
        return configs
