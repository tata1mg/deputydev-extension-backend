from openai.types.chat import ChatCompletionMessage
from torpedo import CONFIG
from openai import OpenAI
from commonutils.utils import Singleton

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):
    def __init__(self):
        self.client = OpenAI(api_key=config.get("OPENAI_KEY"))

    def get_diagnobot_response(self, final_prompt) -> ChatCompletionMessage:
        completion = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": final_prompt}],
            # TODO: Converge tools definition using a single function call. Maybe use decorators for openai_tools functions
            tools=[
                {
                    "type": "function",
                    "function": {
                        "name": "show_lab_test_card",
                        "description": "Get details of the lab test from API call and show a lab test card to "
                        "user to increase add to cart",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "identifier": {
                                    "type": "string",
                                    "description": "The unique identifier of a test or Test ID",
                                },
                                "city": {
                                    "type": "string",
                                    "description": "The name of the city user is currently in or "
                                    "for whichever city user ask for in their question",
                                },
                            },
                            "required": ["identifier", "city"],
                        },
                    },
                }
            ],
        )
        return completion.choices[0].message
