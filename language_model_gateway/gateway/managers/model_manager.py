import logging
from typing import Dict, List


class ModelManager:
    # Mock list of models
    models = [
        {"id": "search-web", "description": "Highly capable language model"},
        {"id": "b.well", "description": "Conversational PHR"},
    ]

    @staticmethod
    async def get_models() -> Dict[str, List[Dict[str, str]]]:
        logger = logging.getLogger(__name__)
        logger.info("Received request for models")
        return {"data": ModelManager.models}
