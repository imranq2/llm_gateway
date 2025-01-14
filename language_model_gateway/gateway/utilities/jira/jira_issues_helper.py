import base64
import logging
from datetime import datetime
from logging import Logger
from typing import Dict, Optional, List, Any

from language_model_gateway.gateway.http.http_client_factory import HttpClientFactory
from language_model_gateway.gateway.utilities.jira.jira_issue import JiraIssue


class JiraIssueHelper:
    def __init__(
        self,
        *,
        http_client_factory: HttpClientFactory,
        jira_base_url: str,
        access_token: Optional[str],
        username: str,
    ):
        """
        Initialize Jira Issue Helper with async rate limit handling.

        Args:
            jira_base_url (str): Base URL of the Jira instance
            access_token (str): Jira API token or personal access token
        """
        self.http_client_factory: HttpClientFactory = http_client_factory
        self.logger: Logger = logging.getLogger(__name__)
        self.jira_base_url: str = jira_base_url.rstrip("/")
        self.jira_access_token: Optional[str] = access_token
        self.username: str = username

        credentials = base64.b64encode(f"{username}:{access_token}".encode()).decode()

        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "AsyncJiraIssueHelper",
        }

    async def retrieve_closed_issues(
        self,
        *,
        max_projects: Optional[int] = None,
        max_issues: Optional[int] = None,
        min_created_at: Optional[datetime] = None,
        max_created_at: Optional[datetime] = None,
        project_key: Optional[str] = None,
    ) -> List[JiraIssue]:
        """
        Async method to retrieve closed issues across Jira projects.

        Args:
            max_projects (int, optional): Maximum number of projects to fetch
            max_issues (int, optional): Maximum number of issues to retrieve
            min_created_at (datetime, optional): Minimum creation date
            max_created_at (datetime, optional): Maximum creation date
            project_key (str, optional): Specific project to fetch issues from

        Returns:
            List[JiraIssue]: List of closed Jira issues
        """
        assert self.jira_base_url, "Jira base URL is required"
        assert self.jira_access_token, "Jira access token is required"

        async with self.http_client_factory.create_http_client(
            base_url=self.jira_base_url, headers=self.headers, timeout=30.0
        ) as client:
            try:
                # Construct JQL (Jira Query Language) based on parameters
                jql_conditions = ["status = Closed"]

                if project_key:
                    jql_conditions.append(f"project = {project_key}")

                if min_created_at:
                    jql_conditions.append(
                        f"created >= '{min_created_at.strftime('%Y-%m-%d')}'"
                    )

                if max_created_at:
                    jql_conditions.append(
                        f"created <= '{max_created_at.strftime('%Y-%m-%d')}'"
                    )

                jql = " AND ".join(jql_conditions)

                # Pagination parameters
                start_at = 0
                max_results = max_issues or 100

                closed_issues_list: List[JiraIssue] = []

                while True:
                    response = await client.get(
                        f"{self.jira_base_url}/rest/api/3/search",
                        params={
                            "jql": jql,
                            "startAt": start_at,
                            "maxResults": max_results,
                            "fields": [
                                "summary",
                                "status",
                                "created",
                                "resolutiondate",
                                "assignee",
                                "project",
                            ],
                        },
                    )
                    response.raise_for_status()

                    issues_data = response.json()

                    for issue in issues_data.get("issues", []):
                        assignee_object: Optional[Dict[str, Any]] = issue["fields"].get(
                            "assignee", {}
                        )
                        assignee: str = (
                            assignee_object.get("displayName", "Unassigned")
                            if assignee_object
                            else "Unassigned"
                        )
                        closed_issues_list.append(
                            JiraIssue(
                                key=issue["key"],
                                summary=issue["fields"].get("summary", "No Summary"),
                                status=issue["fields"]["status"]["name"],
                                created_at=datetime.fromisoformat(
                                    issue["fields"]["created"].replace("Z", "+00:00")
                                ),
                                closed_at=(
                                    datetime.fromisoformat(
                                        issue["fields"]
                                        .get("resolutiondate", "")
                                        .replace("Z", "+00:00")
                                    )
                                    if issue["fields"].get("resolutiondate")
                                    else None
                                ),
                                assignee=assignee,
                                project=issue["fields"].get("project", {}).get("key"),
                            )
                        )

                        if max_issues and len(closed_issues_list) >= max_issues:
                            break

                    # Break if no more issues or max issues reached
                    if (not issues_data.get("issues")) or (
                        max_issues and len(closed_issues_list) >= max_issues
                    ):
                        break

                    start_at += max_results

                return closed_issues_list

            except Exception as e:
                self.logger.error(f"Error retrieving Jira issues: {e}")
                raise

    # noinspection PyMethodMayBeStatic
    def summarize_issues_by_assignee(
        self, *, issues: List[JiraIssue]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Summarize issues by assignee.

        Args:
            issues (List[JiraIssue]): List of Jira issues

        Returns:
            Dict[str, Dict[str, Any]]: Summary of issues by assignee
        """
        assignee_issue_counts: Dict[str, Dict[str, Any]] = {}

        for issue in issues:
            assignee = issue.assignee or "Unassigned"

            if assignee not in assignee_issue_counts:
                assignee_issue_counts[assignee] = {
                    "issue_count": 1,
                    "projects": [issue.project] if issue.project else [],
                }
            else:
                assignee_issue_counts[assignee]["issue_count"] += 1
                if (
                    issue.project
                    and issue.project not in assignee_issue_counts[assignee]["projects"]
                ):
                    assignee_issue_counts[assignee]["projects"].append(issue.project)

        # Sort by issue count
        return dict(
            sorted(
                assignee_issue_counts.items(),
                key=lambda item: item[1]["issue_count"],
                reverse=True,
            )
        )

    def export_results(
        self,
        *,
        issue_counts: Dict[str, Dict[str, Any]],
        output_file: Optional[str] = None,
    ) -> None:
        """
        Export issue count results to console and optional file.

        Args:
            issue_counts (Dict[str, Dict[str, Any]]): Issue counts by assignee
            output_file (Optional[str]): Path to output file
        """
        # Print results to console
        self.logger.info("\n------ Closed Issues by Assignee ------\n")
        for assignee, info in issue_counts.items():
            self.logger.info(f"{assignee} | {info['issue_count']} | {info['projects']}")
        self.logger.info("\n------------------------------------\n")

        # Optional file export
        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write("Assignee\tIssue Count\tProjects\n")
                    for assignee, info in issue_counts.items():
                        projects_text: str = (
                            " | ".join(info["projects"]) if info["projects"] else ""
                        )
                        f.write(f"{assignee}\t{info['issue_count']}\t{projects_text}\n")
                self.logger.info(f"Results exported to {output_file}")
            except IOError as e:
                self.logger.error(f"Failed to export results: {e}")
