from datetime import datetime, timezone
import os
from typing import Dict

from tests.gateway.tools.github.github_pr_counter import GithubPullRequestTool
from tests.gateway.tools.github.github_pull_request_per_contributor_info import (
    GithubPullRequestPerContributorInfo,
)


def test_github() -> None:
    print()
    # Get credentials from environment variables
    org_name = "icanbwell"  # os.getenv('GITHUB_ORG')
    access_token = os.getenv("GITHUB_TOKEN")

    if not org_name or not access_token:
        raise ValueError("Please set GITHUB_ORG and GITHUB_TOKEN environment variables")

    if not org_name or not access_token:
        raise ValueError("Please set GITHUB_ORG and GITHUB_TOKEN environment variables")

    # Initialize PR counter
    pr_counter = GithubPullRequestTool(org_name, access_token)

    try:
        # Get PR counts with optional parameters
        pr_counts: Dict[str, GithubPullRequestPerContributorInfo] = (
            pr_counter.get_closed_prs_by_engineer(
                max_repos=100,  # Optional: limit repositories
                max_pull_requests=200,  # Optional: limit PRs
                min_created_at=datetime(
                    2024, 9, 1, tzinfo=timezone.utc
                ),  # Optional: minimum created date
                include_merged=True,  # Include merged PRs
            )
        )

        # Export results
        pr_counter.export_results(
            pr_counts, output_file="pr_counts.csv"  # Optional CSV export
        )

    except Exception as e:
        print(f"An error occurred: {e}")
