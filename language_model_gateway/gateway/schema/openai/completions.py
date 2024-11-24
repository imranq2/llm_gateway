from typing import Literal, Iterable, Dict, Optional, Union, List, TypedDict

import httpx
from openai import NotGiven

# noinspection PyProtectedMember
from openai._types import Headers, Query, Body
from openai.types import ChatModel
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionAudioParam,
    completion_create_params,
    ChatCompletionModality,
    ChatCompletionPredictionContentParam,
    ChatCompletionStreamOptionsParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolParam,
    ChatCompletionSystemMessageParam,
    ChatCompletionContentPartTextParam,
    ChatCompletionUserMessageParam,
    ChatCompletionAssistantMessageParam,
)


# This class is copied from openai package: openai/resources/chat/completions.py


class ChatRequest(TypedDict, total=False):
    messages: Iterable[ChatCompletionMessageParam]
    model: Union[str, ChatModel]
    audio: Optional[ChatCompletionAudioParam] | NotGiven
    frequency_penalty: Optional[float] | NotGiven
    function_call: completion_create_params.FunctionCall | NotGiven
    functions: Iterable[completion_create_params.Function] | NotGiven
    logit_bias: Optional[Dict[str, int]] | NotGiven
    logprobs: Optional[bool] | NotGiven
    max_completion_tokens: Optional[int] | NotGiven
    max_tokens: Optional[int] | NotGiven
    metadata: Optional[Dict[str, str]] | NotGiven
    modalities: Optional[List[ChatCompletionModality]] | NotGiven
    n: Optional[int] | NotGiven
    parallel_tool_calls: bool | NotGiven
    prediction: Optional[ChatCompletionPredictionContentParam] | NotGiven
    presence_penalty: Optional[float] | NotGiven
    response_format: completion_create_params.ResponseFormat | NotGiven
    seed: Optional[int] | NotGiven
    service_tier: Optional[Literal["auto", "default"]] | NotGiven
    stop: Union[Optional[str], List[str]] | NotGiven
    store: Optional[bool] | NotGiven
    stream: Optional[Literal[False]] | Literal[True] | NotGiven
    stream_options: Optional[ChatCompletionStreamOptionsParam] | NotGiven
    temperature: Optional[float] | NotGiven
    tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven
    tools: Iterable[ChatCompletionToolParam] | NotGiven
    top_logprobs: Optional[int] | NotGiven
    top_p: Optional[float] | NotGiven
    user: str | NotGiven
    # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
    # The extra values given here take precedence over values defined on the client or passed to this method.
    extra_headers: Headers | None
    extra_query: Query | None
    extra_body: Body | None
    timeout: float | httpx.Timeout | None | NotGiven


ROLE_TYPES = Literal["system", "user", "assistant", "tool"]

INCOMING_MESSAGE_TYPES = str | Iterable[ChatCompletionContentPartTextParam]

IncomingSystemMessage = ChatCompletionSystemMessageParam

IncomingHumanMessage = ChatCompletionUserMessageParam

IncomingAssistantMessage = ChatCompletionAssistantMessageParam
