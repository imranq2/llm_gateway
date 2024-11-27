from typing import Generator, AsyncGenerator

import httpx
import pytest
from openai import OpenAI
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


@pytest.mark.asyncio
async def test_chat_completions_streaming(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    # init client and connect to localhost server
    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=sync_client,
    )

    stream = client.chat.completions.create(
        model="b.well",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )
    for chunk in stream:
        print(chunk.choices[0].delta.content or "")
