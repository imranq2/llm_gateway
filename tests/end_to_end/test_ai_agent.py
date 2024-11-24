import json
from typing import Any, Dict

import pytest
from os import environ

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.managers.chat_completions_manager import (
    ChatCompletionsManager,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


@pytest.mark.asyncio
async def test_call_agent_with_input() -> None:
    print("")
    # Create a ChatRequest object
    request = ChatRequest(model="test-model", messages=[])

    manager = ChatCompletionsManager()
    response: StreamingResponse | JSONResponse = await manager.call_agent_with_input(
        chat_history=[msg for msg in request["messages"]],
        input_text="Have I taken covid vaccine?",
        model="test-model",
        agent_url=environ["AGENT_URL"],
        patient_id=environ["DEFAULT_PATIENT_ID"],
        stream_request=False,
        request_id="test-request-id",
    )

    assert response.status_code == 200
    assert isinstance(response, JSONResponse)
    response_json: str = response.body.decode("utf-8")  # type: ignore[union-attr]
    response_dict: Dict[str, Any] = json.loads(response_json)
    assert "choices" in response_dict
    assert len(response_dict["choices"]) > 0
    assert response_dict["choices"][0]["message"]["content"] is not None
