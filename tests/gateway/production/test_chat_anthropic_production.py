import os
from typing import Optional

import pytest
from openai import AsyncOpenAI, AsyncStream
from openai.types.chat import ChatCompletion, ChatCompletionChunk


@pytest.mark.skipif(
    os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
    reason="hits production API",
)
async def test_chat_completions_production(
    # async_client: httpx.AsyncClient
) -> None:
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        # http_client=async_client,
    )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Get the address of Vanessa Paz NP at One Medical.",
            }
        ],
        model="General Purpose",
    )

    # print the top "choice"
    content: Optional[str] = "\n".join(
        choice.message.content or "" for choice in chat_completion.choices
    )

    assert content is not None
    print(content)
    # assert "Barack" in content


@pytest.mark.skipif(
    os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
    reason="hits production API",
)
async def test_chat_completions_streaming_production(
    # async_client: httpx.AsyncClient,
) -> None:
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        # http_client=async_client,
    )

    # call API
    stream: AsyncStream[ChatCompletionChunk] = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Get the address of Vanessa Paz NP at One Medical.",
            }
        ],
        model="General Purpose",
        stream=True,
    )

    # print the top "choice"
    content: Optional[str] = None
    chunk: ChatCompletionChunk
    async for chunk in stream:
        delta_content = "\n".join(
            [choice.delta.content or "" for choice in chunk.choices]
        )
        print("======= Chunk =======")
        print(delta_content)
        print("======= End of Chunk =======")
        content = content + delta_content if content else delta_content

    assert content is not None
    print(content)
    # assert "Barack" in content
