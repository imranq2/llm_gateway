from datetime import datetime

from github import Github, RateLimitExceededException
from github.GithubException import GithubException
from typing import Dict, Optional
import time
import logging
import backoff
from github.PaginatedList import PaginatedList
from github.PullRequest import PullRequest
from github.Repository import Repository

from tests.gateway.tools.github.github_pull_request_per_contributor_info import (
    GithubPullRequestPerContributorInfo,
)


class GithubPullRequestTool:
    def __init__(self, org_name: str, access_token: str):
        """
        Initialize GitHub PR Counter with rate limit handling.

        Args:
            org_name (str): GitHub organization name
            access_token (str): GitHub Personal Access Token
        """
        self.logger = self._setup_logger()
        self.org_name = org_name
        self.access_token = access_token
        assert access_token
        self.github_client = Github(access_token)

    def _setup_logger(self) -> logging.Logger:
        """
        Set up a logger for tracking operations and errors.

        Returns:
            logging.Logger: Configured logger instance
        """
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        return logging.getLogger(__name__)

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

    def get_closed_prs_by_engineer(
        self,
        *,
        max_repos: Optional[int] = None,
        max_pull_requests: Optional[int] = None,
        min_created_at: Optional[datetime] = None,
        max_created_at: Optional[datetime] = None,
        include_merged: bool = True,
    ) -> Dict[str, GithubPullRequestPerContributorInfo]:
        """
        Retrieve count of closed PRs by engineer across organization repositories.

        Args:
            max_repos (Optional[int]): Limit number of repositories to process
            max_pull_requests (Optional[int]): Limit number of pull requests to process
            min_created_at (Optional[datetime]): Minimum created date for PRs
            max_created_at (Optional[datetime]): Maximum created date for PRs
            include_merged (bool): Include merged PRs in count

        Returns:
            Dict[str, int]: Dictionary of engineers and their closed PR counts
        """
        # Validate and get organization
        try:
            org = self.github_client.get_organization(self.org_name)
        except Exception as e:
            self.logger.error(f"Failed to access organization: {e}")
            raise

        # Initialize tracking variables
        engineer_pr_counts: Dict[str, GithubPullRequestPerContributorInfo] = {}
        processed_repos = 0

        repos: PaginatedList[Repository] = org.get_repos(
            type="private", sort="updated", direction="desc"
        )
        repo_count: int = repos.totalCount
        self.logger.info(f"====== Processing {repo_count} repositories =======")

        # Iterate through repositories
        for repo in repos:
            # Optional repository limit
            if max_repos and processed_repos >= max_repos:
                break

            try:
                # Check rate limit before processing
                rate_info: Dict[str, int] = self._get_rate_limit_info()
                if rate_info["remaining"] < 10:
                    self._wait_for_rate_limit_reset(rate_info["reset_time"])

                print(f"\n---------- Processing repository {repo.name} -----------\n")

                # Fetch closed pull requests
                closed_prs: PaginatedList[PullRequest] = repo.get_pulls(
                    state="closed", sort="updated", direction="desc"
                )

                # Count PRs by engineer
                pr_index: int
                pr: PullRequest
                for pr_index, pr in enumerate(closed_prs):
                    if max_pull_requests and pr_index >= max_pull_requests:
                        print(f"Max pull requests reached for {repo.name}")
                        break
                    if min_created_at and pr.created_at < min_created_at:
                        print(f"Min created date reached for {repo.name}")
                        break
                    if not max_created_at or pr.created_at <= max_created_at:
                        # Filter PRs based on merge status
                        if (include_merged and pr.merged) or pr.state == "closed":
                            engineer = pr.user.login
                            info = engineer_pr_counts.get(engineer)
                            if info is None:
                                engineer_pr_counts[engineer] = (
                                    GithubPullRequestPerContributorInfo(
                                        contributor=engineer,
                                        pull_request_count=1,
                                        repos=[repo.name],
                                    )
                                )
                            else:
                                info.pull_request_count += 1
                                if info.repos:
                                    if repo.name not in info.repos:
                                        info.repos.append(repo.name)
                                else:
                                    info.repos = [repo.name]

                            print(
                                f"{engineer} | {pr.title} | {pr.closed_at} | {pr.html_url}"
                            )

                processed_repos += 1
                self.logger.info(
                    f"\n--------- Finished Processed repository: {repo.name} ----------\n"
                )

            except RateLimitExceededException:
                rate_info = self._get_rate_limit_info()
                self._wait_for_rate_limit_reset(rate_info["reset_time"])
                continue

            except Exception as e:
                self.logger.error(f"Error processing repository {repo.name}: {e}")
                continue

        # sort engineer_pr_counts by PR count
        engineer_pr_counts = dict(
            sorted(
                engineer_pr_counts.items(),
                key=lambda item: item[1].pull_request_count,
                reverse=True,
            )
        )
        return engineer_pr_counts

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
        print("\n------ Closed PRs by Engineer ------\n")
        for engineer, info in pr_counts.items():
            print(f"{engineer} | {info.pull_request_count} | {info.repos}")
        print("\n------------------------------------\n")

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
