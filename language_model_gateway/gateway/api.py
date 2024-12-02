import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator
from typing import TypedDict

from fastapi import FastAPI

from language_model_gateway.gateway.routers.chat_completion_router import (
    ChatCompletionsRouter,
)
from language_model_gateway.gateway.routers.models_router import ModelsRouter

# warnings.filterwarnings("ignore", category=LangChainBetaWarning)

logger = logging.getLogger(__name__)


class ErrorDetail(TypedDict):
    message: str
    timestamp: str
    trace_id: str
    call_stack: str


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

        # perform any startup tasks here

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

# Include routers
app.include_router(ChatCompletionsRouter().get_router())
app.include_router(ModelsRouter().get_router())


@app.get("/health")
async def health() -> str:
    return "OK"
