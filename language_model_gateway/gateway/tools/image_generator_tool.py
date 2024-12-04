import logging

from langchain.tools import BaseTool

from language_model_gateway.gateway.utilities.aws_image_generator import (
    AwsImageGenerator,
)

logger = logging.getLogger(__name__)


class ImageGeneratorTool(BaseTool):
    """
    LangChain-compatible tool for generating an image from a given text.
    """

    name: str = "image_generator"
    description: str = (
        "Generates an image from a given text. "
        "Provide the text as input. "
        # "The tool will return the image as a base64 encoded string in PNG format: `data:image/png;base64,{base64_image}`."
        "The tool will return a url to the generated image."
    )
    return_direct: bool = True

    def _run(self, prompt: str) -> str:
        """
        Synchronous version of the tool (falls back to async implementation).
        :param prompt: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        raise NotImplementedError("Use async version of this tool")

    async def _arun(self, prompt: str) -> str:
        """
        Asynchronous version of the tool.
        :param prompt: The URL of the webpage to fetch.
        :return: The content of the webpage in Markdown format.
        """
        try:
            aws_image_generator: AwsImageGenerator = AwsImageGenerator()
            # styles = ["natural", "cinematic", "digital-art", "pop-art"]
            style = "natural"
            image_data: bytes = aws_image_generator.generate_image(
                prompt=prompt, style=style, image_size="1024x1024"
            )
            # base64_image: str = base64.b64encode(image_data).decode("utf-8")

            url = aws_image_generator.get_url(image_bytes=image_data)
            return url
        except Exception as e:
            logger.error(f"Failed to generate image: {str(e)}")
            raise ValueError(f"Failed to generate image: {str(e)}")
