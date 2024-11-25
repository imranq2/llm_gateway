import json
import logging
from os import environ
from random import randint
from typing import Any, Dict

from httpx import Response
from openai.types.chat import (
    ChatCompletion,
)

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
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse:
        """
        Call the OpenAI API to get chat completions

        :param headers:
        :param chat_request:
        :return:
        """
        assert chat_request

        request_id = randint(1, 1000)
        agent_url: Optional[str] = environ["OPENAI_AGENT_URL"]
        assert agent_url
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
