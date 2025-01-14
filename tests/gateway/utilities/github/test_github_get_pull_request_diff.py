import os
from os import makedirs, path
from pathlib import Path
from shutil import rmtree
from typing import Optional

import httpx
from httpx import Response
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
from language_model_gateway.gateway.utilities.github.github_pull_request_helper import (
    GithubPullRequestHelper,
)
from tests.gateway.mocks.mock_environment_variables import MockEnvironmentVariables
from tests.gateway.mocks.mock_http_client_factory import MockHttpClientFactory


async def test_github_get_pull_request_diff(
    async_client: httpx.AsyncClient, httpx_mock: HTTPXMock
) -> None:
    print()
    data_dir: Path = Path(__file__).parent.joinpath("./")
    temp_folder = data_dir.joinpath("./temp")
    if path.isdir(temp_folder):
        rmtree(temp_folder)
    makedirs(temp_folder)

    test_container: SimpleContainer = await get_container_async()

    if not EnvironmentReader.is_environment_variable_set("RUN_TESTS_WITH_REAL_LLM"):
        org_name: str = "icanbwell"
        access_token: Optional[str] = "fake_token"
        test_container.register(
            EnvironmentVariables, lambda c: MockEnvironmentVariables()
        )
        sample_diff_content = """diff --git a/example.py b/example.py
    index 123456..789012 100644
    --- a/example.py
    +++ b/example.py
    @@ -1,5 +1,5 @@
     def example_function():
    -    print("Old content")
    +    print("New content")
    """

        # Mock the GitHub API responses for PR details and diff
        httpx_mock.add_response(
            url=f"https://api.github.com/repos/{org_name}/language-model-gateway-configuration/pulls/6",
            # url=f"http://test/repos/icanbwell/language-model-gateway-configuration/pulls/6",
            method="GET",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/vnd.github.v3.diff",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "AsyncGithubPullRequestHelper",
            },
            content=sample_diff_content.encode(),
            status_code=200,
        )
        # def foo(request):
        #     return Response(
        #         status_code=200,
        #         headers={"Content-Type": "text/event-stream"},
        #     )
        # httpx_mock.add_callback(
        #     callback=foo,
        #     url="https://api.github.com/repos/icanbwell/language-model-gateway-configuration/pulls/6",
        # )
        # http_client_factory = MockHttpClientFactory(fn_http_client=lambda: async_client)
        # this has to be created again to make httpx_mock work
        my_async_client = httpx.AsyncClient()
        http_client_factory = MockHttpClientFactory(fn_http_client=lambda: my_async_client)
    else:
        # Get credentials from environment variables
        org_name = "icanbwell"  # os.getenv('GITHUB_ORG')
        access_token = os.getenv("GITHUB_TOKEN")

        if not org_name or not access_token:
            raise ValueError(
                "Please set GITHUB_ORG and GITHUB_TOKEN environment variables"
            )

        http_client_factory = HttpClientFactory()

    # Initialize PR counter
    pr_counter = GithubPullRequestHelper(
        org_name=org_name,
        access_token=access_token,
        http_client_factory=http_client_factory,
    )

    try:
        diff: str = await pr_counter.get_pr_diff_content(
            pr_url=f"https://github.com/{org_name}/language-model-gateway-configuration/pull/6/"
        )
        print(diff)

    except Exception as e:
        print(f"An error occurred: {e}")
