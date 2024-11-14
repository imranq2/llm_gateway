from typing import Generator
import logging
import os

import pytest
from fastapi.testclient import TestClient

from language_model_gateway.graphql import api


@pytest.fixture
def graphql_client() -> Generator[TestClient, None, None]:
    app = api.app
    # app.config["TESTING"] = True

    # Get log level from environment variable
    log_level = os.getenv("LOG_LEVEL", "INFO").upper()

    # Set up basic configuration for logging
    logging.basicConfig(level=getattr(logging, log_level))

    client = TestClient(app)
    yield client  # Use `yield` to ensure any teardown can happen after the test runs
