import logging

import boto3

from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory
from language_model_gateway.gateway.ocr.ocr_extractor import OCRExtractor

logger = logging.getLogger(__name__)


class AwsOCRExtractor(OCRExtractor):
    def __init__(self, *, aws_client_factory: AwsClientFactory) -> None:
        self.aws_client_factory: AwsClientFactory = aws_client_factory
        assert self.aws_client_factory is not None
        assert isinstance(self.aws_client_factory, AwsClientFactory)

    def extract_text_with_textract(self, pdf_bytes: bytes) -> str:
        try:
            # Call Textract API
            textract_client: boto3.client = self.aws_client_factory.create_client(
                service_name="textract"
            )

            response = textract_client.detect_document_text(
                Document={"Bytes": pdf_bytes}
            )

            # Process and extract text
            current_page_text = []

            for item in response.get("Blocks", []):
                if item["BlockType"] == "LINE":
                    current_page_text.append(item["Text"])

            # Join extracted text
            full_text = " ".join(current_page_text)

            return full_text

        except Exception as e:
            logger.error(f"Textract OCR failed: {str(e)}")
            return ""
