import logging
import os
from datetime import datetime
from typing import Type, Optional, List, Tuple, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from language_model_gateway.gateway.utilities.github.github_pull_request import (
    GithubPullRequest,
)
from language_model_gateway.gateway.utilities.github.github_pull_request_helper import (
    GithubPullRequestHelper,
)

logger = logging.getLogger(__name__)


class GitHubPullRequestToolInput(BaseModel):
    """Input model for GitHub Pull Request extraction tool."""

    repository_name: Optional[str] = Field(
        default=None,
        description="Optional specific repository name within the organization",
    )
    minimum_created_date: Optional[datetime] = Field(
        default=None, description="Minimum creation date for pull requests"
    )
    maximum_created_date: Optional[datetime] = Field(
        default=None, description="Maximum creation date for pull requests"
    )
    contributor_name: Optional[str] = Field(
        default=None,
        description="Optional specific contributor name to filter pull requests",
    )
    include_pull_request_details: Optional[bool] = Field(
        default=None,
        description="Include detailed pull request information otherwise we return only counts per contributor",
    )


class GitHubPullRequestAnalyzerTool(BaseTool):
    """
    LangChain-compatible tool for extracting and analyzing GitHub pull requests.
    """

    name: str = "github_pull_request_analyzer"
    description: str = (
        "Retrieves and analyzes pull requests from a GitHub organization. "
        "Provides detailed insights into pull request activity."
    )

    args_schema: Type[BaseModel] = GitHubPullRequestToolInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    access_token: Optional[str]

    def _run(
        self,
        repository_name: Optional[str] = None,
        minimum_created_date: Optional[datetime] = None,
        maximum_created_date: Optional[datetime] = None,
        contributor_name: Optional[str] = None,
        include_pull_request_details: Optional[bool] = None,
    ) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).

        Raises:
            NotImplementedError: Always raises to enforce async usage
        """
        raise NotImplementedError("Use async version of this tool")

    async def _arun(
        self,
        repository_name: Optional[str] = None,
        minimum_created_date: Optional[datetime] = None,
        maximum_created_date: Optional[datetime] = None,
        contributor_name: Optional[str] = None,
        include_pull_request_details: Optional[bool] = None,
    ) -> Tuple[str, str]:
        """
        Asynchronous version of the GitHub Pull Request extraction tool.

        Returns:
            Tuple of pull request analysis text and artifact description
        """

        assert self.access_token, "GitHub access token is required"

        try:
            # Initialize GitHub Pull Request Helper
            github_organization = os.environ.get("GITHUB_ORGANIZATION_NAME")
            assert (
                github_organization
            ), "GITHUB_ORGANIZATION_NAME environment variable is not set"

            gh_helper = GithubPullRequestHelper(
                org_name=github_organization, access_token=self.access_token
            )

            # Retrieve closed pull requests
            max_repos: int = int(os.environ.get("GITHUB_MAXIMUM_REPOS", 100))
            max_pull_requests: int = int(
                os.environ.get("GITHUB_MAXIMUM_PULL_REQUESTS_PER_REPO", 100)
            )
            closed_prs: List[GithubPullRequest] = await gh_helper.retrieve_closed_prs(
                max_repos=max_repos,
                max_pull_requests=max_pull_requests,
                min_created_at=minimum_created_date,
                max_created_at=maximum_created_date,
                include_merged=True,
                repo_name=repository_name,
            )

            full_text: str
            if include_pull_request_details:
                full_text = ""
                for pr in closed_prs:
                    full_text += f"PR: {pr.title} by {pr.user} closed on {pr.closed_at} - {pr.html_url}\n"
            else:
                # Summarize pull requests by engineer
                pr_summary = gh_helper.summarize_prs_by_engineer(
                    pull_requests=closed_prs
                )

                # Generate detailed text report
                report_lines = [
                    "Pull Requests by Contributor:",
                ]

                for engineer, info in pr_summary.items():
                    report_lines.append(f"{engineer}: {info.pull_request_count}")

                full_text = "\n".join(report_lines)

            # Create artifact description
            artifact = f"GitHubPullRequestTool: Analyzed {len(closed_prs)} closed PRs "

            return full_text, artifact

        except Exception as e:
            error_msg = f"Error analyzing GitHub pull requests: {str(e)}"
            error_artifact = "GitHubPullRequestTool: Analysis failed"
            logger.error(error_msg)
            return error_msg, error_artifact
