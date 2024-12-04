from pathlib import Path


class ImageGenerator:
    def generate_image(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        raise NotImplementedError("Must be implemented by subclass")

    def save_image(self, image_data: bytes, filename: Path) -> None:
        raise NotImplementedError("Must be implemented by subclass")
