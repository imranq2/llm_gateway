import logging
import os
from typing import Type, Literal, Tuple
from uuid import uuid4

from graphviz import Digraph
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from language_model_gateway.gateway.file_managers.file_saver import FileSaver
from language_model_gateway.gateway.utilities.url_parser import UrlParser

logger = logging.getLogger(__name__)


class GraphVizDiagramGeneratorToolInput(BaseModel):
    dot_input: str = Field(
        description="a string describing the nodes and edges in DOT format. "
        "For example:\n"
        "digraph G {\n"
        "  A -> B;\n"
        "  B -> C;\n"
        "  C -> A;\n"
        "}"
    )


class GraphVizDiagramGeneratorTool(BaseTool):
    """
    LangChain-compatible tool for generating a diagram using Graphviz.
    """

    name: str = "graphviz_diagram_generator"
    description: str = (
        "Generate a diagram using Graphviz. "
        "Provide input as a string describing the nodes and edges in DOT format. "
        "For example:\n"
        "digraph G {\n"
        "  A -> B;\n"
        "  B -> C;\n"
        "  C -> A;\n"
        "}"
        "This will generate a directed graph with three nodes: A, B, and C."
    )
    args_schema: Type[BaseModel] = GraphVizDiagramGeneratorToolInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    file_saver: FileSaver

    def _run(self, dot_input: str) -> Tuple[str, str]:
        """
        Run the tool to generate a diagram from DOT input.
        :param dot_input: The DOT description of the graph.
        :return: The path to the generated diagram.
        """
        try:
            # Create a Graphviz object
            dot = Digraph(format="png")
            # Parse the DOT input
            for line in dot_input.strip().split("\n"):
                if "->" in line or "--" in line:
                    # Add edges
                    edge = line.replace(";", "").strip()
                    nodes = edge.split("->" if "->" in edge else "--")
                    dot.edge(nodes[0].strip(), nodes[1].strip())
                elif (
                    line.strip()
                    and not line.startswith("digraph")
                    and not line.endswith("}")
                ):
                    # Add standalone nodes
                    node = line.replace(";", "").strip()
                    dot.node(node)

            # Render the diagram
            image_generation_path_ = os.environ["IMAGE_GENERATION_PATH"]
            assert (
                image_generation_path_
            ), "IMAGE_GENERATION_PATH environment variable is not set"
            image_file_name: str = f"{uuid4()}.png"
            output_file: str = self.file_saver.get_full_path(
                folder=image_generation_path_, filename=image_file_name
            )
            dot.render(output_file, cleanup=True)
            url: str = UrlParser.get_url_for_file_name(output_file)
            return (
                url,
                f"GraphVizDiagramGeneratorTool: Generated diagram from DOT input: <{url}> ",
            )
        except Exception as e:
            raise ValueError(f"Failed to generate diagram: {str(e)}")

    async def _arun(self, dot_input: str) -> Tuple[str, str]:
        """
        Asynchronous version of the tool.
        :param dot_input: The DOT description of the graph.
        :return: The path to the generated diagram.
        """
        # For simplicity, call the synchronous version
        return self._run(dot_input)
