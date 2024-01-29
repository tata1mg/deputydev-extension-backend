from typing import List

from sanic.log import logger

from app.managers.openai_tools.util import openaifunc
from app.managers.serializer.lab_test_serializer import LabSkuSerializer
from app.models.chat import ChatTypeCallAgent, ChatTypeMsg, ChatTypeSkuCard
from app.service_clients.labs import LabsClient


@openaifunc
async def show_lab_sku_card(identifier: str, city: str) -> List[any]:
    """
    Get details of the lab test from API call and show a lab test card to user.
    Should not be called when comparing 2 or more lab tests.
    @param identifier: The unique identifier of a test or Test ID which is most relevant to the question asked by user
    @param city: The name of the city user is currently in or for whichever city user ask for in their question
    """
    logger.info("Test identifier: {}  City: {}".format(identifier, city))
    sku_details = await LabsClient.get_lab_sku_details(identifier, city)
    if not sku_details:
        return [
            ChatTypeMsg.model_validate(
                {"answer": "You can know more about TATA 1mg lab tests here " "- https://1mg.com/labs"}
            ),
            ChatTypeCallAgent(),
        ]
    lab_sku_serialized_details = LabSkuSerializer.format_lab_sku_data(sku_details)
    response = [
        ChatTypeMsg.model_validate(
            {
                "answer": "Here are more details. You can book the test directly from here.",
            }
        ),
        ChatTypeSkuCard.model_validate(lab_sku_serialized_details),
    ]
    return response


@openaifunc
async def show_agent_calling_card() -> List[any]:

    """
    Show call to agent card to user. Whenever user ask to speak to an agent, representative or a real human.
    This function should execute.
    """
    response = [
        ChatTypeMsg.model_validate(
            {
                "answer": "TATA 1mg labs is just a call away.",
            }
        ),
        ChatTypeCallAgent(),
    ]
    return response
