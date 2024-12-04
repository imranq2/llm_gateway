from pathlib import Path

from language_model_gateway.gateway.image_generation.image_generator import (
    ImageGenerator,
)


class MockImageGenerator(ImageGenerator):
    def generate_image(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        return b"mock_image_data"

    def save_image(self, image_data: bytes, filename: Path) -> None:
        pass
