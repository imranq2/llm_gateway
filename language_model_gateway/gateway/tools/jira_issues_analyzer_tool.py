import logging
import os
from datetime import datetime
from typing import Type, Optional, List, Tuple, Literal

from pydantic import BaseModel, Field

from language_model_gateway.gateway.tools.resilient_base_tool import ResilientBaseTool
from language_model_gateway.gateway.utilities.jira.jira_issue import JiraIssue
from language_model_gateway.gateway.utilities.jira.jira_issues_helper import (
    JiraIssueHelper,
)

logger = logging.getLogger(__name__)


class JiraIssuesAnalyzerAgentInput(BaseModel):
    """
    Input model for configuring GitHub Pull Request extraction and analysis.
    """

    project_name: Optional[str] = Field(
        default=None,
        description=(
            "Specific project name to analyze. "
            "PARSING INSTRUCTION: Extract exact project name from the query. "
        ),
    )
    assignee: Optional[str] = Field(
        default=None,
        description=(
            "Jira username to filter issues. "
            "PARSING INSTRUCTION: Extract Jira username mentioned in the query."
        ),
    )
    minimum_created_date: Optional[datetime] = Field(
        default=None,
        description="Earliest date for issue creation (inclusive)",
    )
    maximum_created_date: Optional[datetime] = Field(
        default=None,
        description="Latest date for issue creation (inclusive)",
    )
    summary_only: Optional[bool] = Field(
        default=False,
        description="Whether to return just the summary or full issue details",
    )


class JiraIssuesAnalyzerTool(ResilientBaseTool):
    """
    A LangChain-compatible tool for comprehensive GitHub pull request analysis.

    This tool provides advanced capabilities for extracting and analyzing
    pull request data from a GitHub organization. It supports:
    - Filtering issues by project, date range, and contributor
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
        project_name='my-project',
        minimum_created_date=datetime(2023, 1, 1),
        includeDetails=True
    )
    ```
    """

    name: str = "jira_issues_analyzer"
    description: str = (
        "Advanced Jira Issue analysis tool. Set includeDetails if you want detailed issue information. "
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
        project_name: Optional[str] = None,
        minimum_created_date: Optional[datetime] = None,
        maximum_created_date: Optional[datetime] = None,
        assignee: Optional[str] = None,
        summary_only: Optional[bool] = None,
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
        project_name: Optional[str] = None,
        minimum_created_date: Optional[datetime] = None,
        maximum_created_date: Optional[datetime] = None,
        assignee: Optional[str] = None,
        summary_only: Optional[bool] = None,
    ) -> Tuple[str, str]:
        """
        Asynchronous version of the Jira Issues analyzer tool.

        Returns:
            Tuple of Jira issue text and artifact description
        """

        logger.info(
            "JiraIssuesAnalyzerAgent:"
            + f" {project_name=}, {minimum_created_date=}, {maximum_created_date=}"
            + f", {assignee=}, {summary_only=}"
        )

        log_prefix: str = (
            "JiraIssuesAnalyzerAgent:"
            + f" {project_name=}, {minimum_created_date=}, {maximum_created_date=}"
            + f", {assignee=}, {summary_only=}"
        )

        try:
            max_projects: int = int(os.environ.get("JIRA_MAXIMUM_PROJECTS", 100))
            max_issues: int = int(
                os.environ.get("JIRA_MAXIMUM_ISSUES_PER_PROJECT", 100)
            )
            jira_issues: List[JiraIssue] = (
                await self.jira_issues_helper.retrieve_closed_issues(
                    max_projects=max_projects,
                    max_issues=max_issues,
                    min_created_at=minimum_created_date,
                    max_created_at=maximum_created_date,
                    project_key=project_name,
                    assignee=assignee,
                )
            )

            full_text: str
            if not summary_only:
                full_text = ""
                for issue in jira_issues:
                    full_text += f"Issue: {issue.summary} status: {issue.status} assigned to {issue.assignee}"
                    f" created on {issue.created_at}\n"
                    f" closed on {issue.closed_at}\n"
            else:
                # Summarize issues by engineer
                pr_summary = self.jira_issues_helper.summarize_issues_by_assignee(
                    issues=jira_issues
                )

                # Generate detailed text report
                report_lines = [
                    "Issues by Assignee:",
                ]

                for engineer, info in pr_summary.items():
                    report_lines.append(f"{engineer}: {info.issue_count}")

                full_text = "\n".join(report_lines)

            # Create artifact description
            artifact = log_prefix + f", Analyzed {len(jira_issues)} closed issues"

            return full_text, artifact

        except Exception as e:
            error_msg = f"Error analyzing Jira issues: {str(e)}"
            error_artifact = log_prefix + " Analysis Failed"
            logger.error(error_msg)
            return error_msg, error_artifact
