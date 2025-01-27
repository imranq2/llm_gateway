import logging
import os
import time
from logging import Logger
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState
from databricks.sdk.types.sql import StatementResponse
import pandas as pd
from pandas.core.frame import DataFrame


class DatabricksHelper:
    def __init__(
        self,
        *,
        workspace_client: WorkspaceClient,
        catalog: str = "bronze",
        schema: str = "fhir_rpt",
    ) -> None:
        # Initialize logger as time, error level, and message
        self.logger: Logger = logging.getLogger(__name__)
        logging.basicConfig(
            format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
        )
        self.ws_client = workspace_client
        self.tables = self.ws_client.tables.list(
            catalog_name=catalog, schema_name=schema
        )

    def parse_databricks_statement_response(
        self, statement_response: StatementResponse
    ) -> pd.DataFrame:
        """
        Simple parser to create a DataFrame from Databricks StatementResponse
        Args:
            statement_response: Databricks StatementResponse object
        Returns:
            Pandas DataFrame with query results
        """
        try:
            # Extract column names
            column_names = [
                column.name for column in statement_response.manifest.schema.columns
            ]
            # Extract data array
            data_array = statement_response.result.data_array
            # Create DataFrame
            df = pd.DataFrame(data_array, columns=column_names)

            return df

        except Exception as e:
            self.logger.error(f"Error parsing Databricks statement response: {e}")
            return None

    def dataframe_to_markdown(self, df: DataFrame) -> str:
        """
        Convert a pandas DataFrame to a markdown-formatted table
        Args:
            df (pandas.DataFrame): Input DataFrame
        Returns:
            str: Markdown-formatted table
        """
        # Create header
        markdown_table = "| " + " | ".join(df.columns) + " |\n"
        # Create separator line
        markdown_table += "| " + " | ".join(["---"] * len(df.columns)) + " |\n"
        # Add rows
        for _, row in df.iterrows():
            markdown_table += "| " + " | ".join(str(val) for val in row) + " |\n"

        return markdown_table

    def execute_query(self, query: str, max_wait_time: int = 300) -> str:
        try:
            # Execute initial statement
            # Handle warehouse_id as an environment variable
            warehouse_id = os.environ.get("DATABRICKS_SQL_WAREHOUSE_ID")
            if not warehouse_id:
                raise ValueError(
                    "DATABRICKS_SQL_WAREHOUSE_ID environment variable not set"
                )
            results = self.ws_client.statement_execution.execute_statement(
                query, warehouse_id=warehouse_id
            )

            # Track start time for timeout
            start_time = time.time()

            # Wait while statement is pending
            while results.status.state == StatementState.PENDING:  # type: ignore
                # Check for timeout
                if time.time() - start_time > max_wait_time:
                    self.logger.error(f"Query timed out after {max_wait_time} seconds")
                    return "Query timed out"

                # Wait before checking again
                time.sleep(1)  # Wait 1 second between checks

                # Refresh the statement status
                results = self.ws_client.statement_execution.get_statement(
                    results.statement_id  # type: ignore
                )

                if results.status.state != StatementState.PENDING:  # type: ignore
                    break

            # Check for failed state
            if results.status.state == StatementState.FAILED:  # type: ignore
                error_message = (
                    results.status.error.message  # type: ignore
                    if results.status.error  # type: ignore
                    else "Unknown error"
                )
                self.logger.error(f"Error executing Databricks query: {error_message}")
                return f"Error executing Databricks query: {error_message}"

            # Log successful execution
            self.logger.info(f"Query executed successfully: {results}")

            # Parse and return results
            df = self.parse_databricks_statement_response(results)
            if df is not None:
                return self.dataframe_to_markdown(df)

            return "Dataframe was None. Unable to parse results"

        except Exception as e:
            self.logger.error(f"Error executing Databricks query: {e}")
            return ""
