import logging
import os
from datetime import datetime
from typing import Type, Optional, List, Tuple, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from language_model_gateway.gateway.utilities.jira.jira_issue import JiraIssue
from language_model_gateway.gateway.utilities.jira.jira_issues_helper import (
    JiraIssueHelper,
)

logger = logging.getLogger(__name__)


class JiraIssuesAnalyzerAgentInput(BaseModel):
    """
    Input model for configuring GitHub Pull Request extraction and analysis.

    IMPORTANT LLM PARSING GUIDANCE:
    - When a query mentions a specific repository, extract the repository name exactly as written
    - When a query includes a GitHub username, extract it as the assigneeName
    - Examples of parsing:
      * "What pull requests from imranq2 in helix.pipelines repo"
        -> projectName = "helix.pipelines"
        -> assigneeName = "imranq2"
      * "Show pull requests for user johndoe in myorg/myrepo"
        -> projectName = "myorg/myrepo"
        -> assigneeName = "johndoe"
      * "Pull requests in kubernetes/kubernetes by banzaicloud"
        -> projectName = "kubernetes/kubernetes"
        -> assigneeName = "banzaicloud"

    Attributes:
        projectName (Optional[str]):
            Specific repository name to analyze.
            PARSING HINT: Directly use the repository name mentioned in the query.
            Can include organization prefix (e.g., "org/repo").
            Example: "helix.pipelines", "kubernetes/kubernetes"

        assigneeName (Optional[str]):
            GitHub username to filter pull requests.
            PARSING HINT: Extract the GitHub username mentioned in the query.
            Example: "imranq2", "johndoe"

        # ... (rest of the attributes remain the same)
    """

    # IMPORTANT: Claude 3.5 Haiku 2024-10-22 has a bug where, when streaming, it changes parameter names to be camelCase
    # Hence use camelCase names for all parameters instead of snake_case

    projectName: Optional[str] = Field(
        default=None,
        description=(
            "Specific project name to analyze. "
            "PARSING INSTRUCTION: Extract exact project name from the query. "
        ),
    )
    assigneeName: Optional[str] = Field(
        default=None,
        description=(
            "Jira username to filter issues. "
            "PARSING INSTRUCTION: Extract Jira username mentioned in the query."
        ),
    )
    minimumCreatedDate: Optional[datetime] = Field(
        default=None,
        # alias="minimumCreatedDate",
        description="Earliest date for issue creation (inclusive)",
    )
    maximumCreatedDate: Optional[datetime] = Field(
        default=None,
        # alias="maximumCreatedDate",
        description="Latest date for issue creation (inclusive)",
    )
    includeDetails: Optional[bool] = Field(
        default=False,
        # alias="includePullRequestDetails",
        description="Include detailed Jira issue information or return user summary",
    )


class JiraIssuesAnalyzerTool(BaseTool):
    """
    A LangChain-compatible tool for comprehensive GitHub pull request analysis.

    This tool provides advanced capabilities for extracting and analyzing
    pull request data from a GitHub organization. It supports:
    - Filtering pull requests by repository, date range, and contributor
    - Generating summary reports of pull request activity
    - Retrieving detailed pull request information

    Key Features:
    - Asynchronous pull request retrieval
    - Configurable analysis scope
    - Detailed or summarized reporting
    - Error handling and logging

    Requires:
    - GitHub access token
    - GITHUB_ORGANIZATION_NAME environment variable

    Example Usage:
    ```python
    tool = JiraIssuesAnalyzerTool(access_token='your_github_token')
    results, artifact = await tool._arun(
        projectName='my-project',
        minimumCreatedDate=datetime(2023, 1, 1),
        includeDetails=True
    )
    ```
    """

    name: str = "github_pull_request_analyzer"
    description: str = (
        "Advanced Jira Issue analysis tool. "
        "USAGE TIPS: "
        "- Specify project with 'in [project]' "
        "- Specify assignee with username "
        "- Example queries: "
        "'Pull issues in EFS', "
        "'Issues assigned to johndoe in EFS', "
        "'What issues assigned to imranq2 in EFS project'"
    )

    args_schema: Type[BaseModel] = JiraIssuesAnalyzerAgentInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    jira_issues_helper: JiraIssueHelper

    # noinspection PyPep8Naming
    def _run(
        self,
        projectName: Optional[str] = None,
        minimumCreatedDate: Optional[datetime] = None,
        maximumCreatedDate: Optional[datetime] = None,
        assigneeName: Optional[str] = None,
        includeDetails: Optional[bool] = None,
    ) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).

        Raises:
            NotImplementedError: Always raises to enforce async usage
        """
        raise NotImplementedError("Use async version of this tool")

    # noinspection PyPep8Naming
    async def _arun(
        self,
        projectName: Optional[str] = None,
        minimumCreatedDate: Optional[datetime] = None,
        maximumCreatedDate: Optional[datetime] = None,
        assigneeName: Optional[str] = None,
        includeDetails: Optional[bool] = None,
    ) -> Tuple[str, str]:
        """
        Asynchronous version of the GitHub Pull Request extraction tool.

        Returns:
            Tuple of pull request analysis text and artifact description
        """

        logger.info(
            "JiraIssuesAnalyzerAgent:"
            + f" {projectName=}, {minimumCreatedDate=}, {maximumCreatedDate=}"
            + f", {assigneeName=}, {includeDetails=}"
        )

        log_prefix: str = (
            "JiraIssuesAnalyzerAgent:"
            + f" {projectName=}, {minimumCreatedDate=}, {maximumCreatedDate=}"
            + f", {assigneeName=}, {includeDetails=}"
        )

        try:
            # Initialize GitHub Pull Request Helper
            # Retrieve closed pull requests
            max_projects: int = int(os.environ.get("GITHUB_MAXIMUM_REPOS", 100))
            max_issues: int = int(
                os.environ.get("GITHUB_MAXIMUM_PULL_REQUESTS_PER_REPO", 100)
            )
            jira_issues: List[JiraIssue] = (
                await self.jira_issues_helper.retrieve_closed_issues(
                    max_projects=max_projects,
                    max_issues=max_issues,
                    min_created_at=minimumCreatedDate,
                    max_created_at=maximumCreatedDate,
                    project_key=projectName,
                )
            )

            full_text: str
            if includeDetails:
                full_text = ""
                for issue in jira_issues:
                    full_text += f"Issue: {issue.summary} status: {issue.status} assigned to {issue.assignee}"
                    f" created on {issue.created_at}\n"
                    f" closed on {issue.closed_at}\n"
            else:
                # Summarize pull requests by engineer
                pr_summary = self.jira_issues_helper.summarize_issues_by_assignee(
                    issues=jira_issues
                )

                # Generate detailed text report
                report_lines = [
                    "Pull Requests by Contributor:",
                ]

                for engineer, info in pr_summary.items():
                    report_lines.append(f"{engineer}: {info.issue_count}")

                full_text = "\n".join(report_lines)

            # Create artifact description
            artifact = log_prefix + f", Analyzed {len(jira_issues)} closed PRs"

            return full_text, artifact

        except Exception as e:
            error_msg = f"Error analyzing GitHub pull requests: {str(e)}"
            error_artifact = log_prefix + " Analysis Failed"
            logger.error(error_msg)
            return error_msg, error_artifact
