import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, AsyncGenerator, cast
from typing import List

from fastapi import FastAPI
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.schema import (
    ChatResponseMessage,
    ChatRequest,
    ChatResponse,
    Choice,
    Usage,
    ChoiceDelta,
    ChatStreamResponse,
    UserMessage,
)

logging.basicConfig(level=logging.INFO)

# Based on https://towardsdatascience.com/how-to-build-an-openai-compatible-api-87c8edea2f06


app = FastAPI(title="OpenAI-compatible API")


@app.get("/health")
def health() -> str:
    return "OK"


@app.post("/api/v1/chat/completions_sync")
async def chat_completions_sync(request: ChatRequest) -> Dict[str, Any]:
    resp_content: str
    if request.messages and request.messages[0].role == "user":
        resp_content = cast(str, cast(UserMessage, request.messages[-1]).content)
    else:
        resp_content = "As a mock AI Assistant, I can only echo your last message, but there were no messages!"

    return {
        "id": "1337",
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [
            {"message": ChatResponseMessage(role="assistant", content=resp_content)}
        ],
    }


async def _resp_async_generator(text_resp: str) -> AsyncGenerator[str, None]:
    # let's pretend every word is a token and return it over time
    tokens = text_resp.split(" ")

    for i, token in enumerate(tokens):
        chunk: ChatStreamResponse = ChatStreamResponse(
            id=str(i),
            object="chat.completion.chunk",
            created=int(time.time()),
            model="blah",
            choices=[
                ChoiceDelta(
                    delta=ChatResponseMessage(role="assistant", content=token + " ")
                )
            ],
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )
        yield f"data: {json.dumps(chunk.model_dump())}\n\n"
        await asyncio.sleep(1)
    yield "data: [DONE]\n\n"


@app.post("/api/v1/chat/completions", response_model=None)
async def chat_completions(
    request: ChatRequest,
) -> StreamingResponse | JSONResponse:
    logger = logging.getLogger(__name__)
    request_id = random.randint(1, 1000)
    logger.info(f"Received request {request_id}: {request}")

    response_context: str
    if request.messages:
        resp_content = cast(str, cast(UserMessage, request.messages[-1]).content)
    else:
        resp_content = "As a mock AI Assistant, I can only echo your last message, but there wasn't one!"
    if request.stream:
        logger.info(f"Streaming response {request_id}")
        return StreamingResponse(
            _resp_async_generator(resp_content), media_type="application/x-ndjson"
        )

    response_dict: ChatResponse = ChatResponse(
        id="1337",
        object="chat.completion",
        created=int(time.time()),
        model=request.model,
        choices=[
            Choice(message=ChatResponseMessage(role="assistant", content=resp_content))
        ],
        usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
    )
    logger.info(f"Non-streaming response {request_id}: {response_dict}")

    return JSONResponse(content=response_dict.model_dump())


# Mock list of models
models = [
    {"id": "search-web", "description": "Highly capable language model"},
]


@app.get("/api/v1/models")
async def get_models() -> Dict[str, List[Dict[str, str]]]:
    logger = logging.getLogger(__name__)
    logger.info("Received request for models")
    return {"data": models}
