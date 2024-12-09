import asyncio
import logging
import os
import time
from uuid import uuid4, UUID

import httpx
import json
from typing import List, Tuple, Optional, Any, Dict
from language_model_gateway.configs.config_schema import ChatModelConfig
from urllib.parse import urlparse, unquote

logger = logging.getLogger(__name__)


class GitHubConfigReader:
    # Class-level cache and lock
    _config_cache: Optional[List[ChatModelConfig]] = None
    _cache_timestamp: Optional[float] = None
    _lock: asyncio.Lock = asyncio.Lock()
    _CACHE_TTL: float = (
        float(os.environ["CONFIG_CACHE_TIMEOUT_SECONDS"])
        if os.environ.get("CONFIG_CACHE_TIMEOUT_SECONDS")
        else 60 * 60
    )  # 60 minutes in seconds
    _identifier: UUID = uuid4()

    def __init__(self, github_token: Optional[str]) -> None:
        """
        Initialize the async GitHub config reader

        Args:
            github_token: Optional GitHub personal access token for private repositories
        """
        self.github_token: Optional[str] = github_token

    @classmethod
    def _is_cache_valid(cls) -> bool:
        """Check if the cache is still valid"""
        if cls._config_cache is None or cls._cache_timestamp is None:
            return False
        current_time: float = time.time()
        logger.info(
            f"Identifier: {cls._identifier} Time: {current_time}, Cache Timestamp: {cls._cache_timestamp}, TTL: {cls._CACHE_TTL}"
        )
        return current_time - cls._cache_timestamp < cls._CACHE_TTL

    @staticmethod
    def parse_github_url(github_url: str) -> Tuple[str, str, str]:
        """
        Parse a GitHub URL into repository, path, and branch components

        Args:
            github_url: Full GitHub URL (e.g., https://github.com/owner/repo/tree/branch/path)

        Returns:
            Tuple of (repo, path, branch)
        """
        parsed = urlparse(github_url)

        if parsed.netloc != "github.com":
            raise ValueError(f"Not a GitHub URL: {github_url}")

        # Split the path into components
        parts = [p for p in parsed.path.split("/") if p]

        if len(parts) < 4 or parts[2] != "tree":
            raise ValueError(
                f"Invalid GitHub URL format. Expected format: "
                f"https://github.com/owner/repo/tree/branch/path"
            )

        owner = parts[0]
        repo = parts[1]
        branch = parts[3]
        path = "/".join(parts[4:])

        # Decode URL-encoded characters
        path = unquote(path)

        return f"{owner}/{repo}", path, branch

    async def read_model_configs(self, *, github_url: str) -> List[ChatModelConfig]:
        """
        Read model configurations from JSON files stored in a GitHub repository
        """
        # If configs are cached and not expired, return them
        logger.info(
            f"Identifier: {self.__class__._identifier} Reading model configurations from GitHub: {github_url}"
        )

        logger.info(
            f"Identifier: {self.__class__._identifier} Cache is set: {self._config_cache is not None}"
        )
        logger.info(
            f"Identifier: {self.__class__._identifier} Cache Timestamp: {self._cache_timestamp}"
        )

        if self._is_cache_valid():
            assert self._config_cache is not None
            return self._config_cache

        # Use lock to prevent multiple simultaneous loads
        async with self._lock:
            # Check again in case another request loaded the configs while we were waiting
            if self._is_cache_valid():
                assert self._config_cache is not None
                return self._config_cache

            # Parse the GitHub URL
            repo_url, path, branch = self.parse_github_url(github_url)
            try:
                models = await self._read_model_configs(
                    repo_url=repo_url,
                    path=path,
                    branch=branch,
                    github_token=self.github_token,
                )
                # Store in cache with timestamp
                self.__class__._config_cache = models
                self.__class__._cache_timestamp = time.time()
                logger.info(
                    f"Identifier: {self.__class__._identifier} Set Cache: {self._config_cache is not None}"
                )
                logger.info(
                    f"Identifier: {self.__class__._identifier} Set Cache Timestamp: {self._cache_timestamp}"
                )
                return models
            except Exception as e:
                logger.error(
                    f"Error reading model configurations from Github: {str(e)}"
                )
                logger.exception(e, stack_info=True)
                return []

    @classmethod
    async def _read_model_configs(
        cls, *, repo_url: str, path: str, branch: str, github_token: Optional[str]
    ) -> List[ChatModelConfig]:
        """
        Read model configurations from JSON files stored in a GitHub repository

        Args:
            repo_url: The GitHub repository URL (format: 'owner/repo')
            path: The path within the repository where config files are stored
        """
        assert repo_url
        assert path
        assert branch

        logger.info(f"Reading model configurations from GitHub: {repo_url}/{path}")
        configs: List[ChatModelConfig] = []

        async with httpx.AsyncClient() as client:
            try:
                # Construct the GitHub API URL to list contents
                api_url = f"https://api.github.com/repos/{repo_url}/contents/{path}?ref={branch}"

                headers = (
                    {"Authorization": f"token {github_token}"} if github_token else {}
                )
                # Get the list of files in the specified path
                response = await client.get(api_url, headers=headers)
                response.raise_for_status()

                # Process each file in the directory
                items = response.json()
                json_files = [
                    item
                    for item in items
                    if item["type"] == "file" and item["name"].endswith(".json")
                ]

                async def fetch_and_parse_config(
                    item: Dict[str, Any]
                ) -> Optional[ChatModelConfig]:
                    try:
                        raw_url = item["download_url"]
                        file_response = await client.get(raw_url, headers=headers)
                        file_response.raise_for_status()

                        data = file_response.json()
                        return ChatModelConfig(**data)
                    except httpx.RequestError as e:
                        print(f"Error reading file {item['name']}: {str(e)}")
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON from {item['name']}: {str(e)}")
                    except Exception as e:
                        print(f"Unexpected error processing {item['name']}: {str(e)}")
                    return None

                # Process all files concurrently
                tasks = [fetch_and_parse_config(item) for item in json_files]
                results = await asyncio.gather(*tasks)

                # Filter out None results and add valid configs to the list
                configs.extend([config for config in results if config is not None])

                return configs

            except Exception as e:
                logger.error(f"Error reading configs from GitHub: {str(e)}")
                raise

    @classmethod
    async def clear_cache(cls) -> None:
        async with cls._lock:
            cls._config_cache = None
            cls._cache_timestamp = None
