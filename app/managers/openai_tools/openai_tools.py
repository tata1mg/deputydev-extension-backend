import ast
from typing import List
from app.managers.serializer.lab_test_serializer import LabTestSerializer
from app.models.chat import ChatTypeMsg, ChatTypeSkuCard
from app.service_clients.labs import LabsClient

# TODO : Create a new function for calling an agent.


async def show_lab_test_card(arguments: dict) -> List[any]:
    # TODO : Call Labs API and return approprouate contract for SKU card
    print("Inside show_lab_test_card")
    test_details = await LabsClient.get_lab_test_details(ast.literal_eval(arguments))
    test_serialized_details = LabTestSerializer.format_lab_test_data(
        test_details.get("data")
    )
    response = [
        ChatTypeMsg(
            **{
                "answer": "Here are more details. You can book the test directly from here.",
            }
        ),
        ChatTypeSkuCard.parse_obj(test_serialized_details),
    ]
    return response
