from language_model_gateway.gateway.file_managers.file_manager import FileManager
from language_model_gateway.gateway.file_managers.file_manager_factory import (
    FileManagerFactory,
)
from language_model_gateway.gateway.tools.resilient_base_tool import ResilientBaseTool
from pydantic import BaseModel, Field
from typing import Type, Optional, Tuple, Literal
from starlette.responses import Response, StreamingResponse

from language_model_gateway.gateway.utilities.s3_url import S3Url


class HealthSummaryGeneratorModel(BaseModel):
    """
    Model to generate the health summary report for each user showing the diagnosis, procedures and medications of the
    user
    """

    s3_uri: Optional[str] = Field(
        default=None,
        description="S3 uri for the file for which we will be generating the health summary",
    )


class HealthSummaryGeneratorTool(ResilientBaseTool):
    """
    The HealthSummaryGeneratorTool is designed to generate comprehensive health summary reports for users
    by processing claims data files stored in S3. This tool extracts and deduplicates information about
    diagnoses, procedures, and medications for each user, producing a structured JSON report.
    """

    name: str = "health_summary_generator"

    description: str = """
    The HealthSummaryGeneratorTool is designed to generate comprehensive health summary reports for users 
    by processing claims data files stored in S3. This tool extracts and deduplicates information about 
    diagnoses, procedures, and medications for each user, producing a structured JSON report.
    Features:
    - Accepts a file URL pointing to a claims file in S3.
    - Extracts data related to diagnoses, procedures, and pharmaceuticals, checking for both names and codes.
    - Searches for descriptions of codes if provided, using them for further processing.
    - Deduplicates all extracted data to ensure clean output.
    - Generates a summary JSON object for each user, outlining consolidated health data.
    """

    args_schema: Type[BaseModel] = (
        HealthSummaryGeneratorModel  # Should be the input parameters class you created above
    )
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    file_manager_factory: FileManagerFactory

    async def _arun(self, s3_uri: Optional[str] = None) -> Tuple[str, str]:
        """
        Asynchronous version of the health summary generator tool.
        :param s3_uri: (string) s3 uri of the file which we need to parse.
        :return: The content of the file.
        """
        # do your actual work here
        if not s3_uri:
            return "No s3 file path provided", "uri for S3 object is required"

        # Create a file manager instance from the factory
        file_manager: FileManager = self.file_manager_factory.get_file_manager(
            folder=s3_uri
        )

        s3_uri = S3Url(s3_uri)
        bucket_name = s3_uri.bucket
        file_name = s3_uri.key

        # Download the file from the S3 bucket
        response: StreamingResponse | Response = await file_manager.read_file_async(
            folder=bucket_name, file_path=file_name
        )

        # Check if the response is successful
        if not isinstance(response, StreamingResponse):
            return "Failed to retrieve the file", f"Error retrieving file: {response}"

        # Extract content from the file
        content = await self._extract_content(response)
        return content, "File successfully fetched"

    def _run(self, s3_uri: Optional[str] = None) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).
        :param s3_uri: (string) s3 uri of the file which we need to parse.
        Raises:
            NotImplementedError: Always raises to enforce async usage
        """
        raise NotImplementedError("Use async version of this tool")

    @staticmethod
    async def _extract_content(response: StreamingResponse) -> str:
        """
        Extracts and returns content from a streaming response.
        :param response: (StreamingResponse) s3 response for the file
        :return: returns the file content in string format.
        """
        extracted_content = ""
        async for chunk in response.body_iterator:
            # Decode the chunk, assuming it is UTF-8 encoded
            extracted_content += chunk.decode("utf-8")  # type: ignore

        return extracted_content
