import logging
import os
from typing import Optional

# Since graphql_sync is used, assuming a similar synchronous approach is acceptable
from ariadne import graphql
from ariadne.explorer import ExplorerPlayground
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
from prometheus_fastapi_instrumentator import Instrumentator

from language_model_gateway.api_schema import ApiSchema

# Get log level from environment variable
log_level = os.getenv("LOG_LEVEL", "INFO").upper()

# Set up basic configuration for logging
logging.basicConfig(level=getattr(logging, log_level))

app = FastAPI()

PLAYGROUND_HTML: Optional[str] = ExplorerPlayground(title="language_model_gateway").html(None)  # type: ignore[no-untyped-call]

# Set up CORS middleware; adjust parameters as needed
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# noinspection SpellCheckingInspection
instrumentator = Instrumentator()
instrumentator.instrument(app).expose(app)


@app.get("/", response_class=HTMLResponse)
def hello() -> str:
    return "Use /graphql endpoint to test"


@app.get("/health")
def health() -> str:
    return "OK"


@app.get("/graphql", response_class=HTMLResponse)
def graphql_playground() -> str:
    assert PLAYGROUND_HTML is not None
    return PLAYGROUND_HTML


@app.post("/graphql")
async def graphql_server(request: Request) -> JSONResponse:
    data = await request.json()
    print(f"API call [{request.client.host if request.client else None}] {data!r}")

    success, result = await graphql(
        ApiSchema.schema,
        data,
        context_value=request,
        debug=False,
    )

    status_code = 200 if success else 400
    return JSONResponse(result, status_code=status_code)
