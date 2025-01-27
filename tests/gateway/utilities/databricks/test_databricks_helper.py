import pytest
import pandas as pd
from unittest.mock import Mock, patch
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import (
    StatementState,
    StatementStatus,
    ColumnInfo,
    ResultSchema,
)
from language_model_gateway.gateway.utilities.databricks.databricks_helper import (
    DatabricksHelper,
)


# Fixture for creating a mock WorkspaceClient
@pytest.fixture
def mock_workspace_client() -> Mock:
    return Mock(spec=WorkspaceClient)


# Fixture for creating a DatabricksHelper instance
@pytest.fixture
def databricks_helper(mock_workspace_client: Mock) -> DatabricksHelper:
    return DatabricksHelper(workspace_client=mock_workspace_client)


# Test parse_databricks_statement_response
def test_parse_databricks_statement_response() -> None:
    # Create a mock statement response
    mock_response = Mock(
        manifest=Mock(
            schema=ResultSchema(
                columns=[ColumnInfo(name="id"), ColumnInfo(name="name")]
            )
        ),
        result=Mock(data_array=[[1, "John"], [2, "Jane"]]),
    )

    # Create helper instance
    helper = DatabricksHelper(workspace_client=Mock())

    # Parse response
    df = helper.parse_databricks_statement_response(mock_response)

    # Assertions
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert list(df.columns) == ["id", "name"]
    assert df.iloc[0, 0] == 1
    assert df.iloc[0, 1] == "John"


# Test dataframe_to_markdown
def test_dataframe_to_markdown() -> None:
    # Create a sample DataFrame
    df = pd.DataFrame({"id": [1, 2], "name": ["John", "Jane"]})

    # Create helper instance
    helper = DatabricksHelper(workspace_client=Mock())

    # Convert to markdown
    markdown = helper.dataframe_to_markdown(df)

    # Assertions
    assert "| id | name |" in markdown
    assert "| --- | --- |" in markdown
    assert "| 1 | John |" in markdown
    assert "| 2 | Jane |" in markdown


# Test execute_query - Successful Scenario
@patch("os.environ.get")
def test_execute_query_success(
    mock_env_get: Mock, databricks_helper: DatabricksHelper, mock_workspace_client: Mock
) -> None:
    # Mock environment variable
    mock_env_get.return_value = "test_warehouse_id"

    # Create mock successful statement response
    mock_response = Mock(
        statement_id="test_statement_id",
        status=StatementStatus(state=StatementState.SUCCEEDED),
        manifest=Mock(schema=ResultSchema(columns=[ColumnInfo(name="id")])),
        result=Mock(data_array=[[1], [2]]),
    )

    # Configure mock workspace client
    mock_workspace_client.statement_execution.execute_statement.return_value = (
        mock_response
    )

    # Execute query
    result = databricks_helper.execute_query("SELECT * FROM test_table")

    # Assertions
    assert "| id |" in result
    assert "| 1 |" in result
    assert "| 2 |" in result


def test_execute_query_pending(
    databricks_helper: DatabricksHelper,
    mock_workspace_client: Mock,
) -> None:
    # Patch environment variable
    with patch("os.environ.get", return_value="test_warehouse_id"):
        # Patch time to control timeout logic
        with patch("time.time", side_effect=[0, 1, 2]):
            # Patch sleep to prevent actual waiting
            with patch("time.sleep"):
                # Create mock pending and then successful statement response
                pending_response = Mock(
                    statement_id="test_statement_id",
                    status=StatementStatus(state=StatementState.PENDING),
                )

                successful_response = Mock(
                    statement_id="test_statement_id",
                    status=StatementStatus(state=StatementState.SUCCEEDED),
                    manifest=Mock(schema=ResultSchema(columns=[ColumnInfo(name="id")])),
                    result=Mock(data_array=[[1], [2]]),
                )

                # Configure mock workspace client to return pending then successful response
                mock_workspace_client.statement_execution.execute_statement.return_value = (
                    pending_response
                )
                mock_workspace_client.statement_execution.get_statement.side_effect = [
                    pending_response,
                    successful_response,
                ]

                # Patch logger to prevent logging issues
                with patch.object(databricks_helper.logger, "info"), patch.object(
                    databricks_helper.logger, "error"
                ):
                    # Execute query
                    result = databricks_helper.execute_query("SELECT * FROM test_table")

                    # Print debug information
                    print(
                        "Get statement call count:",
                        mock_workspace_client.statement_execution.get_statement.call_count,
                    )
                    print(
                        "Execute statement call count:",
                        mock_workspace_client.statement_execution.execute_statement.call_count,
                    )

                    # Assertions
                    assert (
                        mock_workspace_client.statement_execution.get_statement.call_count
                        == 2
                    ), "get_statement should be called only twice"
                    assert result is not None
                    mock_workspace_client.statement_execution.execute_statement.assert_called_once()


# Test execute_query - Timeout Scenario
def test_execute_query_timeout(
    databricks_helper: DatabricksHelper, mock_workspace_client: Mock
) -> None:
    # Patch multiple dependencies
    with patch("os.environ.get", return_value="test_warehouse_id"), patch(
        "time.time", side_effect=[0, 3]
    ), patch("time.sleep"), patch.object(
        databricks_helper.logger, "info"
    ), patch.object(
        databricks_helper.logger, "error"
    ):
        # Create mock pending statement response
        pending_response = Mock(
            statement_id="test_statement_id",
            status=StatementStatus(state=StatementState.PENDING),
        )

        # Configure mock workspace client
        mock_workspace_client.statement_execution.execute_statement.return_value = (
            pending_response
        )
        mock_workspace_client.statement_execution.get_statement.return_value = (
            pending_response
        )

        # Add print statements or logging for debugging
        print("Before execute_query")

        # Execute query with short timeout
        result = databricks_helper.execute_query(
            "SELECT * FROM test_table", max_wait_time=1
        )

        # Print debug information
        print("Result:", result)
        print(
            "Execute statement call count:",
            mock_workspace_client.statement_execution.execute_statement.call_count,
        )

        # Assertions
        assert result == "Query timed out"
        mock_workspace_client.statement_execution.execute_statement.assert_called_once()


# Test execute_query - Failed State Scenario
@patch("os.environ.get")
def test_execute_query_failed_state(
    mock_env_get: Mock, databricks_helper: DatabricksHelper, mock_workspace_client: Mock
) -> None:
    # Mock environment variable
    mock_env_get.return_value = "test_warehouse_id"

    # Create mock failed statement response
    failed_response = Mock(
        statement_id="test_statement_id",
        status=StatementStatus(
            state=StatementState.FAILED, error=Mock(message="Test error message")
        ),
    )

    # Configure mock workspace client
    mock_workspace_client.statement_execution.execute_statement.return_value = (
        failed_response
    )

    # Execute query
    result = databricks_helper.execute_query(
        "SELECT * FROM test_table", max_wait_time=10
    )

    # Assertions
    assert result == "Error executing Databricks query: Test error message"
    mock_workspace_client.statement_execution.execute_statement.assert_called_once()
