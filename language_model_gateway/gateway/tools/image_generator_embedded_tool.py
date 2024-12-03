import base64
import json
import logging
import os
from os import makedirs
from pathlib import Path
from typing import Tuple, Literal
from uuid import uuid4

import boto3
from langchain.tools import BaseTool

logger = logging.getLogger(__name__)


class ImageGeneratorEmbeddedTool(BaseTool):
    """
    LangChain-compatible tool for generating an image from a given text.
    """

    name: str = "image_generator"
    description: str = (
        "Generates an image from a given text. "
        "Provide the text as input. "
        "The tool will return the url to the image and a markdown containing a base64 encoded string in PNG format: `data:image/png;base64,{base64_image}`."
        # "The tool will return a url to the generated image."
    )
    return_direct: bool = True
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    # noinspection PyMethodMayBeStatic
    def create_bedrock_client(self) -> boto3.client:
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

    def generate_image(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        """Generate an image using Titan Image Generator"""

        logger.info(f"Generating image for prompt: {prompt}")

        # Create Bedrock client
        client = self.create_bedrock_client()

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
            response = client.invoke_model(
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
            raise Exception(f"Error generating image: {str(e)}")

    # noinspection PyMethodMayBeStatic
    def save_image(self, image_data: bytes, filename: Path) -> None:
        """Save the generated image to a file"""
        if image_data:
            with open(filename, "wb") as f:
                f.write(image_data)
            print(f"Image saved as {filename}")
        else:
            print("No image to save")

    def _run(self, prompt: str) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).
        :param prompt: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        raise NotImplementedError("Use async version of this tool")

    async def _arun(self, prompt: str) -> Tuple[str, str]:
        """
        Asynchronous version of the tool.
        :param prompt: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        try:
            # styles = ["natural", "cinematic", "digital-art", "pop-art"]
            style = "natural"
            image_data: bytes = self.generate_image(
                prompt=prompt, style=style, image_size="1024x1024"
            )
            image_generation_path = Path(os.environ["IMAGE_GENERATION_PATH"])
            makedirs(image_generation_path, exist_ok=True)
            # image_file_name = f"{prompt.replace(' ', '_')}_{style}.png"
            base64_image: str = base64.b64encode(image_data).decode("utf-8")
            embedded_url = f"data:image/png;base64,{base64_image}"
            markdown_image = f"![Generated Image]({embedded_url})"

            # now save the image on the server
            # create a random image file name
            image_file_name = f"{uuid4()}.png"
            self.save_image(image_data, image_generation_path.joinpath(image_file_name))
            image_generation_url = os.environ["IMAGE_GENERATION_URL"]
            url = f"{image_generation_url}/{image_file_name}"
            return f"{url} ", markdown_image
        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            raise ValueError(f"Failed to generate image: {str(e)}")
