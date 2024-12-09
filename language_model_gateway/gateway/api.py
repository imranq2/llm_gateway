import logging
import os
from contextlib import asynccontextmanager
from os import makedirs, environ
from pathlib import Path
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from starlette.responses import FileResponse, JSONResponse
from starlette.staticfiles import StaticFiles

from language_model_gateway.configs.config_reader.config_reader import ConfigReader
from language_model_gateway.gateway.routers.chat_completion_router import (
    ChatCompletionsRouter,
)
from language_model_gateway.gateway.routers.image_generation_router import (
    ImageGenerationRouter,
)
from language_model_gateway.gateway.routers.models_router import ModelsRouter
from language_model_gateway.gateway.utilities.state_manager import StateManager

# warnings.filterwarnings("ignore", category=LangChainBetaWarning)

logger = logging.getLogger(__name__)

# create the state manager to hold state such as model configurations
state_manager: StateManager = StateManager()


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
        state_manager.set("models", await ConfigReader().read_model_configs_async())

        logger.info("Application initialization completed")
        yield

    except Exception as e:
        logger.exception(e, stack_info=True)
        raise

    finally:
        try:
            logger.info("Starting application shutdown...")
            # await container.cleanup()
            # Clean up on shutdown
            state_manager.clear()
            print("Data cleaned up")
            logger.info("Application shutdown completed")
        except Exception as e:
            logger.exception(e, stack_info=True)
            raise


def create_app() -> FastAPI:
    app1: FastAPI = FastAPI(title="OpenAI-compatible API", lifespan=lifespan)
    app1.include_router(ChatCompletionsRouter(state_manager=state_manager).get_router())
    app1.include_router(ModelsRouter(state_manager=state_manager).get_router())
    app1.include_router(ImageGenerationRouter(state_manager=state_manager).get_router())
    # Mount the static directory
    app1.mount(
        "/static",
        StaticFiles(
            directory="/usr/src/language_model_gateway/language_model_gateway/static"
        ),
        name="static",
    )

    image_generation_path: str = environ["IMAGE_GENERATION_PATH"]

    assert (
        image_generation_path is not None
    ), "IMAGE_GENERATION_PATH environment variable must be set"

    makedirs(image_generation_path, exist_ok=True)

    app1.mount(
        "/image_generation",
        StaticFiles(directory=image_generation_path),
        name="static",
    )
    return app1


# Create the FastAPI app instance
app = create_app()


@app.get("/health")
async def health() -> str:
    return "OK"


@app.get("/favicon.png", include_in_schema=False)
async def favicon() -> FileResponse:
    # Get absolute path
    file_path = Path("language_model_gateway/static/bwell-web.png")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {file_path}")
    return FileResponse(file_path)


@app.get("/refresh")
async def refresh_data() -> JSONResponse:
    state_manager.set("models", await ConfigReader().read_model_configs_async())
    return JSONResponse(
        {"message": "Data refreshed", "data": state_manager.get("models")}
    )
