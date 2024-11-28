import json
import logging
import time
from typing import (
    Any,
    List,
    cast,
    AsyncGenerator,
    Iterable,
    TypedDict,
    Sequence,
    Dict,
)

from fastapi import HTTPException
from langchain.agents import AgentExecutor
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage, AIMessage
from langchain_core.messages import (
    AnyMessage,
)
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnableSerializable, RunnablePassthrough
from langchain_core.runnables.schema import CustomStreamEvent, StandardStreamEvent
from langchain_core.tools import BaseTool
from langchain_core.utils.function_calling import convert_to_openai_function
from openai.types import CompletionUsage
from openai.types.chat import (
    ChatCompletionChunk,
    ChatCompletion,
    ChatCompletionMessage,
    ChatCompletionSystemMessageParam,
)
from openai.types.chat import ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta, Choice as ChunkChoice
from starlette.responses import StreamingResponse, JSONResponse

from language_model_gateway.gateway.schema.openai.completions import (
    ChatRequest,
    ROLE_TYPES,
    INCOMING_MESSAGE_TYPES,
)
from language_model_gateway.gateway.utilities.chat_message_helpers import (
    langchain_to_chat_message,
)

logger = logging.getLogger(__file__)

type MessageList = List[BaseMessage]
type ToolList = Sequence[BaseTool]


class ChainInput(TypedDict):
    input: str
    chat_history: MessageList


class ChainOutput(TypedDict):
    output: Dict[str, Any]


class LangChainToOpenAIConverter:
    async def _stream_resp_async_generator(
        self,
        *,
        request: ChatRequest,
        request_id: str,
        chain_input: ChainInput,
        tools: ToolList,
        llm: BaseChatModel,
        system_messages: List[ChatCompletionSystemMessageParam],
    ) -> AsyncGenerator[str, None]:
        """
        Asynchronously generate streaming responses from the agent.

        Yields:
            The streaming response as a string.
        """

        logger.info(f"Streaming response from generator {request_id} from agent.")

        # Process streamed events from the graph and yield messages over the SSE stream.
        event: StandardStreamEvent | CustomStreamEvent
        async for event in self.astream_events(
            system_messages=system_messages,
            chain_input=chain_input,
            tools=tools,
            llm=llm,
        ):
            if not event:
                continue

            event_type: str = event["event"]

            match event_type:
                case "on_chain_start":
                    # Handle the start of the chain event
                    pass
                case "on_chat_model_stream":
                    # Handle the chat model stream event
                    chunk: AIMessageChunk = event["data"]["chunk"]
                    content: str | list[str | dict[str, Any]] = chunk.content

                    content_text: str
                    if isinstance(content, list):
                        content_text_or_dict: str | dict[str, Any] = (
                            content[0] if len(content) > 0 else ""
                        )
                        if isinstance(content_text_or_dict, dict):
                            content_text = (
                                cast(str, content_text_or_dict.get("text"))
                                if content_text_or_dict.get("text")
                                else ""
                            )
                            assert isinstance(
                                content_text, str
                            ), f"content_text: {content_text} (type: {type(content_text)})"
                        else:
                            assert isinstance(content_text_or_dict, str)
                            content_text = content_text_or_dict
                    else:
                        assert isinstance(content, str)
                        content_text = content

                    assert isinstance(
                        content_text, str
                    ), f"content_text: {content_text} (type: {type(content_text)})"

                    if content_text:
                        chat_stream_response: ChatCompletionChunk = ChatCompletionChunk(
                            id=request_id,
                            created=int(time.time()),
                            model=request["model"],
                            choices=[
                                ChunkChoice(
                                    index=0,
                                    delta=ChoiceDelta(
                                        role="assistant", content=content_text
                                    ),
                                )
                            ],
                            usage=CompletionUsage(
                                prompt_tokens=0, completion_tokens=0, total_tokens=0
                            ),
                            object="chat.completion.chunk",
                        )
                        yield f"data: {json.dumps(chat_stream_response.model_dump())}\n\n"
                case "on_chain_end":
                    # Handle the end of the chain event
                    pass
                case _:
                    # Handle other event types
                    pass

        yield "data: [DONE]\n\n"

    async def call_agent_with_input(
        self,
        *,
        request: ChatRequest,
        request_id: str,
        system_messages: List[ChatCompletionSystemMessageParam],
        llm: BaseChatModel,
        chain_input: ChainInput,
        tools: ToolList,
    ) -> StreamingResponse | JSONResponse:
        """
        Call the agent with the provided input and return the response.

        Returns:
            The response as a StreamingResponse or JSONResponse.
        """
        assert request is not None
        assert isinstance(request, dict)

        if request.get("stream"):
            return StreamingResponse(
                await self.get_streaming_response_async(
                    request=request,
                    request_id=request_id,
                    llm=llm,
                    system_messages=system_messages,
                    tools=tools,
                    chain_input=chain_input,
                ),
                media_type="text/event-stream",
            )
        else:
            try:
                response: List[AnyMessage] = await self.ainvoke(
                    system_messages=system_messages,
                    chain_input=chain_input,
                    llm=llm,
                    tools=tools,
                )
                output: ChatCompletionMessage = langchain_to_chat_message(response[-1])
                chat_response: ChatCompletion = ChatCompletion(
                    id=request_id,
                    model=request["model"],
                    choices=[Choice(index=0, message=output, finish_reason="stop")],
                    usage=CompletionUsage(
                        prompt_tokens=0, completion_tokens=0, total_tokens=0
                    ),
                    created=int(time.time()),
                    object="chat.completion",
                )
                return JSONResponse(content=chat_response.model_dump())
            except Exception as e:
                logger.error(f"An exception occurred: {e}")
                raise HTTPException(status_code=500, detail="Unexpected error")

    async def get_streaming_response_async(
        self,
        *,
        request: ChatRequest,
        request_id: str,
        chain_input: ChainInput,
        llm: BaseChatModel,
        system_messages: List[ChatCompletionSystemMessageParam],
        tools: ToolList,
    ) -> AsyncGenerator[str, None]:
        """
        Get the streaming response asynchronously.

        Returns:
            The streaming response as an async generator.
        """
        logger.info(f"Streaming response {request_id} from agent")
        generator: AsyncGenerator[str, None] = self._stream_resp_async_generator(
            request=request,
            request_id=request_id,
            llm=llm,
            system_messages=system_messages,
            tools=tools,
            chain_input=chain_input,
        )
        return generator

    # noinspection SpellCheckingInspection,PyMethodMayBeStatic
    async def ainvoke(
        self,
        *,
        system_messages: List[ChatCompletionSystemMessageParam],
        chain_input: ChainInput,
        tools: ToolList,
        llm: BaseChatModel,
    ) -> List[AnyMessage]:
        """
        Run the agent asynchronously.
        """
        system_prompts: List[str] = cast(
            List[str], [s["content"] for s in system_messages]
        )
        chain: Runnable[ChainInput, ChainOutput] = self.create_chain(
            llm=llm, system_prompts=system_prompts, tools=tools
        )

        response: ChainOutput = await chain.ainvoke(chain_input)
        output: Dict[str, Any] = response["output"]
        output_text: str = output["output"]
        return [AIMessage(content=output_text)]

    # noinspection PyMethodMayBeStatic
    def create_chain(
        self,
        *,
        llm: BaseChatModel,
        system_prompts: List[str],
        tools: ToolList,
    ) -> Runnable[ChainInput, ChainOutput]:
        prompt: ChatPromptTemplate = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    system_prompt,
                )
                for system_prompt in system_prompts
            ]
            + [
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ]
        )
        # Create functions for the LLM
        llm_with_tools = llm.bind(
            functions=[convert_to_openai_function(t) for t in tools]
        )
        # Create the agent
        agent: RunnableSerializable[ChainInput, ChainOutput] = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: convert_to_openai_function(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()  # type: ignore[operator]
        )
        # Create the executor
        agent_executor: AgentExecutor = AgentExecutor(
            agent=agent, tools=tools, verbose=True, return_intermediate_steps=True
        )
        # Create the final chain
        chain: RunnableSerializable[
            ChainInput, ChainOutput
        ] = RunnablePassthrough.assign(
            output=agent_executor
        ) | (  # type:ignore[assignment]
            lambda x: {"output": x["output"]}  # type:ignore[operator]
        )
        return chain

    async def astream_events(
        self,
        *,
        system_messages: List[ChatCompletionSystemMessageParam],
        chain_input: ChainInput,
        tools: ToolList,
        llm: BaseChatModel,
    ) -> AsyncGenerator[StandardStreamEvent | CustomStreamEvent, None]:
        """
        Stream events asynchronously.

        Yields:
            The standard or custom stream event.
        """
        system_prompts: List[str] = [cast(str, s["content"]) for s in system_messages]
        chain: Runnable[ChainInput, ChainOutput] = self.create_chain(
            llm=llm, system_prompts=system_prompts, tools=tools
        )

        # Get response
        chunk: ChainOutput
        async for chunk in chain.astream(chain_input):
            if isinstance(chunk, dict) and "output" in chunk:
                print(chunk["output"], end="", flush=True)
                output: Dict[str, Any] = chunk["output"]
                output_text: str = output["output"]
                # noinspection PyArgumentList
                yield StandardStreamEvent(
                    run_id="",
                    parent_ids=[],
                    name="",
                    event="on_chat_model_stream",
                    data={
                        "chunk": AIMessageChunk(
                            content=output_text,
                        )
                    },
                )

    # noinspection PyMethodMayBeStatic
    def create_messages_for_graph(
        self, *, messages: Iterable[ChatCompletionMessageParam]
    ) -> List[tuple[ROLE_TYPES, INCOMING_MESSAGE_TYPES]]:
        """
        Create messages for the graph.

        Args:
            messages: The iterable of chat completion message parameters.

        Returns:
            The list of role and incoming message type tuples.
        """
        return cast(
            List[tuple[ROLE_TYPES, INCOMING_MESSAGE_TYPES]],
            [(m["role"], m["content"]) for m in messages],
        )

    async def run_graph_async(
        self,
        *,
        request: ChatRequest,
        llm: BaseChatModel,
        tools: ToolList,
        chain_input: ChainInput,
        system_messages: List[ChatCompletionSystemMessageParam],
    ) -> List[AnyMessage]:
        """
        Run the graph asynchronously.

        Returns:
            The list of any messages.
        """

        output_messages: List[AnyMessage] = await self.ainvoke(
            llm=llm,
            chain_input=chain_input,
            system_messages=system_messages,
            tools=tools,
        )
        return output_messages
