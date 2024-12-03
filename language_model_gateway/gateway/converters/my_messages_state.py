from typing import Optional

from langchain_core.messages.ai import UsageMetadata
from langgraph.graph import MessagesState


class MyMessagesState(MessagesState):
    usage_metadata: Optional[UsageMetadata]
