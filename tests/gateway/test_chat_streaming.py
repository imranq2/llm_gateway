import httpx
import pytest
from openai import OpenAI


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
        model="b.well PHR",
        messages=[{"role": "user", "content": "Say this is a test"}],
        stream=True,
    )
    for chunk in stream:
        print(chunk.choices[0].delta.content or "")
