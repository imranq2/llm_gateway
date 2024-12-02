from contextlib import asynccontextmanager
from typing import AsyncGenerator

import httpx


class HttpClientFactory:
    # noinspection PyMethodMayBeStatic
    @asynccontextmanager
    async def create_http_client(
        self, base_url: str
    ) -> AsyncGenerator[httpx.AsyncClient, None]:
        async with httpx.AsyncClient(base_url=base_url) as client:
            yield client
