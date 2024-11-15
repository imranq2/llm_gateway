from typing import Generator

import httpx
import pytest
from openai import OpenAI

from language_model_gateway.gateway.api import app


@pytest.fixture
def httpx_client() -> Generator[httpx.Client, None, None]:
    with httpx.Client(app=app, base_url="http://localhost") as client:
        yield client


@pytest.mark.asyncio
async def test_chat_completions(httpx_client: httpx.Client) -> None:

    # get /health url
    response = httpx_client.get("/health")
    assert response.status_code == 200
    assert response.text == "OK"

    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000",  # change the default port if needed
        http_client=httpx_client,
    )

    # call API
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-1337-turbo-pro-max",
    )

    # print the top "choice"
    print(chat_completion.choices[0].message.content)
