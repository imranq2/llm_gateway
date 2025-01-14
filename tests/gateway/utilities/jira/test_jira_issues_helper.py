import json
import os
from datetime import datetime, timezone
from os import makedirs, path
from pathlib import Path
from shutil import rmtree
from typing import Dict, List, Optional, Any

import pytest
from pytest_httpx import HTTPXMock

from language_model_gateway.container.simple_container import SimpleContainer
from language_model_gateway.gateway.api_container import get_container_async
from language_model_gateway.gateway.http.http_client_factory import HttpClientFactory
from language_model_gateway.gateway.utilities.environment_reader import (
    EnvironmentReader,
)
from language_model_gateway.gateway.utilities.environment_variables import (
    EnvironmentVariables,
)
from language_model_gateway.gateway.utilities.jira.jira_issue import JiraIssue
from language_model_gateway.gateway.utilities.jira.jira_issues_helper import (
    JiraIssueHelper,
)
from tests.gateway.mocks.mock_environment_variables import MockEnvironmentVariables


async def test_jira_get_summarized_issues(httpx_mock: HTTPXMock) -> None:
    print()
    data_dir: Path = Path(__file__).parent.joinpath("./")
    temp_folder = data_dir.joinpath("./temp")
    if path.isdir(temp_folder):
        rmtree(temp_folder)
    makedirs(temp_folder)

    max_projects = 2

    test_container: SimpleContainer = await get_container_async()

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        jira_base_url: str = "https://your-org.atlassian.net"
        access_token: Optional[str] = "fake_token"
        test_container.register(
            EnvironmentVariables, lambda c: MockEnvironmentVariables()
        )

        # Mock Jira search API response
        search_url = f"{jira_base_url}/rest/api/3/search"
        sample_issues_content: Dict[str, Any] = {
            "total": 2,
            "issues": [
                {
                    "key": "PROJECT-1",
                    "fields": {
                        "summary": "First test issue",
                        "status": {"name": "Closed"},
                        "created": "2024-09-01T00:00:00.000Z",
                        "resolutiondate": "2024-09-02T00:00:00.000Z",
                        "assignee": {"displayName": "user1"},
                        "project": {"key": "PROJECT"},
                    },
                },
                {
                    "key": "PROJECT-2",
                    "fields": {
                        "summary": "Second test issue",
                        "status": {"name": "Closed"},
                        "created": "2024-09-01T00:00:00.000Z",
                        "resolutiondate": "2024-09-02T00:00:00.000Z",
                        "assignee": {"displayName": "user2"},
                        "project": {"key": "PROJECT"},
                    },
                },
            ],
        }

        httpx_mock.add_response(
            url=search_url,
            method="GET",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "AsyncJiraIssueHelper",
            },
            content=json.dumps(sample_issues_content).encode(),
            status_code=200,
        )
    else:
        # Get credentials from environment variables
        jira_base_url = os.getenv("JIRA_BASE_URL", "")
        access_token = os.getenv("JIRA_TOKEN")

    if not jira_base_url or not access_token:
        raise ValueError(
            "Please set JIRA_BASE_URL and JIRA_TOKEN environment variables"
        )

    http_client_factory = HttpClientFactory()

    # Initialize Jira Issue Helper
    issue_helper = JiraIssueHelper(
        jira_base_url=jira_base_url,
        access_token=access_token,
        http_client_factory=http_client_factory,
    )

    # Get issue counts with optional parameters
    issues: List[JiraIssue] = await issue_helper.retrieve_closed_issues(
        max_projects=max_projects,  # Optional: limit projects
        max_issues=200,  # Optional: limit issues
        min_created_at=datetime(
            2024, 9, 1, tzinfo=timezone.utc
        ),  # Optional: minimum created date
    )

    issue_counts: Dict[str, Dict[str, Any]] = issue_helper.summarize_issues_by_assignee(
        issues=issues
    )

    # Assertions
    assert len(issue_counts) > 0
    assert len(issues) == 2

    # Verify issue details
    assert issues[0].key == "PROJECT-1"
    assert issues[0].assignee == "user1"
    assert issues[1].key == "PROJECT-2"
    assert issues[1].assignee == "user2"

    # Verify summary
    assert len(issue_counts) == 2
    assert issue_counts["user1"]["issue_count"] == 1
    assert issue_counts["user2"]["issue_count"] == 1

    # Export results
    issue_helper.export_results(
        issue_counts=issue_counts,
        output_file=str(
            temp_folder.joinpath("issue_counts.tsv")
        ),  # Optional TSV export
    )

    # Verify export file was created
    assert path.exists(temp_folder.joinpath("issue_counts.tsv"))


@pytest.mark.asyncio
async def test_jira_issue_helper_error_handling(httpx_mock: HTTPXMock) -> None:
    """
    Test error handling scenarios for Jira Issue Helper
    """
    jira_base_url = "https://your-org.atlassian.net"
    access_token = "fake_token"
    http_client_factory = HttpClientFactory()

    # Mock a server error response
    httpx_mock.add_response(
        url=f"{jira_base_url}/rest/api/3/search",
        method="GET",
        status_code=500,
        content=json.dumps({"error": "Internal Server Error"}).encode(),
    )

    issue_helper = JiraIssueHelper(
        jira_base_url=jira_base_url,
        access_token=access_token,
        http_client_factory=http_client_factory,
    )

    # Test error handling
    with pytest.raises(Exception):
        await issue_helper.retrieve_closed_issues(max_issues=10)
