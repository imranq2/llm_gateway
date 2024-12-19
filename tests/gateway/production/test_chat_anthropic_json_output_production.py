from typing import Optional, Any, Dict, List

import httpx
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.shared_params import (
    ResponseFormatJSONSchema,
    ResponseFormatJSONObject,
)
from openai.types.shared_params.response_format_json_schema import JSONSchema
from pydantic import BaseModel, Field


# @pytest.mark.skipif(
#     os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
#     reason="hits production API",
# )
async def test_chat_completions_json__output_production(
    async_client: httpx.AsyncClient,
) -> None:
    """
    This tests requests JSON output without passing a JSON schema

    :param async_client:
    :return:
    """
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        http_client=async_client,
    )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Get the address of Vanessa Paz NP at One Medical.""",
            }
        ],
        model="General Purpose",
        response_format=ResponseFormatJSONObject(
            type="json_object",
        ),
    )

    # print the top "choice"
    content: Optional[str] = "\n".join(
        choice.message.content or "" for choice in chat_completion.choices
    )

    assert content is not None
    print("======= JSON Output =======")
    print(content)
    print("======= End of JSON Output =======")
    # assert "Barack" in content


# @pytest.mark.skipif(
#     os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
#     reason="hits production API",
# )
async def test_chat_completions_json_schema_output_production(
    async_client: httpx.AsyncClient,
) -> None:
    """
    This tests requests JSON output with a JSON schema in the prompt


    :param async_client:
    :return:
    """
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        http_client=async_client,
    )

    json_schema: Dict[str, Any] = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "doctor_name": {
                "type": "string",
                "description": "The full name of the doctor",
            },
            "doctor_address": {
                "type": "object",
                "properties": {
                    "line1": {
                        "type": "string",
                        "description": "First line of the address (street address)",
                    },
                    "line2": {
                        "type": "string",
                        "description": "Second line of the address (apartment, suite, etc.)",
                        "nullable": True,
                    },
                    "city": {
                        "type": "string",
                        "description": "City of the doctor's practice",
                    },
                    "state": {
                        "type": "string",
                        "description": "State of the doctor's practice",
                        "minLength": 2,
                        "maxLength": 2,
                    },
                    "zipcode": {
                        "type": "string",
                        "description": "Zip code of the doctor's practice",
                        "pattern": "^\\d{5}(-\\d{4})?$",
                    },
                },
                "required": ["line1", "city", "state", "zipcode"],
            },
            "doctor_phone": {
                "type": "string",
                "description": "The contact phone number for the doctor",
                "pattern": "^\\(\\d{3}\\)\\s?\\d{3}-\\d{4}$",
            },
        },
        "required": ["doctor_name", "doctor_address", "doctor_phone"],
    }
    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Get the address of Vanessa Paz NP at One Medical.""",
            }
        ],
        model="General Purpose",
        response_format=ResponseFormatJSONSchema(
            type="json_schema",
            json_schema=JSONSchema(
                name="DoctorInformation",
                schema=json_schema,
            ),
        ),
    )

    # print the top "choice"
    content: Optional[str] = "\n".join(
        choice.message.content or "" for choice in chat_completion.choices
    )

    assert content is not None
    print("======= JSON Output =======")
    print(content)
    print("======= End of JSON Output =======")
    # assert "Barack" in content


# Now use Pydantic to define the schema for the JSON output
class Address(BaseModel):
    line1: str = Field(description="First line of the address (street address)")
    line2: Optional[str] = Field(
        description="Second line of the address (apartment, suite, etc.)", default=None
    )
    city: str = Field(description="City of the doctor's practice")
    state: str = Field(description="State of the doctor's practice")
    zipcode: str = Field(description="Zip code of the doctor's practice")
    phone: Optional[str] = Field(
        description="The contact phone number for the doctor",
        default=None,
    )


class DoctorInformation(BaseModel):
    doctor_name: str = Field(description="The full name of the doctor")
    doctor_address: List[Address] | None = Field(
        description="The address of the doctor's practice", default=None
    )


# @pytest.mark.skipif(
#     os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
#     reason="hits production API",
# )
async def test_chat_completions_json_classes_output_production(
    async_client: httpx.AsyncClient,
) -> None:
    """
    This test requests JSON output with a schema by specifying the response_format


    :param async_client:
    :return:
    """
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        http_client=async_client,
    )

    json_schema: Dict[str, Any] = DoctorInformation.model_json_schema()

    # example_doctor_information = DoctorInformation(
    #     doctor_name="James Ward, MD",
    #     doctor_address=Address(
    #         line1="1 House Street",
    #         line2=None,
    #         city="Baltimore",
    #         state="MD",
    #         zipcode="21723",
    #     ),
    #     doctor_phone="(408) 418-4350",
    # )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Get the address of Vanessa Paz NP at One Medical.""",
            }
        ],
        model="General Purpose",
        response_format=ResponseFormatJSONSchema(
            type="json_schema",
            json_schema=JSONSchema(
                name="DoctorInformation",
                schema=json_schema,
            ),
        ),
    )

    # print the top "choice"
    content: Optional[str] = "\n".join(
        choice.message.content or "" for choice in chat_completion.choices
    )

    assert content is not None
    print("======= JSON Output =======")
    print(content)
    print("======= End of JSON Output =======")

    # assert "Barack" in content

    doctor_information = DoctorInformation.parse_raw(content)
    print("======= Doctor Information =======")
    print(doctor_information)
    print("======= End of Doctor Information =======")
