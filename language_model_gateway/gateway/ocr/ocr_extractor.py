class OCRExtractor:
    def extract_text_with_textract(self, pdf_bytes: bytes) -> str:
        raise NotImplementedError("Method should be implemented by subclass")
