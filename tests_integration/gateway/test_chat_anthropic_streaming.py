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
async def test_chat_completions(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:

    # Test health endpoint
    response = await async_client.get("/health")
    assert response.status_code == 200

    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=sync_client,
    )

    # call API
    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "what is the first name of Obama?",
            }
        ],
        model="SimpleAnthropic",
        stream=True,
    )
    content: str = ""
    i: int = 0
    for chunk in stream:
        i += 1
        print(f"======== Chunk {i} ========")
        delta_content = chunk.choices[0].delta.content
        content += delta_content or ""
        print(delta_content or "")
        print(f"====== End of Chunk {i} ======")

    print("======== Final Content ========")
    print(content)
    print("====== End of Final Content ======")
    assert "Barack" in content


@pytest.mark.asyncio
async def test_chat_completions_with_chat_history(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    print("")
    # Test health endpoint
    response = await async_client.get("/health")
    assert response.status_code == 200

    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=sync_client,
    )

    # call API
    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Who was the 44th president of United States? ",
            },
            {"role": "assistant", "content": "Barack Obama"},
            {
                "role": "user",
                "content": "what is his first name?",
            },
        ],
        model="SimpleAnthropic",
        stream=True,
    )
    content: str = ""
    i: int = 0
    for chunk in stream:
        i += 1
        print(f"======== Chunk {i} ========")
        delta_content = chunk.choices[0].delta.content
        content += delta_content or ""
        print(delta_content or "")
        print(f"====== End of Chunk {i} ======")

    print("======== Final Content ========")
    print(content)
    print("====== End of Final Content ======")
    assert "Barack" in content
