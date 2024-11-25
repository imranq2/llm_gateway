from abc import abstractmethod
from typing import Dict

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.schema.openai.completions import ChatRequest


class BaseChatCompletionsProvider:
    @abstractmethod
    async def chat_completions(
        self,
        *,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse: ...
