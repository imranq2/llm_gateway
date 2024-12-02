from typing import Generator, AsyncGenerator, Optional, Dict, Any

import httpx
import pytest
from openai import OpenAI
from starlette.responses import StreamingResponse, JSONResponse
from starlette.testclient import TestClient

from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.api import app
from language_model_gateway.gateway.api_container import get_container_async
from language_model_gateway.gateway.providers.langchain_chat_completions_provider import (
    LangChainCompletionsProvider,
)
from language_model_gateway.gateway.providers.openai_chat_completions_provider import (
    OpenAiChatCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


# @pytest.fixture
# def app() -> Generator[FastAPI, None, None]:
#     app = create_app()
#     yield app


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


class MockOpenAiChatCompletionsProvider(OpenAiChatCompletionsProvider):
    async def chat_completions(
        self,
        *,
        model_config: ChatModelConfig,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        result: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "content": "Barack",
                        "role": "assistant",
                    }
                }
            ]
        }
        return JSONResponse(content=result)


class MockLangChainChatCompletionsProvider(LangChainCompletionsProvider):
    async def chat_completions(
        self,
        *,
        model_config: ChatModelConfig,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        result: Dict[str, Any] = {
            "choices": [
                {
                    "message": {
                        "content": "Barack",
                        "role": "assistant",
                    }
                }
            ]
        }
        return JSONResponse(content=result)


@pytest.mark.asyncio
async def test_chat_completions(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    print("")

    test_container: SimpleContainer = await get_container_async()
    # test_container.register(
    #     OpenAiChatCompletionsProvider, lambda c: MockOpenAiChatCompletionsProvider()
    # )
    test_container.register(
        LangChainCompletionsProvider, lambda c: MockLangChainChatCompletionsProvider()
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

    test_container: SimpleContainer = await get_container_async()
    # test_container.register(
    #     OpenAiChatCompletionsProvider, lambda c: MockOpenAiChatCompletionsProvider()
    # )
    test_container.register(
        LangChainCompletionsProvider, lambda c: MockLangChainChatCompletionsProvider()
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
