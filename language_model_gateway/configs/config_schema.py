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


class ModelConfig(BaseModel):
    model: str
    name: str
    description: str
    type: str
    url: str
    prompts: List[Prompt]
    model_parameters: List[ModelParameter]
    few_shot_examples: List[FewShotExample]
    headers: List[Header]
