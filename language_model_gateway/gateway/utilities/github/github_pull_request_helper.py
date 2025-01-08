from datetime import datetime
from logging import Logger
from urllib.parse import urlparse

import requests
import re
from github import Github, RateLimitExceededException
from github.GithubException import GithubException
from typing import Dict, Optional, List, cast
import time
import logging
import backoff
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.Repository import Repository
from requests import Response

from language_model_gateway.gateway.utilities.github.github_pull_request import (
    GithubPullRequest,
)
from language_model_gateway.gateway.utilities.github.github_pull_request_per_contributor_info import (
    GithubPullRequestPerContributorInfo,
)


class GithubPullRequestHelper:
    def __init__(self, org_name: str, access_token: str):
        """
        Initialize GitHub PR Counter with rate limit handling.

        Args:
            org_name (str): GitHub organization name
            access_token (str): GitHub Personal Access Token
        """
        self.logger: Logger = logging.getLogger(__name__)
        self.org_name = org_name
        self.github_access_token = access_token
        assert access_token
        self.github_client: Github = Github(access_token)

    @backoff.on_exception(
        backoff.expo, (RateLimitExceededException, GithubException), max_tries=5
    )
    def _get_rate_limit_info(self) -> Dict[str, int]:
        """
        Retrieve and log GitHub API rate limit information.

        Returns:
            Dict[str, int]: Rate limit details
        """
        rate_limit = self.github_client.get_rate_limit()
        remaining = rate_limit.core.remaining
        reset_time = rate_limit.core.reset

        # self.logger.info(f"Rate Limit Remaining: {remaining}")
        # self.logger.info(f"Rate Limit Reset Time: {reset_time}")

        return {"remaining": remaining, "reset_time": int(reset_time.timestamp())}

    def _wait_for_rate_limit_reset(self, reset_time: int) -> None:
        """
        Wait until rate limit resets.

        Args:
            reset_time (int): Timestamp when rate limit will reset
        """
        current_time = int(time.time())
        wait_time = max(reset_time - current_time + 5, 0)

        if wait_time > 0:
            self.logger.warning(f"Rate limit exceeded. Waiting {wait_time} seconds.")
            time.sleep(wait_time)

    def retrieve_closed_prs(
        self,
        *,
        max_repos: Optional[int] = None,
        max_pull_requests: Optional[int] = None,
        min_created_at: Optional[datetime] = None,
        max_created_at: Optional[datetime] = None,
        include_merged: bool = True,
        repo_name: Optional[str] = None,
    ) -> List[GithubPullRequest]:
        """
        Retrieve closed pull requests across organization repositories.

        Args:
            max_repos (Optional[int]): Limit number of repositories to process
            max_pull_requests (Optional[int]): Limit number of pull requests to process
            min_created_at (Optional[datetime]): Minimum created date for PRs
            max_created_at (Optional[datetime]): Maximum created date for PRs
            include_merged (bool): Include merged PRs in count
            repo_name (Optional[str]): filter by repo name

        Returns:
            List[Tuple[PullRequest, Repository]]: List of pull requests with their repositories
        """
        # Validate and get organization
        try:
            org = self.github_client.get_organization(self.org_name)
        except Exception as e:
            self.logger.error(f"Failed to access organization: {e}")
            raise

        # Initialize tracking variables
        closed_prs_list: List[GithubPullRequest] = []

        if repo_name is not None:
            repo: Repository = org.get_repo(name=repo_name)
            closed_prs_list = self.get_pull_requests_from_repo(
                include_merged=include_merged,
                max_created_at=max_created_at,
                max_pull_requests=max_pull_requests,
                min_created_at=min_created_at,
                repo=repo,
            )
        else:
            repos: PaginatedList[Repository] = org.get_repos(
                type="private", sort="updated", direction="desc"
            )

            repo_count: int = repos.totalCount
            self.logger.info(f"====== Processing {repo_count} repositories =======")

            # Iterate through repositories
            for repo in repos:
                # Optional repository limit
                if max_repos and len(closed_prs_list) >= max_repos:
                    break

                closed_prs_list.extend(
                    self.get_pull_requests_from_repo(
                        include_merged=include_merged,
                        max_created_at=max_created_at,
                        max_pull_requests=max_pull_requests,
                        min_created_at=min_created_at,
                        repo=repo,
                    )
                )

        return closed_prs_list

    def get_pull_requests_from_repo(
        self,
        *,
        max_pull_requests: Optional[int] = None,
        min_created_at: Optional[datetime] = None,
        max_created_at: Optional[datetime] = None,
        include_merged: bool = True,
        repo: Repository,
    ) -> List[GithubPullRequest]:
        closed_prs_list: List[GithubPullRequest] = []
        try:
            # Check rate limit before processing
            rate_info: Dict[str, int] = self._get_rate_limit_info()
            if rate_info["remaining"] < 10:
                self._wait_for_rate_limit_reset(rate_info["reset_time"])

            self.logger.info(
                f"\n---------- Processing repository {repo.name} -----------\n"
            )

            # Fetch closed pull requests
            closed_prs: PaginatedList[PullRequest] = repo.get_pulls(
                state="closed", sort="updated", direction="desc"
            )

            # Collect PRs by engineer
            pr_index: int
            pr: PullRequest
            for pr_index, pr in enumerate(closed_prs):
                if max_pull_requests and pr_index >= max_pull_requests:
                    self.logger.info(f"Max pull requests reached for {repo.name}")
                    break
                if min_created_at and pr.created_at < min_created_at:
                    self.logger.info(f"Min created date reached for {repo.name}")
                    break
                if not max_created_at or pr.created_at <= max_created_at:
                    # Filter PRs based on merge status
                    if (include_merged and pr.merged) or pr.state == "closed":
                        closed_prs_list.append(
                            GithubPullRequest(
                                repo=repo.name,
                                title=pr.title,
                                closed_at=pr.closed_at,
                                html_url=pr.html_url,
                                user=pr.user.login,
                            )
                        )
                        self.logger.debug(
                            f"{pr.user.login} | {pr.title} | {pr.closed_at} | {pr.html_url}"
                        )

            self.logger.info(
                f"\n--------- Finished Processed repository: {repo.name} ----------\n"
            )

        except RateLimitExceededException:
            rate_info = self._get_rate_limit_info()
            self._wait_for_rate_limit_reset(rate_info["reset_time"])

        except Exception as e:
            self.logger.error(f"Error processing repository {repo.name}: {e}")

        return closed_prs_list

    # noinspection PyMethodMayBeStatic
    def summarize_prs_by_engineer(
        self, *, pull_requests: List[GithubPullRequest]
    ) -> Dict[str, GithubPullRequestPerContributorInfo]:
        """
        Summarize pull requests by engineer.

        Args:
            pull_requests (List[GithubPullRequest]): List of pull requests with their repositories

        Returns:
            Dict[str, GithubPullRequestPerContributorInfo]: Summary of PRs by engineer
        """
        engineer_pr_counts: Dict[str, GithubPullRequestPerContributorInfo] = {}

        pr: GithubPullRequest
        for pr in pull_requests:
            engineer = pr.user
            info = engineer_pr_counts.get(engineer)

            if info is None:
                engineer_pr_counts[engineer] = GithubPullRequestPerContributorInfo(
                    contributor=engineer,
                    pull_request_count=1,
                    repos=[pr.repo],
                )
            else:
                info.pull_request_count += 1
                if info.repos:
                    if pr.repo not in info.repos:
                        info.repos.append(pr.repo)
                else:
                    info.repos = [pr.repo]

        # Sort engineer_pr_counts by PR count
        return dict(
            sorted(
                engineer_pr_counts.items(),
                key=lambda item: item[1].pull_request_count,
                reverse=True,
            )
        )

    # noinspection PyMethodMayBeStatic
    def parse_pr_url(self, pr_url: str) -> dict[str, str | int]:
        """
        Parse GitHub PR URL to extract repository and PR details.

        Args:
            pr_url (str): Full GitHub PR URL

        Returns:
            Dict containing owner, repo, and PR number

        Raises:
            ValueError: If URL is not a valid GitHub PR URL
        """
        parsed_url = urlparse(pr_url)

        # Support both github.com and GitHub Enterprise URLs
        if not (
            parsed_url.netloc in ["github.com", "www.github.com"]
            or ".githubenterprise.com" in parsed_url.netloc
        ):
            raise ValueError("Invalid GitHub URL")

        # Regex to match GitHub PR URL pattern
        match = re.match(r"/([^/]+)/([^/]+)/pull/(\d+)", parsed_url.path)

        if not match:
            raise ValueError("Invalid GitHub PR URL format")

        return {
            "owner": match.group(1),
            "repo": match.group(2),
            "pr_number": int(match.group(3)),
        }

    def get_pr_diff(self, pr_url: str) -> str:
        """
        Fetch the diff for a given GitHub PR URL.

        Args:
            pr_url (str): Full GitHub PR URL

        Returns:
            str: The diff content of the PR

        Raises:
            ValueError: For URL parsing errors
            GithubException: For GitHub API related errors
        """
        try:
            # Parse the PR URL
            pr_details: Dict[str, str | int] = self.parse_pr_url(pr_url)

            # Get the repository
            repo = self.github_client.get_repo(
                f"{pr_details['owner']}/{pr_details['repo']}"
            )

            # Get the pull request
            pr_number: int = cast(int, pr_details["pr_number"])
            pull_request: PullRequest = repo.get_pull(pr_number)

            # Fetch and return the diff
            return pull_request.diff_url

        except GithubException as e:
            print(f"GitHub API Error: {e}")
            raise
        except Exception as e:
            print(f"Error fetching PR diff: {e}")
            raise

    def get_pr_diff_content(self, pr_url: str) -> str:
        """
        Fetch the actual diff content for a given GitHub PR URL.

        Args:
            pr_url (str): Full GitHub PR URL

        Returns:
            str: The raw diff content of the PR
        """
        try:
            # Parse the PR URL
            pr_details: Dict[str, str | int] = self.parse_pr_url(pr_url)

            # Get the repository
            repo = self.github_client.get_repo(
                f"{pr_details['owner']}/{pr_details['repo']}"
            )

            # Get the pull request
            pr_number: int = cast(int, pr_details["pr_number"])
            pull_request: PullRequest = repo.get_pull(pr_number)

            # Prepare headers for authenticated request
            headers: Dict[str, str] = {
                "Accept": "application/vnd.github.v3.diff",
                "User-Agent": "PyGithub-PR-Diff-Fetcher",
            }

            # Add authentication if token is available
            if self.github_access_token:
                headers["Authorization"] = f"token {self.github_access_token}"

            # Make authenticated request to diff URL
            diff_response: Response = requests.get(
                pull_request.diff_url, headers=headers
            )

            # Raise an exception for bad responses
            diff_response.raise_for_status()

            return diff_response.text

        except requests.RequestException as e:
            print(f"Request Error: {e}")
            # If possible, include response text for debugging
            if hasattr(e, "response") and e.response:
                print(f"Response content: {e.response.text}")
            raise
        except GithubException as e:
            print(f"GitHub API Error: {e}")
            raise
        except Exception as e:
            print(f"Error fetching PR diff: {e}")
            raise

    def export_results(
        self,
        pr_counts: Dict[str, GithubPullRequestPerContributorInfo],
        output_file: Optional[str] = None,
    ) -> None:
        """
        Export PR count results to console and optional file.

        Args:
            pr_counts (Dict[str, int]): PR counts by engineer
            output_file (Optional[str]): Path to output file
        """
        # Print results to console
        self.logger.info("\n------ Closed PRs by Engineer ------\n")
        for engineer, info in pr_counts.items():
            self.logger.info(f"{engineer} | {info.pull_request_count} | {info.repos}")
        self.logger.info("\n------------------------------------\n")

        # Optional file export
        if output_file:
            try:
                with open(output_file, "w") as f:
                    f.write("Contributor\tPR Count\tRepos\n")
                    for engineer, info in pr_counts.items():
                        repos_text: str = " | ".join(info.repos) if info.repos else ""
                        f.write(
                            f"{engineer}\t{info.pull_request_count}\t{repos_text}\n"
                        )
                self.logger.info(f"Results exported to {output_file}")
            except IOError as e:
                self.logger.error(f"Failed to export results: {e}")
