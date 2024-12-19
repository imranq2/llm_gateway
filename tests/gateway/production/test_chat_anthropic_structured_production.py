import os
from typing import Optional, Any, Dict, List

import pytest
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion
from openai.types.shared_params import (
    ResponseFormatJSONSchema,
)
from openai.types.shared_params.response_format_json_schema import JSONSchema
from pydantic import BaseModel, Field


# Now use Pydantic to define the schema for the JSON input and output


class DoctorInput(BaseModel):
    doctor_name: str = Field(description="The full name of the doctor")
    doctor_organization: str | None = Field(
        description="The health system name", default=None
    )


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


class Result(BaseModel):
    doctor_information: List[DoctorInformation] = Field(
        description="The information about the doctor"
    )


@pytest.mark.skipif(
    os.getenv("RUN_TESTS_WITH_REAL_LLM") != "1",
    reason="hits production API",
)
async def test_chat_completions_structured_production(
    # async_client: httpx.AsyncClient,
) -> None:
    """
    This test requests passes in structured input and expects structured output


    :return:
    """
    print("")

    # init client and connect to localhost server
    client = AsyncOpenAI(
        api_key="fake-api-key",
        base_url="https://language-model-gateway.services.bwell.zone/api/v1",
        # http_client=async_client,
    )

    json_schema: Dict[str, Any] = Result.model_json_schema()

    doctor_inputs: List[DoctorInput] = [
        DoctorInput(doctor_name="Vanessa Paz NP", doctor_organization="One Medical"),
        DoctorInput(
            doctor_name="Dr. Meggin A. Sabatino", doctor_organization="Medstar Health"
        ),
        DoctorInput(
            doctor_name="Dr. James Ward", doctor_organization="Johns Hopkins Hospital"
        ),
    ]

    doctor_input_text: str = ", ".join(
        f"{doctor.doctor_name} at {doctor.doctor_organization}"
        for doctor in doctor_inputs
    )

    # call API
    chat_completion: ChatCompletion = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": f"""Get the address of following doctors: {doctor_input_text}.""",
            }
        ],
        model="General Purpose",
        response_format=ResponseFormatJSONSchema(
            type="json_schema",
            json_schema=JSONSchema(
                name="Result",
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

    doctor_information = Result.parse_raw(content)
    print("======= Doctor Information =======")
    print(doctor_information)
    print("======= End of Doctor Information =======")
