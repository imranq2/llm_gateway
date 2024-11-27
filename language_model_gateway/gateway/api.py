import logging
import os
import traceback
from inspect import stack
from typing import Dict, Any, cast, TypedDict
from typing import List
from datetime import datetime

from fastapi import FastAPI, HTTPException
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.schema.openai.completions import ChatRequest

# Get log level from environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Set up basic configuration for logging
logging.basicConfig(level=getattr(logging, log_level))

# warnings.filterwarnings("ignore", category=LangChainBetaWarning)
logger = logging.getLogger(__name__)

app = FastAPI(title="OpenAI-compatible API")


@app.get("/health")
def health() -> str:
    return "OK"


class ErrorDetail(TypedDict):
    message: str
    timestamp: str
    trace_id: str
    call_stack: str


@app.post("/api/v1/chat/completions", response_model=None)
async def chat_completions(
    request: Request,
    chat_request: Dict[str, Any],
) -> StreamingResponse | JSONResponse:
    try:
        return await ChatCompletionManager().chat_completions(
            headers={k: v for k, v in request.headers.items()},
            chat_request=cast(ChatRequest, chat_request),
        )
    except* ConnectionError as e:
        call_stack = traceback.format_exc()
        error_detail: ErrorDetail = {
            "message": "Service connection error",
            "timestamp": datetime.now().isoformat(),
            "trace_id": "",
            # "trace_id": request.trace_id if hasattr(request, "trace_id") else "",
            "call_stack": call_stack,
        }
        logger.error(f"Connection error: {e}\n{call_stack}")
        raise HTTPException(status_code=503, detail=error_detail)
    except* ValueError as e:
        call_stack = traceback.format_exc()
        error_detail = {
            "message": str(e),
            "timestamp": datetime.now().isoformat(),
            "trace_id": "",
            # "trace_id": request.trace_id if hasattr(request, "trace_id") else "",
            "call_stack": call_stack,
        }
        logger.error(f"Validation error: {e}\n{stack}")
        raise HTTPException(status_code=400, detail=error_detail)
    except* Exception as e:
        call_stack = traceback.format_exc()
        error_detail = {
            "message": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            # "trace_id": request.trace_id if hasattr(request, "trace_id") else "",
            "trace_id": "",
            "call_stack": call_stack,
        }
        logger.error(f"Unexpected error: {e}\n{stack}")
        raise HTTPException(status_code=500, detail=error_detail)


@app.get("/api/v1/models")
async def get_models() -> Dict[str, List[Dict[str, str]]]:
    return await ModelManager.get_models()
