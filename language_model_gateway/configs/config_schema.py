from typing import List

from pydantic import BaseModel


class PromptConfig(BaseModel):
    """Prompt configuration"""

    role: str
    """The role of the prompt"""

    content: str | None = None
    """The content of the prompt"""

    hub_id: str | None = None
    """The hub id of the prompt"""


class ModelParameterConfig(BaseModel):
    """Model parameter configuration"""

    key: str
    """The key of the parameter"""

    value: float
    """The value of the parameter"""


class FewShotExampleConfig(BaseModel):
    """Few shot example configuration"""

    input: str
    """The input"""

    output: str
    """The output"""


class HeaderConfig(BaseModel):
    """Header configuration"""

    key: str
    """The key of the header"""

    value: str
    """The value of the header"""


class ToolParameterConfig(BaseModel):
    """Tool parameter configuration"""

    key: str
    """The key of the parameter"""

    value: str
    """The value of the parameter"""


class ToolConfig(BaseModel):
    """Tool configuration"""

    name: str
    """The name of the tool"""

    parameters: List[ToolParameterConfig] | None = None
    """The parameters for the tool"""


class ModelConfig(BaseModel):
    """Model configuration"""

    provider: str
    """The provider of the model"""

    model: str
    """The model to use"""


class ChatModelConfig(BaseModel):
    """Model configuration for chat models"""

    id: str
    """The unique identifier for the model"""

    name: str
    """The name of the model"""

    description: str
    """A description of the model"""

    type: str
    """The type of model"""

    url: str | None = None
    """The URL to access the model"""

    model: ModelConfig | None = None
    """The model configuration"""

    system_prompts: List[PromptConfig] | None = None
    """The prompts for the model"""

    model_parameters: List[ModelParameterConfig] | None = None
    """The model parameters"""

    few_shot_examples: List[FewShotExampleConfig] | None = None
    """The few shot examples"""

    headers: List[HeaderConfig] | None = None
    """The headers to pass to url when calling the model"""

    tools: List[ToolConfig] | None = None
    """The tools to use with the model"""
