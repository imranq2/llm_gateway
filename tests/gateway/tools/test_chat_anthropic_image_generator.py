from typing import Optional, List

import httpx
import pytest
from openai import OpenAI
from openai.types.chat.chat_completion import Choice


@pytest.mark.asyncio
async def test_chat_completions(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    print("")

    # if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
    #     test_container: SimpleContainer = await get_container_async()
    #     test_container.register(
    #         ModelFactory,
    #         lambda c: MockModelFactory(
    #             fn_get_model=lambda chat_model_config: MockChatModel(
    #                 fn_get_response=lambda messages: "Barack"
    #             )
    #         ),
    #     )

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
                "content": "Generate an image depicting a neural network",
            }
        ],
        model="General Purpose",
    )

    # print the top "choice"
    choices: List[Choice] = chat_completion.choices
    content: Optional[str] = choices[1].message.content
    assert content is not None
    print(content)
    assert "http://dev:5000/image_generation/" in content
