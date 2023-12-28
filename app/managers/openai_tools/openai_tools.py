from typing import List

from app.models.chat import ChatTypeMsg, ChatTypeSkuCard

# TODO : Create a new function for calling an agent.


async def show_lab_test_card(arguments: dict) -> List[any]:
    # TODO : Call Labs API and return approprouate contract for SKU card
    print("Inside show_lab_test_card")
    response = [
        ChatTypeMsg(
            **{
                "answer": "Here are more details. You can book the test directly from here.",
            }
        ),
        ChatTypeSkuCard(
            **{
                "header": "Liver function test (LFT)",
                "sub_header": "Also known as LFT test",
                "report_eta": "Get report in 72hrs",
                "icon": "https://onemg.gumlet.io/assets/44a16856-6882-11ec-82c2-0a3c85ad997a.png?format=auto",
                "price": "500",
                "sku_id": "25166",
                "target_url": "https://www.1mg.com/labs/test/lft-liver-function-test-2562",
                "cta": "add2cart",
            }
        ),
    ]
    return response
