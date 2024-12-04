import base64
import logging
import time
from typing import Dict, List, Literal, Optional, Union

from openai import NotGiven
from openai.types import ImagesResponse, Image, ImageModel
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.image_generation.image_generator import (
    ImageGenerator,
)
from language_model_gateway.gateway.image_generation.image_generator_factory import (
    ImageGeneratorFactory,
)
from language_model_gateway.gateway.providers.base_image_generation_provider import (
    BaseImageGenerationProvider,
)
from language_model_gateway.gateway.schema.openai.image_generation import (
    ImageGenerationRequest,
)
from language_model_gateway.gateway.utilities.image_generation_helper import (
    ImageGenerationHelper,
)

logger = logging.getLogger(__name__)


class ImageGenerationProvider(BaseImageGenerationProvider):
    def __init__(self, *, image_generator_factory: ImageGeneratorFactory) -> None:
        self.image_generator_factory: ImageGeneratorFactory = image_generator_factory
        assert self.image_generator_factory is not None
        assert isinstance(self.image_generator_factory, ImageGeneratorFactory)

    async def generate_image_async(
        self,
        *,
        image_generation_request: ImageGenerationRequest,
        headers: Dict[str, str],
    ) -> StreamingResponse | JSONResponse:
        """
        Implements the image generation API
        https://platform.openai.com/docs/api-reference/images/create

        :param image_generation_request:
        :param headers:
        :return:
        """
        response_format: Optional[Literal["url", "b64_json"]] | NotGiven = (
            image_generation_request.get("response_format")
        )

        logger.info(f"image_generation_request: {image_generation_request}")

        model: Union[str, ImageModel, None] | NotGiven = image_generation_request.get(
            "model"
        )

        image_generator: ImageGenerator = (
            self.image_generator_factory.get_image_generator(
                model_name=str(model) if model else "aws"
            )
        )

        prompt = image_generation_request["prompt"]
        assert prompt is not None
        assert isinstance(prompt, str)

        image_bytes: bytes = image_generator.generate_image(prompt=prompt)

        response_data: List[Image]
        if response_format == "b64_json":
            # convert image_bytes to base64 json
            # logger.info(f"image_bytes: {image_bytes!r}")
            image_b64_json = base64.b64encode(image_bytes).decode("utf-8")
            # logger.info(f"image_b64_json: {image_b64_json}")
            response_data = [Image(b64_json=image_b64_json)]
        else:
            image_full_path = ImageGenerationHelper.get_full_path()
            image_generator.save_image(image_bytes, image_full_path)
            url = ImageGenerationHelper.get_url_for_file_name(image_full_path)
            response_data = [Image(url=url)]

        response: ImagesResponse = ImagesResponse(
            created=int(time.time()), data=response_data
        )
        return JSONResponse(content=response.model_dump())
