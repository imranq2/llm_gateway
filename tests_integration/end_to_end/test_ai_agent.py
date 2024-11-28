import json
from typing import Any, Dict, List

import pytest

from openai.types.chat import ChatCompletionMessageParam, ChatCompletionUserMessageParam
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.configs.config_schema import ChatModelConfig, ModelChoice
from language_model_gateway.gateway.providers.openai_chat_completions_provider import (
    OpenAiChatCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


@pytest.mark.asyncio
async def test_call_agent_with_input() -> None:
    print("")

    chat_history: List[ChatCompletionMessageParam] = []
    user_message: ChatCompletionMessageParam = ChatCompletionUserMessageParam(
        role="user",
        content="Have I taken covid vaccine?",
    )
    # Create a ChatRequest object
    request = ChatRequest(
        model="test-model",
        messages=chat_history + [user_message],
    )

    provider = OpenAiChatCompletionsProvider()
    response: StreamingResponse | JSONResponse = await provider.chat_completions(
        headers={},
        chat_request=request,
        model_config=ChatModelConfig(
            id="1",
            name="test-model",
            description="test model",
            type="chat",
            model=ModelChoice(
                provider="openai",
                model="gpt-3.5-turbo",
            ),
            url="http://localhost:5000",
        ),
    )

    assert response.status_code == 200
    assert isinstance(response, JSONResponse)
    response_json: str = response.body.decode("utf-8")  # type: ignore[union-attr]
    response_dict: Dict[str, Any] = json.loads(response_json)
    assert "choices" in response_dict
    assert len(response_dict["choices"]) > 0
    assert response_dict["choices"][0]["message"]["content"] is not None
