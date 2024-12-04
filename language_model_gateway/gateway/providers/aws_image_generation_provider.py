import base64
import logging
import time
from typing import Dict, List, Literal, Optional

from openai import NotGiven
from openai.types import ImagesResponse, Image
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.providers.base_image_generation_provider import (
    BaseImageGenerationProvider,
)
from language_model_gateway.gateway.schema.openai.image_generation import (
    ImageGenerationRequest,
)
from language_model_gateway.gateway.utilities.aws_image_generator import (
    AwsImageGenerator,
)


logger = logging.getLogger(__name__)


class AwsImageGenerationProvider(BaseImageGenerationProvider):
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

        aws_image_generator: AwsImageGenerator = AwsImageGenerator()

        prompt = image_generation_request["prompt"]
        assert prompt is not None
        assert isinstance(prompt, str)

        image_bytes: bytes = aws_image_generator.generate_image(prompt=prompt)

        response_data: List[Image]
        if response_format == "b64_json":
            # convert image_bytes to base64 json
            # logger.info(f"image_bytes: {image_bytes!r}")
            image_b64_json = base64.b64encode(image_bytes).decode("utf-8")
            # logger.info(f"image_b64_json: {image_b64_json}")
            response_data = [Image(b64_json=image_b64_json)]
        else:
            url = aws_image_generator.get_url(image_bytes=image_bytes)
            response_data = [Image(url=url)]

        response: ImagesResponse = ImagesResponse(
            created=int(time.time()), data=response_data
        )
        return JSONResponse(content=response.model_dump())
