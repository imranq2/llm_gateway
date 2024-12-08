import base64
import json
import logging
import os
from pathlib import Path
from typing import override

import boto3

from language_model_gateway.gateway.image_generation.image_generator import (
    ImageGenerator,
)

logger = logging.getLogger(__name__)


class AwsImageGenerator(ImageGenerator):
    # noinspection PyMethodMayBeStatic
    def _create_bedrock_client(self) -> boto3.client:
        """Create and return a Bedrock client"""
        session1 = boto3.Session(profile_name=os.environ.get("AWS_CREDENTIALS_PROFILE"))
        bedrock_client = session1.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",  # Replace with your preferred region
            # Add credentials if not using default AWS configuration:
            # aws_access_key_id='YOUR_ACCESS_KEY',
            # aws_secret_access_key='YOUR_SECRET_KEY'
        )
        return bedrock_client

    @override
    async def generate_image_async(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        """Generate an image using Titan Image Generator"""

        logger.info(f"Generating image for prompt: {prompt}")

        # Create Bedrock client
        client: boto3.client = self._create_bedrock_client()

        # Prepare the request parameters
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
            # Invoke the model
            response = await client.invoke_model_async(
                modelId="amazon.titan-image-generator-v2:0",
                body=json.dumps(request_body),
            )

            # Parse the response
            response_body = json.loads(response["body"].read())

            # Get the base64 encoded image
            base64_image = response_body["images"][0]

            # Convert base64 to bytes
            image_data = base64.b64decode(base64_image)

            logger.info(
                f"Image generated successfully for prompt: {prompt}:\n{base64_image}"
            )
            return image_data

        except Exception as e:
            logger.error(f"Error generating image for prompt {prompt}: {str(e)}")
            logger.exception(e, stack_info=True)
            raise Exception(f"Error generating image: {str(e)}")

        finally:
            # Close the client
            client.close()

    # noinspection PyMethodMayBeStatic
    @override
    async def save_image_async(self, image_data: bytes, filename: Path) -> None:
        """Save the generated image to a file"""
        if image_data:
            with open(filename, "wb") as f:
                f.write(image_data)
            print(f"Image saved as {filename}")
        else:
            print("No image to save")
