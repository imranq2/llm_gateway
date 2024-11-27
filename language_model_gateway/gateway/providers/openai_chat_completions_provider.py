import json
import logging
from os import environ
from random import randint
from typing import Any, Dict, AsyncGenerator

from httpx import Response
from httpx_sse import aconnect_sse, ServerSentEvent
from openai.types.chat import (
    ChatCompletion,
)

from language_model_gateway.configs.config_schema import ChatModelConfig

logger = logging.getLogger(__file__)
from typing import Optional

import httpx
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.providers.base_chat_completions_provider import (
    BaseChatCompletionsProvider,
)
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


class OpenAiChatCompletionsProvider(BaseChatCompletionsProvider):
    async def chat_completions(
        self,
        *,
        model_config: ChatModelConfig,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        """
        Call the OpenAI API to get chat completions

        :param headers:
        :param chat_request:
        :param model_config:
        :return:
        """
        assert chat_request

        request_id: str = str(randint(1, 1000))
        agent_url: Optional[str] = environ["OPENAI_AGENT_URL"]
        assert agent_url

        if chat_request.get("stream"):
            return StreamingResponse(
                await self.get_streaming_response_async(
                    agent_url=agent_url,
                    request_id=request_id,
                    headers=headers,
                    chat_request=chat_request,
                ),
                media_type="text/event-stream",
            )

        async with httpx.AsyncClient(base_url=agent_url) as client:
            try:
                agent_response: Response = await client.post(
                    "/chat/completions",
                    json=chat_request,
                    timeout=60 * 60,
                    headers=headers,
                )

                response_text: str = agent_response.text
                response_dict: Dict[str, Any] = agent_response.json()
            except json.JSONDecodeError:
                return JSONResponse(content="Error decoding response", status_code=500)
            except Exception as e:
                return JSONResponse(content=f"Error from agent: {e}", status_code=500)

            response: ChatCompletion = ChatCompletion.parse_obj(response_dict)
            logger.info(f"Non-streaming response {request_id}: {response}")
            return JSONResponse(content=response.model_dump())

    async def get_streaming_response_async(
        self,
        *,
        agent_url: str,
        request_id: str,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        logger.info(f"Streaming response {request_id} from agent")
        generator: AsyncGenerator[str, None] = self._stream_resp_async_generator(
            agent_url=agent_url,
            request_id=request_id,
            chat_request=chat_request,
            headers=headers,
        )
        return generator

    @staticmethod
    async def _stream_resp_async_generator(
        *,
        request_id: str,
        agent_url: str,
        chat_request: ChatRequest,
        headers: Dict[str, str],
    ) -> AsyncGenerator[str, None]:

        logger.info(f"Streaming response {request_id} from agent")
        async with httpx.AsyncClient(base_url=agent_url) as client:
            async with aconnect_sse(
                client,
                "POST",
                "/chat/completions",
                json=chat_request,
                timeout=60 * 60,
                headers=headers,
            ) as event_source:
                i = 0
                sse: ServerSentEvent
                async for sse in event_source.aiter_sse():
                    event: str = sse.event
                    data: str = sse.data
                    i += 1

                    if logger.isEnabledFor(logging.DEBUG):
                        logger.debug(
                            f"----- Received data from stream {i} {event} {type(data)} ------"
                        )
                        logger.debug(data)
                        logger.debug(
                            f"----- End data from stream {i} {event} {type(data)} ------"
                        )
                    yield f"data: {data}\n\n"
