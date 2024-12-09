import logging
import os
from urllib.parse import urlparse
import boto3
import json
import time
import asyncio
from typing import List, Tuple, Optional
from botocore.exceptions import ClientError
from language_model_gateway.configs.config_schema import ChatModelConfig

logger = logging.getLogger(__name__)


class S3ConfigReader:
    # Class-level cache, lock, and timestamp
    _config_cache: Optional[List[ChatModelConfig]] = None
    _cache_timestamp: Optional[float] = None
    _lock: asyncio.Lock = asyncio.Lock()
    _CACHE_TTL: int = (
        int(os.environ["CONFIG_CACHE_TIMEOUT_SECONDS"])
        if os.environ.get("CONFIG_CACHE_TIMEOUT_SECONDS")
        else 60 * 60
    )  # 60 minutes in seconds

    @staticmethod
    def parse_s3_uri(uri: str) -> Tuple[str, str]:
        parsed = urlparse(uri)
        if parsed.scheme != "s3":
            raise ValueError(f"Invalid S3 URI scheme: {uri}")

        bucket = parsed.netloc
        path = parsed.path.lstrip("/")  # Remove leading slash

        return bucket, path

    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Check if the cache is still valid"""
        if cls._config_cache is None or cls._cache_timestamp is None:
            return False
        return time.time() - cls._cache_timestamp < cls._CACHE_TTL

    async def read_model_configs(self, *, s3_url: str) -> List[ChatModelConfig]:
        """
        Read model configurations from JSON files stored in an S3 bucket
        """
        # If configs are cached and not expired, return them
        if self._is_cache_valid():
            assert self._config_cache is not None
            return self._config_cache

        # Use lock to prevent multiple simultaneous loads
        async with self._lock:
            # Check again in case another request loaded the configs while we were waiting
            if self._is_cache_valid():
                assert self._config_cache is not None
                return self._config_cache

            bucket_name, prefix = self.parse_s3_uri(s3_url)
            try:
                models = await self._read_model_configs(
                    bucket_name=bucket_name, prefix=prefix
                )
                # Store in cache with timestamp
                self.__class__._config_cache = models
                self.__class__._cache_timestamp = time.time()
                return models
            except Exception as e:
                logger.error(f"Error reading model configurations from S3: {str(e)}")
                logger.exception(e, stack_info=True)
                return []

    @classmethod
    async def _read_model_configs(
        cls, *, bucket_name: str, prefix: str
    ) -> List[ChatModelConfig]:
        """
        Read model configurations from JSON files stored in an S3 bucket

        Args:
            bucket_name: The name of the S3 bucket
            prefix: The prefix (folder path) where the config files are stored
        """
        assert bucket_name
        assert prefix

        logger.info(f"Reading model configurations from S3: {bucket_name}/{prefix}")

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
                                logger.error(
                                    f"Error reading file {obj['Key']}: {str(e)}"
                                )
                            except json.JSONDecodeError as e:
                                logger.error(
                                    f"Error parsing JSON from {obj['Key']}: {str(e)}"
                                )

            return configs

        except Exception as e:
            logger.error(f"Error reading configs from S3: {str(e)}")
            raise

    @classmethod
    async def clear_cache(cls) -> None:
        """Clear the configuration cache"""
        async with cls._lock:
            cls._config_cache = None
            cls._cache_timestamp = None
