from typing import Optional, List

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice

from language_model_gateway.configs.config_schema import (
    ChatModelConfig,
    ModelConfig,
    ToolConfig,
)
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.api_container import get_container_async
from language_model_gateway.gateway.utilities.expiring_cache import ExpiringCache


async def test_chat_network_topology_diagram_generator(
    async_client: httpx.AsyncClient,
) -> None:
    print("")
    test_container: SimpleContainer = await get_container_async()

    # if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
    #     test_container.register(
    #         ModelFactory,
    #         lambda c: MockModelFactory(
    #             fn_get_model=lambda chat_model_config: MockChatModel(
    #                 fn_get_response=lambda messages: "http://localhost:5050/image_generation/"
    #             )
    #         ),
    #     )
    #     test_container.register(
    #         ImageGeneratorFactory,
    #         lambda c: MockImageGeneratorFactory(image_generator=MockImageGenerator()),
    #     )

    # set the model configuration for this test
    model_configuration_cache: ExpiringCache[List[ChatModelConfig]] = (
        test_container.resolve(ExpiringCache)
    )
    await model_configuration_cache.set(
        [
            ChatModelConfig(
                id="general_purpose",
                name="General Purpose",
                description="General Purpose Language Model",
                type="langchain",
                model=ModelConfig(
                    provider="bedrock",
                    model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
                ),
                tools=[
                    ToolConfig(name="network_topology_generator"),
                ],
            )
        ]
    )

    # Test health endpoint
    # response = await async_client.get("/health")
    # assert response.status_code == 200

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
                "content": """
Create a network topology diagram with the following specifications:

Instructions:
- Specify nodes (network components) with their types
- Define connections between nodes
- Optional: Add labels to connections
- Optional: Customize node styles

Node Types:
- cloud: Represents internet or external network
- router: Network routing device
- switch: Network switch
- server: Server or computer
- firewall: Security device

Styling Options:
- shape: cloud, router, switch, server, firewall
- color: lightblue, lightgreen, lightgray, lightcoral, etc.

Example Format:
```json
{
    "nodes": {
        "Internet": {"style": {"shape": "cloud", "color": "lightgray"}},
        "Firewall": {"style": {"shape": "firewall", "color": "lightcoral"}},
        "Router": {"style": {"shape": "router", "color": "lightblue"}},
        "Switch1": {"style": {"shape": "switch", "color": "lightgreen"}},
        "Server1": {"style": {"shape": "server", "color": "lightpink"}}
    },
    "connections": [
        {"from": "Internet", "to": "Firewall", "label": "WAN"},
        {"from": "Firewall", "to": "Router", "label": "Secured"},
        {"from": "Router", "to": "Switch1", "label": "LAN"},
        {"from": "Switch1", "to": "Server1", "label": "eth0"}
    ],
    "title": "Simple Corporate Network"
}
""",
            }
        ],
        model="General Purpose",
    )

    print(chat_completion)

    # print the top "choice"
    choices: List[Choice] = chat_completion.choices
    print(choices)
    content: Optional[str] = ",".join(
        [choice.message.content or "" for choice in choices]
    )
    assert content is not None
    print(content)
    assert "http://localhost:5050/image_generation/" in content
    # assert "data:image/png;base64" in content
