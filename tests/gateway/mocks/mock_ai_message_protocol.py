from typing import Protocol, runtime_checkable

from langchain_core.messages import BaseMessage


@runtime_checkable
class MockAiMessageProtocol(Protocol):
    def __call__(self, *, messages: list[BaseMessage]) -> str: ...
