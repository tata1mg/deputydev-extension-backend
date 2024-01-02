from typing import List

from app.managers.openai_tools.util import openaifunc
from app.managers.serializer.lab_test_serializer import LabTestSerializer
from app.models.chat import ChatTypeMsg, ChatTypeSkuCard, ChatTypeCallAgent
from app.service_clients.labs import LabsClient


@openaifunc
async def show_lab_test_card(identifier: str, city: str) -> List[any]:
    """
    Get details of the lab test from API call and show a lab test card to user to increase add to cart.
    @param identifier: The unique identifier of a test or Test ID
    @param city: The name of the city user is currently in or for whichever city user ask for in their question
    """
    test_details = await LabsClient.get_lab_test_details('2558', city)
    if not test_details:
        return [ChatTypeMsg.model_validate({"answer": "You can know more about TATA 1mg lab tests here "
                                                      "- https://1mg.com/labs"}),
                ChatTypeCallAgent()]
    test_serialized_details = LabTestSerializer.format_lab_test_data(
        test_details.get("data")
    )
    response = [
        ChatTypeMsg.model_validate(
            {
                "answer": "Here are more details. You can book the test directly from here.",
            }
        ),
        ChatTypeSkuCard.model_validate(test_serialized_details),
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
        ChatTypeCallAgent()
    ]
    return response
