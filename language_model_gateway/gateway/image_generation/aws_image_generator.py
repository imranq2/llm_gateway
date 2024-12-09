import asyncio
import base64
import json
import logging
import os
from concurrent.futures.thread import ThreadPoolExecutor
from typing import override, Dict, Any

import boto3

from language_model_gateway.gateway.image_generation.image_generator import (
    ImageGenerator,
)

logger = logging.getLogger(__name__)


class AwsImageGenerator(ImageGenerator):
    def __init__(self) -> None:
        self.executor: ThreadPoolExecutor = ThreadPoolExecutor()

    def _create_bedrock_client(self) -> boto3.client:
        """Create and return a Bedrock client"""
        session1 = boto3.Session(profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"))
        bedrock_client = session1.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
        )
        return bedrock_client

    def _invoke_model(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous model invocation"""

        client: boto3.client = self._create_bedrock_client()
        response: Dict[str, Any] = client.invoke_model(
            modelId="amazon.titan-image-generator-v2:0",
            body=json.dumps(request_body),
        )
        return response

    @override
    async def generate_image_async(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        """Generate an image using Titan Image Generator"""
        logger.info(f"Generating image for prompt: {prompt}")

        request_body = {
            "textToImageParams": {"text": prompt},
            "taskType": "TEXT_IMAGE",
            "imageGenerationConfig": {
                "cfgScale": 8,
                "seed": 0,
                "width": 1024,
                "height": 1024,
                "numberOfImages": 1,
                "quality": "standard",
            },
        }

        try:
            # Get the current event loop
            loop = asyncio.get_running_loop()

            # Run model invocation in executor
            response = await loop.run_in_executor(
                self.executor, self._invoke_model, request_body
            )

            # Parse the response
            response_body = json.loads(response["body"].read())

            # Get the base64 encoded image
            base64_image = response_body["images"][0]

            # Convert base64 to bytes
            image_data = base64.b64decode(base64_image)

            logger.info(f"Image generated successfully for prompt: {prompt}")
            return image_data

        except Exception as e:
            logger.error(f"Error generating image for prompt {prompt}: {str(e)}")
            logger.exception(e, stack_info=True)
            raise
