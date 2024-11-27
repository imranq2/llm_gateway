from typing import List

from pydantic import BaseModel


class Prompt(BaseModel):
    role: str
    message: str


class ModelParameter(BaseModel):
    key: str
    value: float


class FewShotExample(BaseModel):
    input: str
    output: str


class Header(BaseModel):
    key: str
    value: str


class ToolParameter(BaseModel):
    key: str
    value: str


class Tool(BaseModel):
    name: str
    parameters: List[ToolParameter]


class ModelChoice(BaseModel):
    provider: str
    model: str


class ChatModelConfig(BaseModel):
    name: str
    description: str
    type: str
    url: str | None = None
    model: ModelChoice | None = None
    prompts: List[Prompt] | None = None
    model_parameters: List[ModelParameter] | None = None
    few_shot_examples: List[FewShotExample] | None = None
    headers: List[Header] | None = None
    tools: List[Tool] | None = None
