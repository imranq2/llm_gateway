from pydantic import BaseModel


class Endpoint(BaseModel):
    url: str
    method: str


class ConfiguredModel(BaseModel):
    name: str
    endpoint: Endpoint
    input: str
