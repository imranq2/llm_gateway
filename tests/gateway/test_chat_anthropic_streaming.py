from typing import Generator, AsyncGenerator, Dict, Any

import httpx
import pytest
from openai import OpenAI
from starlette.testclient import TestClient

from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.api import app
from language_model_gateway.gateway.api_container import get_container_async
from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest
from language_model_gateway.gateway.utilities.environment_reader import (
    EnvironmentReader,
)
from tests.gateway.mocks.mock_langchain_completions_provider import (
    MockLangChainChatCompletionsProvider,
)


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
    print("")

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        test_container: SimpleContainer = await get_container_async()

        def mock_fn_get_response(
            model_config: ChatModelConfig,
            headers: Dict[str, str],
            chat_request: ChatRequest,
        ) -> Dict[str, Any]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Barack",
                            "role": "assistant",
                        }
                    }
                ]
            }

        test_container.register(
            LangChainCompletionsProvider,
            lambda c: MockLangChainChatCompletionsProvider(
                fn_get_response=mock_fn_get_response
            ),
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
    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "what is the first name of Obama?",
            }
        ],
        model="General Purpose",
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

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        test_container: SimpleContainer = await get_container_async()

        def mock_fn_get_response(
            model_config: ChatModelConfig,
            headers: Dict[str, str],
            chat_request: ChatRequest,
        ) -> Dict[str, Any]:
            return {
                "choices": [
                    {
                        "message": {
                            "content": "Barack",
                            "role": "assistant",
                        }
                    }
                ]
            }

        test_container.register(
            LangChainCompletionsProvider,
            lambda c: MockLangChainChatCompletionsProvider(
                fn_get_response=mock_fn_get_response
            ),
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
        model="General Purpose",
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
