import logging
import os
import traceback
from contextlib import asynccontextmanager
from datetime import datetime
from functools import wraps
from typing import Any, Dict, cast, List, TypedDict, Callable, Awaitable
from typing import AsyncGenerator, Annotated

from fastapi import FastAPI, APIRouter, Depends, HTTPException
from starlette.responses import StreamingResponse, JSONResponse
from typing_extensions import ParamSpec, TypeVar
from starlette.requests import Request
from language_model_gateway.container.container_creator import ContainerCreator
from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.schema.openai.completions import ChatRequest

# warnings.filterwarnings("ignore", category=LangChainBetaWarning)

logger = logging.getLogger(__name__)

# Dependencies
P = ParamSpec("P")
R = TypeVar("R")


def cached(f: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
    cache: R | None = None

    @wraps(f)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        nonlocal cache

        if cache is not None:
            return cache

        cache = await f(*args, **kwargs)
        return cache

    return wrapper


@cached  # makes it singleton-like
async def get_container() -> SimpleContainer:
    return await ContainerCreator().create_container_async()


def get_chat_manager(
    container: Annotated[SimpleContainer, Depends(get_container)]
) -> ChatCompletionManager:
    assert isinstance(container, SimpleContainer), type(container)
    return container.resolve(ChatCompletionManager)


def get_model_manager(
    container: Annotated[SimpleContainer, Depends(get_container)]
) -> ModelManager:
    assert isinstance(container, SimpleContainer), type(container)
    return container.resolve(ModelManager)


# Create routers with dependencies
router = APIRouter()


@router.get("/health")
async def health() -> str:
    return "OK"


class ErrorDetail(TypedDict):
    message: str
    timestamp: str
    trace_id: str
    call_stack: str


@router.post("/api/v1/chat/completions", response_model=None)
async def chat_completions(
    request: Request,
    chat_request: Dict[str, Any],
    chat_manager: Annotated[ChatCompletionManager, Depends(get_chat_manager)],
) -> StreamingResponse | JSONResponse:
    assert chat_request
    assert chat_manager
    try:
        return await chat_manager.chat_completions(
            headers={k: v for k, v in request.headers.items()},  # Add headers if needed
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
        logger.error(f"Validation error: {e}\n{call_stack}")
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
        logger.error(f"Unexpected error: {e}\n{call_stack}")
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/api/v1/models")
async def get_models(
    request: Request, model_manager: Annotated[ModelManager, Depends(get_model_manager)]
) -> Dict[str, List[Dict[str, str]]]:
    return await model_manager.get_models()


@asynccontextmanager
async def lifespan(app1: FastAPI) -> AsyncGenerator[None, None]:
    try:
        # Configure logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger.info("Starting application initialization...")

        # Initialize container
        # await container.initialize()

        logger.info("Application initialization completed")
        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    finally:
        try:
            logger.info("Starting application shutdown...")
            # await container.cleanup()
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise


# Create the FastAPI app instance
app = FastAPI(title="OpenAI-compatible API", lifespan=lifespan)

# Include router
app.include_router(router)
