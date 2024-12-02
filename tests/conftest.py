from typing import Generator, AsyncGenerator

import httpx
import pytest
from starlette.testclient import TestClient

from language_model_gateway.gateway.api import app


@pytest.fixture
async def async_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://test"
    ) as client:
        yield client


# If you need a sync client for OpenAI
@pytest.fixture
def sync_client() -> Generator[httpx.Client, None, None]:
    with TestClient(app) as client:
        yield client
