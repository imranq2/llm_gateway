# language_model_gateway/gateway/api.py
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any, cast, List
from fastapi import FastAPI, APIRouter
from starlette.requests import Request
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.managers.chat_completion_manager import (
    ChatCompletionManager,
)
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.schema.openai.completions import ChatRequest

logger = logging.getLogger(__name__)


def create_chat_router(chat_manager: ChatCompletionManager) -> APIRouter:
    router = APIRouter()

    async def chat_completions_handler(
        request: Request, chat_request: Dict[str, Any]
    ) -> StreamingResponse | JSONResponse:
        try:
            return await chat_manager.chat_completions(
                headers={k: v for k, v in request.headers.items()},
                chat_request=cast(ChatRequest, chat_request),
            )
        except Exception as e:
            logger.error(f"Error in chat completions: {e}")
            raise

    router.add_api_route(
        "/api/v1/chat/completions",
        chat_completions_handler,
        methods=["POST"],
        response_model=None,
    )
    return router


def create_models_router(model_manager: ModelManager) -> APIRouter:
    router = APIRouter()

    async def models_handler() -> Dict[str, List[Dict[str, str]]]:
        return await model_manager.get_models()

    router.add_api_route("/api/v1/models", models_handler, methods=["GET"])
    return router


def create_health_router() -> APIRouter:
    router = APIRouter()
    router.add_api_route("/health", lambda: "OK", methods=["GET"])
    return router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    """
    # Startup
    try:
        # Configure logging
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logging.basicConfig(
            level=getattr(logging, log_level),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        logger.info("Starting application initialization...")

        # Initialize managers
        chat_manager = ChatCompletionManager()

        model_manager = ModelManager()

        # Create and include routes with initialized managers
        logger.info("Setting up routes...")
        app.include_router(create_health_router())
        app.include_router(create_chat_router(chat_manager))
        app.include_router(create_models_router(model_manager))

        logger.info("Application initialization completed")

        # Store managers for cleanup
        app.state.managers = [chat_manager, model_manager]
        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    finally:
        # Cleanup
        try:
            logger.info("Starting application shutdown...")

            logger.info("Application shutdown completed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            raise


# Create the app instance at module level
app = FastAPI(title="OpenAI-compatible API", lifespan=lifespan)
