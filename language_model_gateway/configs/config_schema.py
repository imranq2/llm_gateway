from typing import List

from pydantic import BaseModel


class PromptConfig(BaseModel):
    role: str
    content: str | None = None
    hub_id: str | None = None


class ModelParameterConfig(BaseModel):
    key: str
    value: float


class FewShotExampleConfig(BaseModel):
    input: str
    output: str


class HeaderConfig(BaseModel):
    key: str
    value: str


class ToolParameterConfig(BaseModel):
    key: str
    value: str


class ToolConfig(BaseModel):
    name: str
    parameters: List[ToolParameterConfig] | None = None


class ModelConfig(BaseModel):
    provider: str
    model: str


class ChatModelConfig(BaseModel):
    id: str
    name: str
    description: str
    type: str
    url: str | None = None
    model: ModelConfig | None = None
    prompts: List[PromptConfig] | None = None
    model_parameters: List[ModelParameterConfig] | None = None
    few_shot_examples: List[FewShotExampleConfig] | None = None
    headers: List[HeaderConfig] | None = None
    tools: List[ToolConfig] | None = None
