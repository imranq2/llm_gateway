from typing import Optional

import httpx
import pytest
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion


@pytest.mark.asyncio
async def test_chat_completions_with_web_search(
    async_client: httpx.AsyncClient,
) -> None:

    # if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
    #     test_container: SimpleContainer = await get_container_async()
    #     test_container.register(
    #         ModelFactory,
    #         lambda c: MockModelFactory(
    #             fn_get_model=lambda chat_model_config: MockChatModel(
    #                 fn_get_response=lambda messages: "Donald Trump won the last US election"
    #             )
    #         ),
    #     )

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=async_client,
    )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Who won the last US election?",
            }
        ],
        model="Google Search",
    )

    # print the top "choice"
    content: Optional[str] = "\n".join(
        choice.message.content or "" for choice in chat_completion.choices
    )
    assert content is not None
    print(content)
    assert "Trump" in content
