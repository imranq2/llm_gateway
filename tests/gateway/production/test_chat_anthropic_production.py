import os
from typing import Optional

import httpx
import pytest
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


@pytest.mark.skipif(
    os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
    reason="hits production API",
)
async def test_chat_completions_production(async_client: httpx.AsyncClient) -> None:
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.dev.bwell.zone/api/v1",
        http_client=async_client,
    )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Get the address of Dr. Meggin A. Sabatino at Medstar",
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
