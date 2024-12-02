import httpx
import pytest
from openai import OpenAI
from openai.pagination import SyncPage
from openai.types import Model


@pytest.mark.asyncio
async def test_models(
    async_client: httpx.AsyncClient, sync_client: httpx.Client
) -> None:
    # init client and connect to localhost server
    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000/api/v1",  # change the default port if needed
        http_client=sync_client,
    )
    models: SyncPage[Model] = client.models.list()
    print(models.model_dump_json())
    assert models
    for model in models:
        print(model.id)
        assert model.id
