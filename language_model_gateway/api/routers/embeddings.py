from typing import Annotated

from fastapi import APIRouter, Depends, Body

from language_model_gateway.api.auth import api_key_auth
from language_model_gateway.api.models.bedrock import get_embeddings_model
from language_model_gateway.api.schema import EmbeddingsRequest, EmbeddingsResponse
from language_model_gateway.api.setting import DEFAULT_EMBEDDING_MODEL

router = APIRouter(
    prefix="/embeddings",
    dependencies=[Depends(api_key_auth)],
)


@router.post("", response_model=EmbeddingsResponse)
async def embeddings(
    embeddings_request: Annotated[
        EmbeddingsRequest,
        Body(
            examples=[
                {
                    "model": "cohere.embed-multilingual-v3",
                    "input": ["Your text string goes here"],
                }
            ],
        ),
    ]
) -> EmbeddingsResponse:
    if embeddings_request.model.lower().startswith("text-embedding-"):
        embeddings_request.model = DEFAULT_EMBEDDING_MODEL
    # Exception will be raised if model not supported.
    model = get_embeddings_model(embeddings_request.model)
    return model.embed(embeddings_request)
