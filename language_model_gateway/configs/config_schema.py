from typing import List, Optional

from pydantic import BaseModel


class PromptConfig(BaseModel):
    """Prompt configuration"""

    role: str = "system"
    """The role of the prompt"""

    content: str | None = None
    """The content of the prompt"""

    hub_id: str | None = None
    """The hub id of the prompt"""

    cache: bool | None = None
    """Whether to cache the prompt"""


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


class AgentParameterConfig(BaseModel):
    """Tool parameter configuration"""

    key: str
    """The key of the parameter"""

    value: str
    """The value of the parameter"""


class AgentConfig(BaseModel):
    """Tool configuration"""

    name: str
    """The name of the tool"""

    parameters: List[AgentParameterConfig] | None = None
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

    type: str = "langchain"
    """The type of model"""

    owner: Optional[str] = None
    """The owner of the model"""

    url: str | None = None
    """The URL to access the model"""

    disabled: bool | None = None

    model: ModelConfig | None = None
    """The model configuration"""

    system_prompts: List[PromptConfig] | None = None
    """The system prompts for the model"""

    model_parameters: List[ModelParameterConfig] | None = None
    """The model parameters"""

    headers: List[HeaderConfig] | None = None
    """The headers to pass to url when calling the model"""

    tools: List[AgentConfig] | None = None
    """The tools to use with the model"""

    agents: List[AgentConfig] | None = None
    """The tools to use with the model"""

    example_prompts: List[PromptConfig] | None = None
    """Example prompts for the model"""

    def get_agents(self) -> List[AgentConfig]:
        """Get the agents for the model"""
        return self.agents or self.tools or []
