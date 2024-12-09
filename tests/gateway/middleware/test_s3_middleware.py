from pathlib import Path

import pytest
import boto3
from moto import mock_aws
from fastapi import FastAPI, Request
from unittest.mock import patch, MagicMock

from starlette.responses import Response

from language_model_gateway.gateway.middleware.s3_middleware import S3Middleware


@pytest.fixture
def fastapi_app() -> FastAPI:
    return FastAPI()


@pytest.fixture
def mock_s3() -> boto3.client:
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")


@pytest.fixture
def s3_middleware(fastapi_app: FastAPI, mock_s3: boto3.client) -> S3Middleware:
    return S3Middleware(
        app=fastapi_app,
        image_generation_path="s3://test-bucket/images/",
        target_path="/image_generation/",
        allowed_extensions=["jpg", "png"],
    )


async def test_s3_middleware_check_extension(s3_middleware: S3Middleware) -> None:
    # Test allowed extensions
    assert s3_middleware.check_extension("image.jpg") == True
    assert s3_middleware.check_extension("image.png") == True
    assert s3_middleware.check_extension("image.gif") == False

    # Test when no extensions are specified
    s3_middleware.allowed_extensions = None
    assert s3_middleware.check_extension("image.gif") == True


async def test_s3_middleware_handle_s3_request_with_moto(
    fastapi_app: FastAPI, mock_s3: boto3.client
) -> None:
    # Create S3 bucket and upload a test file
    bucket_name = "test-bucket"
    mock_s3.create_bucket(Bucket=bucket_name)

    # Prepare test image content
    test_image_content = b"test image content"
    mock_s3.put_object(
        Bucket=bucket_name, Key="images/test.jpg", Body=test_image_content
    )

    # Create middleware
    middleware = S3Middleware(
        app=fastapi_app,
        image_generation_path=f"s3://{bucket_name}/images",
        target_path="/image_generation/",
        allowed_extensions=["jpg", "png"],
    )

    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/image_generation/test.jpg"

    # Call handle_s3_request
    response = await middleware.handle_s3_request(mock_request)

    # Assertions
    assert response.status_code == 200
    assert response.body == test_image_content


async def test_s3_middleware_local_file_handling(
    fastapi_app: FastAPI, tmp_path: Path
) -> None:
    # Create a temporary file
    test_file_path = tmp_path / "test.jpg"
    test_content = b"local file content"
    test_file_path.write_bytes(test_content)

    # Create middleware with local path
    middleware = S3Middleware(
        app=fastapi_app,
        image_generation_path=str(tmp_path) + "/",
        target_path="/image_generation/",
        allowed_extensions=["jpg", "png"],
    )

    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/image_generation/test.jpg"

    # Call handle_s3_request
    response: Response = await middleware.handle_s3_request(mock_request)

    # Assertions
    assert response.status_code == 200
    assert response.body == test_content


async def test_s3_middleware_extension_filtering(fastapi_app: FastAPI) -> None:
    # Create middleware with specific allowed extensions
    middleware = S3Middleware(
        app=fastapi_app,
        image_generation_path="s3://test-bucket/images/",
        target_path="/image_generation/",
        allowed_extensions=["jpg", "png"],
    )

    # Create a mock request with non-allowed extension
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/image_generation/images/test.gif"

    # Call handle_s3_request
    response = await middleware.handle_s3_request(mock_request)

    # Assert forbidden for non-allowed extension
    assert response.status_code == 403
    assert response.body == b"File type not allowed"


async def test_s3_middleware_file_not_found(fastapi_app: FastAPI) -> None:
    # Create middleware
    middleware = S3Middleware(
        app=fastapi_app,
        image_generation_path="s3://test-bucket/images/",
        target_path="/image_generation/",
    )

    # Create a mock request
    mock_request = MagicMock(spec=Request)
    mock_request.url.path = "/image_generation/nonexistent.jpg"

    # Patch UrlParser and mock S3 file not found
    with patch(
        "your_module.UrlParser.parse_s3_uri",
        return_value=("test-bucket", "images/nonexistent.jpg"),
    ), patch(
        "your_module.AwsS3FileManager.handle_s3_request", side_effect=FileNotFoundError
    ):
        # Call handle_s3_request
        response = await middleware.handle_s3_request(mock_request)

        # Assertions
        assert response.status_code == 404
        assert response.body == b"File not found"
