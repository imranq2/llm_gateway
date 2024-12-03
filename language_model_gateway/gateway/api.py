import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from starlette.staticfiles import StaticFiles

from language_model_gateway.gateway.routers.chat_completion_router import (
    ChatCompletionsRouter,
)
from language_model_gateway.gateway.routers.models_router import ModelsRouter
from fastapi.responses import FileResponse

# warnings.filterwarnings("ignore", category=LangChainBetaWarning)

logger = logging.getLogger(__name__)


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


def create_app() -> FastAPI:
    app1: FastAPI = FastAPI(title="OpenAI-compatible API", lifespan=lifespan)
    app1.include_router(ChatCompletionsRouter().get_router())
    app1.include_router(ModelsRouter().get_router())
    return app1


# Create the FastAPI app instance
app = create_app()


@app.get("/health")
async def health() -> str:
    return "OK"


# Mount the static directory
app.mount(
    "/static", StaticFiles(directory="language_model_gateway/static"), name="static"
)


@app.get("/favicon.png", include_in_schema=False)
async def favicon() -> FileResponse:
    # Get absolute path
    file_path = Path("language_model_gateway/static/bwell-web.png")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)
