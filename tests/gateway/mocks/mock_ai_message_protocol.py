from typing import Protocol, runtime_checkable

from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult


@runtime_checkable
class MockAiMessageProtocol(Protocol):
    def __call__(self, *, messages: list[BaseMessage]) -> ChatResult: ...
