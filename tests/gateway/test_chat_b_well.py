import httpx
import pytest
from openai import OpenAI
from openai.types.chat import ChatCompletion
from pytest_httpx import HTTPXMock

from language_model_gateway.gateway.utilities.environment_reader import (
    EnvironmentReader,
)


@pytest.mark.httpx_mock(
    should_mock=lambda request: request.url.host == "host.docker.internal"
)
async def test_chat_completions_b_well(
    async_client: httpx.AsyncClient, sync_client: httpx.Client, httpx_mock: HTTPXMock
) -> None:

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        httpx_mock.add_response(
            url="http://host.docker.internal:5055/api/v1/chat/completions",
            json={
                "id": "chat_1",
                "object": "chat.completion",
                "created": 1633660000,
                "model": "b.well PHR",
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "content": "Barack",
                            "role": "assistant",
                        },
                    }
                ],
            },
        )

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
    chat_completion: ChatCompletion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="b.well PHR",
    )

    # print the top "choice"
    print(chat_completion.choices[0].message.content)
