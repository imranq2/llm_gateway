from pathlib import Path

from fastapi.testclient import TestClient

from language_model_gateway.utilities.test_runner import run_test_runner


async def test_simple(graphql_client: TestClient) -> None:
    # Arrange
    data_dir: Path = Path(__file__).parent.joinpath("./")

    run_test_runner(
        data_dir=data_dir,
        graphql_client=graphql_client,
        test_name="test_simple",
    )
