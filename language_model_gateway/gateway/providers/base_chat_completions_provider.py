from abc import abstractmethod
from typing import Dict

from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.gateway.schema.openai.completions import ChatRequest


class BaseChatCompletionsProvider:
    @abstractmethod
    async def chat_completions(
        self,
        *,
        model_config: ChatModelConfig,
        headers: Dict[str, str],
        chat_request: ChatRequest,
    ) -> StreamingResponse | JSONResponse: ...
