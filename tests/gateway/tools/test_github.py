import os


from tests.gateway.tools.github_pr_counter import GitHubPRCounter


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
    pr_counter = GitHubPRCounter(org_name, access_token)

    try:
        # Get PR counts with optional parameters
        pr_counts = pr_counter.get_closed_prs_by_engineer(
            max_repos=5,  # Optional: limit repositories
            max_pull_requests=50,  # Optional: limit PRs
            include_merged=True,  # Include merged PRs
        )

        # Export results
        pr_counter.export_results(
            pr_counts, output_file="pr_counts.csv"  # Optional CSV export
        )

    except Exception as e:
        print(f"An error occurred: {e}")
