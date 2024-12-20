import logging
import os
from typing import Optional
from uuid import uuid4

import boto3

from language_model_gateway.gateway.aws.aws_client_factory import AwsClientFactory
from language_model_gateway.gateway.file_managers.file_manager import FileManager
from language_model_gateway.gateway.file_managers.file_manager_factory import (
    FileManagerFactory,
)
from language_model_gateway.gateway.ocr.ocr_extractor import OCRExtractor
from language_model_gateway.gateway.utilities.url_parser import UrlParser

logger = logging.getLogger(__name__)


class AwsOCRExtractor(OCRExtractor):
    def __init__(
        self,
        *,
        aws_client_factory: AwsClientFactory,
        file_manager_factory: FileManagerFactory,
    ) -> None:
        self.aws_client_factory: AwsClientFactory = aws_client_factory
        assert self.aws_client_factory is not None
        assert isinstance(self.aws_client_factory, AwsClientFactory)
        self.file_manager_factory: FileManagerFactory = file_manager_factory
        assert self.file_manager_factory is not None
        assert isinstance(self.file_manager_factory, FileManagerFactory)

    async def extract_text_with_textract_async(self, pdf_bytes: bytes) -> str:
        try:
            # first save the file to s3
            # Save the file to S3
            image_generation_path_ = os.environ["IMAGE_GENERATION_PATH"]
            assert (
                image_generation_path_
            ), "IMAGE_GENERATION_PATH environment variable is not set"
            image_file_name: str = f"{uuid4()}.pdf"

            file_manager: FileManager = self.file_manager_factory.get_file_manager(
                folder=image_generation_path_
            )
            file_path: Optional[str] = await file_manager.save_file_async(
                file_data=pdf_bytes,
                folder=image_generation_path_,
                filename=image_file_name,
                content_type="application/pdf",
            )
            assert file_path is not None

            # Call Textract API
            textract_client: boto3.client = self.aws_client_factory.create_client(
                service_name="textract"
            )

            s3_bucket, s3_object_key = UrlParser.parse_s3_uri(file_path)

            response = textract_client.detect_document_text(
                Document={"S3Object": {"Bucket": s3_bucket, "Name": s3_object_key}}
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
