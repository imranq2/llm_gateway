import httpx
import pytest
from openai import OpenAI


@pytest.mark.asyncio
async def test_chat_anthropic_image_generation(
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
    response = client.images.generate(
        model="dall-e-3",
        prompt="a white siamese cat",
        size="1024x1024",
        quality="standard",
        n=1,
    )

    image_url = response.data[0].url
    print(f"Image URL: {image_url}")
    assert image_url is not None
    assert "http" in image_url
