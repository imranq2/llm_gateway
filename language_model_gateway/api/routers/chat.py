from typing import Annotated

from fastapi import APIRouter, Depends, Body
from fastapi.responses import StreamingResponse

from language_model_gateway.api.auth import api_key_auth
from language_model_gateway.api.models.bedrock import BedrockModel
from language_model_gateway.api.schema import (
    ChatRequest,
    ChatResponse,
    ChatStreamResponse,
)
from language_model_gateway.api.setting import DEFAULT_MODEL

router = APIRouter(
    prefix="/chat",
    dependencies=[Depends(api_key_auth)],
    # responses={404: {"description": "Not found"}},
)


@router.post(
    "/completions",
    response_model=ChatResponse | ChatStreamResponse,
    response_model_exclude_unset=True,
)
async def chat_completions(
    chat_request: Annotated[
        ChatRequest,
        Body(
            examples=[
                {
                    "model": "anthropic.claude-3-sonnet-20240229-v1:0",
                    "messages": [
                        {"role": "system", "content": "You are a helpful assistant."},
                        {"role": "user", "content": "Hello!"},
                    ],
                }
            ],
        ),
    ]
) -> ChatResponse | StreamingResponse:
    if chat_request.model.lower().startswith("gpt-"):
        chat_request.model = DEFAULT_MODEL

    # Exception will be raised if model not supported.
    model = BedrockModel()
    model.validate(chat_request)
    if chat_request.stream:
        return StreamingResponse(
            content=iter(model.chat_stream(chat_request)),  # type: ignore[arg-type]
            media_type="text/event-stream",
        )
    return model.chat(chat_request)
