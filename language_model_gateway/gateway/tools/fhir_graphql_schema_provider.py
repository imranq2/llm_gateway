from typing import Tuple, Literal
from language_model_gateway.gateway.tools.resilient_base_tool import ResilientBaseTool


class GraphqlSchemaProviderTool(ResilientBaseTool):
    """
    A tool for providing FHIR GraphQL schema.
    """

    name: str = "graphql_query_generator"
    description: str = (
        "This is a FHIR GraphQL schema provider that provides the GraphQL SDL for needed for generating correct query"
        "Example queries: "
        "'Make query for getting all patients with ids 1,2', "
        "'Get conditions for patients whose name is John'"
    )

    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"

    async def _arun(self) -> Tuple[str, str]:
        schema_file = "fhir_graphql_sdl/fhir_graphql_schema.graphql"
        graphql_schema = open(schema_file, "r").read()

        return graphql_schema, "FHIR server graphql schema"

    def _run(self) -> Tuple[str, str]:
        """
        Synchronous version of the tool (falls back to async implementation).

        Raises:
            NotImplementedError: Always raises to enforce async usage
        """
        raise NotImplementedError("Use async version of this tool")
