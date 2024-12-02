from typing import Generator, AsyncGenerator, Optional

import httpx
import pytest
from langchain_core.messages import BaseMessage, AIMessage
from langchain_core.outputs import ChatResult, ChatGeneration
from openai import OpenAI
from starlette.testclient import TestClient

from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.api import app
from language_model_gateway.gateway.api_container import get_container_async
from language_model_gateway.gateway.models.model_factory import ModelFactory
from language_model_gateway.gateway.utilities.environment_reader import (
    EnvironmentReader,
)
from tests.gateway.mocks.mock_chat_model import MockChatModel
from tests.gateway.mocks.mock_model_factory import MockModelFactory


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

        def mock_fn_get_response(messages: list[BaseMessage]) -> ChatResult:
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content="Barack"))]
            )

        test_container.register(
            ModelFactory,
            lambda c: MockModelFactory(
                fn_get_model=lambda model_config: MockChatModel(
                    fn_get_response=mock_fn_get_response
                )
            ),
        )

    # Test health endpoint
    # response = await async_client.get("/health")
    # assert response.status_code == 200

    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=sync_client,
    )

    # call API
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "what is the first name of Obama?",
            }
        ],
        model="General Purpose",
    )

    # print the top "choice"
    content: Optional[str] = chat_completion.choices[0].message.content
    assert content is not None
    print(content)
    assert "Barack" in content


@pytest.mark.asyncio
async def test_chat_completions_with_chat_history(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    print("")

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        test_container: SimpleContainer = await get_container_async()

        def mock_fn_get_response(messages: list[BaseMessage]) -> ChatResult:
            return ChatResult(
                generations=[ChatGeneration(message=AIMessage(content="Barack"))]
            )

        test_container.register(
            ModelFactory,
            lambda c: MockModelFactory(
                fn_get_model=lambda model_config: MockChatModel(
                    fn_get_response=mock_fn_get_response
                )
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
    chat_completion = client.chat.completions.create(
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
    )

    # print the top "choice"
    print("========  Response ======")
    print(chat_completion)
    print("====== End of Response ======")
    content: Optional[str] = chat_completion.choices[0].message.content
    assert content is not None
    print(content)
    assert "Barack" in content
