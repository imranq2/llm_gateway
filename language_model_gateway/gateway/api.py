import time

from typing import Optional, List, Dict, Any

from pydantic import BaseModel

from fastapi import FastAPI

# Based on https://towardsdatascience.com/how-to-build-an-openai-compatible-api-87c8edea2f06

from typing import List, Optional

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "mock-gpt-model"
    messages: List[ChatMessage]
    max_tokens: Optional[int] = 512
    temperature: Optional[float] = 0.1
    stream: Optional[bool] = False


app = FastAPI(title="OpenAI-compatible API")


@app.post("/chat/completions")
async def chat_completions(request: ChatCompletionRequest) -> Dict[str, Any]:
    if request.messages and request.messages[0].role == "user":
        resp_content = (
            "As a mock AI Assistant, I can only echo your last message:"
            + request.messages[-1].content
        )
    else:
        resp_content = "As a mock AI Assistant, I can only echo your last message, but there were no messages!"

    return {
        "id": "1337",
        "object": "chat.completion",
        "created": time.time(),
        "model": request.model,
        "choices": [{"message": ChatMessage(role="assistant", content=resp_content)}],
    }
