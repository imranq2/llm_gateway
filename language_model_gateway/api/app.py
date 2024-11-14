import logging
from typing import Dict, Any

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from language_model_gateway.api.routers import model, chat, embeddings
from language_model_gateway.api.setting import (
    API_ROUTE_PREFIX,
    TITLE,
    DESCRIPTION,
    SUMMARY,
    VERSION,
)

config = {
    "title": TITLE,
    "description": DESCRIPTION,
    "summary": SUMMARY,
    "version": VERSION,
}

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = FastAPI(**config)  # type: ignore[arg-type]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(model.router, prefix=API_ROUTE_PREFIX)
app.include_router(chat.router, prefix=API_ROUTE_PREFIX)
app.include_router(embeddings.router, prefix=API_ROUTE_PREFIX)


@app.get("/health")
async def health() -> Dict[str, str]:
    """For health check if needed"""
    return {"status": "OK"}


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Any, exc: Any) -> PlainTextResponse:
    return PlainTextResponse(str(exc), status_code=400)
