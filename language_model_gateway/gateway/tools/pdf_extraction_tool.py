import base64
import io
import logging
import os
from typing import Type, Literal, Tuple, Optional, Dict

import pypdf
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class PDFExtractionToolInput(BaseModel):
    """Input model for PDF extraction tool."""

    base64_pdf: str = Field(
        description="Base64 encoded PDF content to extract text from"
    )
    start_page: Optional[int] = Field(
        default=None, description="Optional starting page for extraction (0-indexed)"
    )
    end_page: Optional[int] = Field(
        default=None, description="Optional ending page for extraction (0-indexed)"
    )


class PDFExtractionTool(BaseTool):
    """
    LangChain-compatible tool for extracting text from base64 encoded PDFs using PyPDF.
    """

    name: str = "pdf_text_extractor"
    description: str = (
        "Extracts text from a base64 encoded PDF. "
        "Provide the base64 encoded PDF content. "
        "Optionally specify start and end pages for partial extraction."
    )
    args_schema: Type[BaseModel] = PDFExtractionToolInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    def _run(
        self,
        base64_pdf: str,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).

        :param base64_pdf: Base64 encoded PDF content
        :param start_page: Optional starting page for extraction
        :param end_page: Optional ending page for extraction
        :return: Tuple of extracted text and artifact description
        """
        raise NotImplementedError("Use async version of this tool")

    async def _arun(
        self,
        base64_pdf: str,
        start_page: Optional[int] = None,
        end_page: Optional[int] = None,
    ) -> Tuple[str, str]:
        """
        Asynchronous version of the tool.

        :param base64_pdf: Base64 encoded PDF content
        :param start_page: Optional starting page for extraction
        :param end_page: Optional ending page for extraction
        :return: Tuple of extracted text and artifact description
        """
        logger.info(f"Extracting text from base64 encoded PDF")

        if not base64_pdf:
            return "", "PDFExtractionTool: Empty input PDF content"

        try:
            # Decode the base64 string to bytes
            pdf_bytes = base64.b64decode(base64_pdf)

            # Create a bytes buffer to simulate file-like object
            pdf_buffer = io.BytesIO(pdf_bytes)

            # Create a PDF reader object
            pdf_reader = pypdf.PdfReader(pdf_buffer)

            # Determine page range
            total_pages = len(pdf_reader.pages)
            start = start_page if start_page is not None else 0
            end = end_page if end_page is not None else total_pages - 1

            # Validate page range
            if start < 0 or end >= total_pages or start > end:
                raise ValueError(f"Invalid page range. Total pages: {total_pages}")

            # Extract text from specified pages with improved text extraction
            full_text = ""
            for page_num in range(start, end + 1):
                page = pdf_reader.pages[page_num]

                # Use multiple methods to extract text
                try:
                    # Primary method: extract_text()
                    page_text = page.extract_text()

                    # Fallback: extract text from page object
                    if not page_text:
                        page_text = page.extract_text(extraction_mode="layout")
                except Exception as extract_error:
                    logger.warning(
                        f"Text extraction failed for page {page_num}: {extract_error}"
                    )
                    page_text = ""

                full_text += page_text + "\n"

            # Log extraction details if logging is enabled
            if os.environ.get("LOG_INPUT_AND_OUTPUT", "0") == "1":
                logger.info(
                    f"==== Extracted PDF Text (Pages {start}-{end}) ======\n"
                    f"{full_text}\n"
                    f"====== End of Extracted PDF Text ======"
                )

            # Prepare artifact description
            artifact = (
                f"PDFExtractionTool: Extracted text from pages {start} to {end} "
                f"(Total pages: {total_pages})"
            )

            return full_text.strip(), artifact

        except Exception as e:
            error_msg = f"Failed to extract PDF contents: {str(e)}"
            error_artifact = f"PDFExtractionTool: Failed to process PDF: {str(e)}"

            return error_msg, error_artifact

    def extract_metadata(self, base64_pdf: str) -> Dict[str, str]:
        """
        Extract metadata from the PDF.

        :param base64_pdf: Base64 encoded PDF content
        :return: Dictionary of PDF metadata
        """
        try:
            # Decode the base64 string to bytes
            pdf_bytes = base64.b64decode(base64_pdf)

            # Create a bytes buffer to simulate file-like object
            pdf_buffer = io.BytesIO(pdf_bytes)

            # Create a PDF reader object
            pdf_reader = pypdf.PdfReader(pdf_buffer)

            # Extract metadata
            metadata: Dict[str, str] = pdf_reader.metadata or {}

            # Convert metadata to dictionary
            return {
                k.replace("/", ""): v
                for k, v in metadata.items()
                if isinstance(k, str) and isinstance(v, str)
            }

        except Exception as e:
            logger.error(f"Failed to extract PDF metadata: {str(e)}")
            return {}
