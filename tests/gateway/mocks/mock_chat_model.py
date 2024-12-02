import typing
from typing import Optional, Any, Sequence, Union, Callable

from langchain_core.callbacks import CallbackManagerForLLMRun
from langchain_core.language_models import BaseChatModel, LanguageModelInput
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from tests.gateway.mocks.mock_ai_message_protocol import MockAiMessageProtocol


class MockChatModel(BaseChatModel):
    fn_get_response: MockAiMessageProtocol

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: Optional[list[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    ) -> ChatResult:
        return self.fn_get_response(messages=messages)

    def bind_tools(
        self,
        tools: Sequence[
            Union[
                typing.Dict[str, Any], type, Callable[[], Any], BaseTool
            ]  # noqa: UP006
        ],
        **kwargs: Any,
    ) -> Runnable[LanguageModelInput, BaseMessage]:
        return self
