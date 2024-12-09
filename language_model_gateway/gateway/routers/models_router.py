import logging
from enum import Enum
from typing import Annotated, Dict, List, Sequence
from fastapi import APIRouter, Depends
from starlette.requests import Request
from fastapi import params

from language_model_gateway.configs.config_schema import ChatModelConfig
from language_model_gateway.gateway.api_container import get_model_manager
from language_model_gateway.gateway.managers.model_manager import ModelManager
from language_model_gateway.gateway.utilities.state_manager import StateManager

logger = logging.getLogger(__name__)


class ModelsRouter:
    """
    Router class for models endpoints
    """

    def __init__(
        self,
        *,
        state_manager: StateManager,
        prefix: str = "/api/v1",
        tags: list[str | Enum] | None = None,
        dependencies: Sequence[params.Depends] | None = None,
    ) -> None:
        self.state_manager = state_manager
        self.prefix = prefix
        self.tags = tags or ["models"]
        self.dependencies = dependencies or []
        self.router = APIRouter(
            prefix=self.prefix, tags=self.tags, dependencies=self.dependencies
        )
        self._register_routes()

    def _register_routes(self) -> None:
        """Register all routes for this router"""
        self.router.add_api_route(
            "/models",
            self.get_models,
            methods=["GET"],
            response_model=Dict[str, List[Dict[str, str]]],
            summary="List available models",
            description="Lists the currently available models",
            response_description="The list of available models",
            status_code=200,
        )

    # noinspection PyMethodMayBeStatic
    async def get_models(
        self,
        request: Request,
        model_manager: Annotated[ModelManager, Depends(get_model_manager)],
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Get models endpoint. model_manager is injected by FastAPI.

        Args:
            request: The incoming request
            model_manager: Injected model manager instance

        Returns:
            Dictionary containing list of available models
        """
        configs: List[ChatModelConfig] = self.state_manager.get("models")
        return await model_manager.get_models(
            configs=configs,
            headers={k: v for k, v in request.headers.items()},
        )

    def get_router(self) -> APIRouter:
        """Get the configured router"""
        return self.router
