from typing import Dict, Any

from langchain_core.messages import (
    AIMessage,
    BaseMessage,
    HumanMessage,
    ToolMessage,
)
from langchain_core.messages import (
    ChatMessage as LangchainChatMessage,
)
from openai.types.chat import ChatCompletionMessage


def convert_message_content_to_string(content: str | list[str | Dict[str, Any]]) -> str:
    if isinstance(content, str):
        return content
    text: list[str] = []
    for content_item in content:
        if isinstance(content_item, str):
            text.append(content_item)
            continue
        if content_item["type"] == "text":
            text.append(content_item["text"])
    return "".join(text)


def langchain_to_chat_message(message: BaseMessage) -> ChatCompletionMessage:
    """Create a ChatMessage from a LangChain message."""
    match message:
        case HumanMessage():
            assert (
                False
            ), "Human messages should not be converted to ChatCompletionMessage"
        case AIMessage():
            ai_message = ChatCompletionMessage(
                role="assistant",
                content=convert_message_content_to_string(message.content),
            )
            # if message.tool_calls:
            #     ai_message.tool_calls = message.tool_calls
            # if message.response_metadata:
            #     ai_message.response_metadata = message.response_metadata
            return ai_message
        case ToolMessage():
            assert (
                False
            ), "Tool messages should not be converted to ChatCompletionMessage"
        case LangchainChatMessage():
            assert (
                False
            ), "Chat messages should not be converted to ChatCompletionMessage"
        case _:
            raise ValueError(f"Unsupported message type: {message.__class__.__name__}")


def remove_tool_calls(
    content: str | list[str | dict[str, Any]]
) -> str | list[str | dict[str, Any]]:
    """Remove tool calls from content."""
    if isinstance(content, str):
        return content
    # Currently only Anthropic models stream tool calls, using content item type tool_use.
    return [
        content_item
        for content_item in content
        if isinstance(content_item, str) or content_item["type"] != "tool_use"
    ]
