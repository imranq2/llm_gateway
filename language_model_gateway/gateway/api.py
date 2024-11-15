import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, AsyncGenerator
from typing import List, Optional

from fastapi import FastAPI
from pydantic import BaseModel
from starlette.responses import StreamingResponse

logging.basicConfig(level=logging.INFO)

# Based on https://towardsdatascience.com/how-to-build-an-openai-compatible-api-87c8edea2f06


class ChatMessage(BaseModel):
    role: str
    content: str

    def to_dict(self) -> Dict[str, str]:
        return self.model_dump()


class ChatCompletionRequest(BaseModel):
    model: str = "mock-gpt-model"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False


app = FastAPI(title="OpenAI-compatible API")


@app.get("/health")
def health() -> str:
    return "OK"


@app.post("/api/v1/chat/completions_sync")
async def chat_completions_sync(request: ChatCompletionRequest) -> Dict[str, Any]:
    if request.messages and request.messages[0].role == "user":
        resp_content = (
            "As a mock AI Assistant, I can only echo your last message:"
            + request.messages[-1].content
        )
    else:
        resp_content = "As a mock AI Assistant, I can only echo your last message, but there were no messages!"

    return {
        "id": "1337",
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [{"message": ChatMessage(role="assistant", content=resp_content)}],
    }


async def _resp_async_generator(text_resp: str) -> AsyncGenerator[str, None]:
    # let's pretend every word is a token and return it over time
    tokens = text_resp.split(" ")

    for i, token in enumerate(tokens):
        chunk = {
            "id": i,
            "object": "chat.completion.chunk",
            "created": time.time(),
            "model": "blah",
            "choices": [{"delta": {"content": token + " "}}],
        }
        yield f"data: {json.dumps(chunk)}\n\n"
        await asyncio.sleep(1)
    yield "data: [DONE]\n\n"


@app.post("/api/v1/chat/completions", response_model=None)
async def chat_completions(
    request: ChatCompletionRequest,
) -> StreamingResponse | Dict[str, Any]:
    logger = logging.getLogger(__name__)
    request_id = random.randint(1, 1000)
    logger.info(f"Received request {request_id}: {request}")
    if request.messages:
        resp_content = (
            "As a mock AI Assistant, I can only echo your last message:"
            + request.messages[-1].content
        )
    else:
        resp_content = "As a mock AI Assistant, I can only echo your last message, but there wasn't one!"
    if request.stream:
        logger.info(f"Streaming response {request_id}")
        return StreamingResponse(
            _resp_async_generator(resp_content), media_type="application/x-ndjson"
        )

    response_dict = {
        "id": "1337",
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [
            {"message": ChatMessage(role="assistant", content=resp_content).to_dict()}
        ],
    }
    logger.info(f"Non-streaming response {request_id}: {response_dict}")

    return response_dict


# Mock list of models
models = [
    {"id": "text-davinci-003", "description": "Highly capable language model"},
    {"id": "text-curie-001", "description": "Less capable than Davinci, faster"},
    {"id": "text-babbage-001", "description": "Basic capability, faster"},
    {"id": "text-ada-001", "description": "Simplest and fastest model"},
]


@app.get("/api/v1/models")
async def get_models() -> Dict[str, List[Dict[str, str]]]:
    logger = logging.getLogger(__name__)
    logger.info("Received request for models")
    return {"data": models}
