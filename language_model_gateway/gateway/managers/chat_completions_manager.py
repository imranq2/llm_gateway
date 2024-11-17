import asyncio
import json
import logging
import random
import time
from typing import AsyncGenerator, cast

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.schema import (
    ChatResponseMessage,
    ChatResponse,
    Choice,
    Usage,
    ChoiceDelta,
    ChatStreamResponse,
    UserMessage,
    ChatRequest,
)


class ChatCompletionsManager:

    @staticmethod
    async def _resp_async_generator(text_resp: str) -> AsyncGenerator[str, None]:
        # let's pretend every word is a token and return it over time
        tokens = text_resp.split(" ")

        for i, token in enumerate(tokens):
            chunk: ChatStreamResponse = ChatStreamResponse(
                id=str(i),
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

    @staticmethod
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
                ChatCompletionsManager._resp_async_generator(resp_content),
                media_type="text/event-stream",
            )
        response_dict: ChatResponse = ChatResponse(
            id="1337",
            created=int(time.time()),
            model=request.model,
            choices=[
                Choice(
                    message=ChatResponseMessage(role="assistant", content=resp_content)
                )
            ],
            usage=Usage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
        )
        logger.info(f"Non-streaming response {request_id}: {response_dict}")
        return JSONResponse(content=response_dict.model_dump())
