from typing import override

from language_model_gateway.gateway.image_generation.image_generator import (
    ImageGenerator,
)


class MockImageGenerator(ImageGenerator):
    @override
    async def generate_image_async(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        return b"mock_image_data"
