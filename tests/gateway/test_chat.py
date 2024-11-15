import pytest
from openai import OpenAI


@pytest.mark.asyncio
async def test_chat_completions() -> None:

    # init client and connect to localhost server
    client = OpenAI(
        api_key="fake-api-key",
        base_url="http://localhost:5000",  # change the default port if needed
    )

    # call API
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-1337-turbo-pro-max",
    )

    # print the top "choice"
    print(chat_completion.choices[0].message.content)
