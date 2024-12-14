class ImageGenerator:
    async def generate_image_async(
        self, prompt: str, style: str = "natural", image_size: str = "1024x1024"
    ) -> bytes:
        raise NotImplementedError("Must be implemented by subclass")
