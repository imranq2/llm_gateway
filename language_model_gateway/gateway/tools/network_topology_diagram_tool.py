import logging
import os
from typing import Type, Literal, Tuple, Optional, List, Dict, Union, Set
from uuid import uuid4

from graphviz import Digraph
from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from language_model_gateway.gateway.file_managers.file_manager import FileManager
from language_model_gateway.gateway.file_managers.file_manager_factory import (
    FileManagerFactory,
)
from language_model_gateway.gateway.utilities.url_parser import UrlParser

logger = logging.getLogger(__name__)


class NetworkTopologyInput(BaseModel):
    """
    Input model for network topology diagram generation

    Example input:
    {
        "nodes": {
            "Internet": {"style": {"shape": "cloud", "color": "lightgray"}},
            "Router": {"style": {"shape": "diamond", "color": "lightblue"}},
            "Switch": {"style": {"shape": "box", "color": "lightgreen"}},
            "Server1": {"style": {"shape": "box3d", "color": "lightcoral"}},
            "Server2": {"style": {"shape": "box3d", "color": "lightyellow"}}
        },
        "connections": [
            {"from": "Internet", "to": "Router", "label": "WAN"},
            {"from": "Router", "to": "Switch", "label": "LAN"},
            {"from": "Switch", "to": "Server1", "label": "eth0"},
            {"from": "Switch", "to": "Server2", "label": "eth1"}
        ],
        "title": "Simple Network Topology"
    }
    """

    nodes: Dict[str, Dict[str, Union[str, Dict[str, str]]]] = Field(
        description='Dictionary of network nodes with optional styling. Example: "Router": {"style": {"shape": "diamond", "color": "lightblue"}}'
    )
    connections: List[Dict[str, str]] = Field(
        description='List of connections between nodes. Example: {"from": "Router", "to": "Switch", "label": "LAN"}'
    )
    title: Optional[str] = Field(
        default=None, description="Optional title for the network topology diagram"
    )


class NetworkTopologyGeneratorTool(BaseTool):
    """
    LangChain-compatible tool for generating network topology diagrams using Graphviz
    """

    name: str = "network_topology_generator"
    description: str = (
        "Generate a network topology diagram using Graphviz. "
        "Provide nodes and their connections. "
        "Example:\n"
        "nodes: {"
        "  'Internet': {'style': {'shape': 'cloud', 'color': 'lightgray'}},"
        "  'Router': {'style': {'shape': 'diamond', 'color': 'lightblue'}}"
        "}\n"
        "connections: ["
        "  {'from': 'Internet', 'to': 'Router', 'label': 'WAN'},"
        "  {'from': 'Router', 'to': 'Switch', 'label': 'LAN'}"
        "]"
    )
    args_schema: Type[BaseModel] = NetworkTopologyInput
    response_format: Literal["content", "content_and_artifact"] = "content_and_artifact"
    file_manager_factory: FileManagerFactory

    def _run(
        self,
        nodes: Dict[str, Dict[str, Union[str, Dict[str, str]]]],
        connections: List[Dict[str, str]],
        title: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Synchronous method (not implemented)
        """
        raise NotImplementedError("Call the asynchronous version of the tool")

    async def _arun(
        self,
        nodes: Dict[str, Dict[str, Union[str, Dict[str, str]]]],
        connections: List[Dict[str, str]],
        title: Optional[str] = None,
    ) -> Tuple[str, str]:
        """
        Asynchronous method to generate a network topology diagram
        """
        try:
            # Create a Graphviz Digraph for the network topology
            dot = Digraph(
                "network_topology",
                filename="network_topology",
                node_attr={"style": "filled", "color": "lightblue"},
            )

            # Set graph attributes
            dot.attr(rankdir="TB")  # Top to Bottom layout

            # Add title if provided
            if title:
                dot.attr(label=title, labelloc="t", fontsize="16")

            # Determine which nodes are actually used in connections
            connected_nodes: Set[str] = set()
            for connection in connections:
                connected_nodes.add(connection["from"])
                connected_nodes.add(connection["to"])

            # Add only connected nodes with custom styling
            for node_name in connected_nodes:
                # Default style
                node_style = {
                    "shape": "box",
                    "color": "lightblue",
                    "style": "filled",
                    "fontcolor": "black",
                }

                # Update with custom style if provided
                if node_name in nodes and "style" in nodes[node_name]:
                    custom_style = nodes[node_name]["style"]
                    # Node shape mapping for network topology
                    node_shapes = {
                        "cloud": "ellipse",
                        "router": "diamond",
                        "switch": "box",
                        "server": "box3d",
                        "firewall": "hexagon",
                        "default": "circle",
                    }

                    # Determine shape based on custom or default
                    shape_key = custom_style.get("shape", "default").lower()  # type: ignore[union-attr]
                    shape = node_shapes.get(shape_key, node_shapes["default"])

                    node_style.update(
                        {
                            "shape": shape,
                            "color": custom_style.get("color", node_style["color"]),  # type: ignore[union-attr]
                            "style": custom_style.get("style", node_style["style"]),  # type: ignore[union-attr]
                            "fontcolor": custom_style.get(  # type: ignore[union-attr]
                                "font_color", node_style["fontcolor"]
                            ),
                        }
                    )

                # Add node with styling
                dot.node(
                    node_name,
                    node_name,
                    shape=node_style["shape"],
                    color=node_style["color"],
                    style=node_style["style"],
                    fontcolor=node_style["fontcolor"],
                )

            # Add connections
            for connection in connections:
                dot.edge(
                    connection["from"],
                    connection["to"],
                    label=connection.get("label", ""),
                    color=connection.get("color", "black"),
                )

            # Render the diagram to bytes
            image_data: bytes = dot.pipe(format="png")

            # Generate a unique filename
            image_file_name: str = f"{uuid4()}.png"

            # Use file manager to save the file (if needed)
            image_generation_path_ = os.environ.get("IMAGE_GENERATION_PATH", "/tmp")
            file_manager: FileManager = self.file_manager_factory.get_file_manager(
                folder=image_generation_path_
            )

            # Attempt to save the file
            file_path: Optional[str] = await file_manager.save_file_async(
                image_data=image_data,
                folder=image_generation_path_,
                filename=image_file_name,
            )
            if file_path is None:
                return (
                    f"Failed to save image to disk",
                    f"NetworkTopologyGeneratorTool: Failed to save image to disk ",
                )

            # Generate URL for the image
            url: Optional[str] = UrlParser.get_url_for_file_name(image_file_name)
            if url is None:
                return (
                    f"Failed to save image to disk",
                    f"NetworkTopologyGeneratorTool: Failed to save image to disk",
                )

            # Return the image bytes and a description
            return (
                url,
                f"NetworkTopologyGeneratorTool: Generated network topology diagram <{url}> ",
            )

        except Exception as e:
            logger.error(f"Failed to generate network topology diagram: {str(e)}")
            raise ValueError(f"Failed to generate network topology diagram: {str(e)}")
