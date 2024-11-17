import logging
from typing import Dict
from typing import List

from fastapi import FastAPI
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.managers.chat_completions_manager import (
    ChatCompletionsManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.schema import (
    ChatRequest,
)

logging.basicConfig(level=logging.INFO)

# Based on https://towardsdatascience.com/how-to-build-an-openai-compatible-api-87c8edea2f06


app = FastAPI(title="OpenAI-compatible API")


@app.get("/health")
def health() -> str:
    return "OK"


@app.post("/api/v1/chat/completions", response_model=None)
async def chat_completions(
    request: ChatRequest,
) -> StreamingResponse | JSONResponse:
    return await ChatCompletionsManager().chat_completions(request=request)


@app.get("/api/v1/models")
async def get_models() -> Dict[str, List[Dict[str, str]]]:
    return await ModelManager.get_models()
