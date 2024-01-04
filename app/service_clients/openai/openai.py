from openai.types.chat import ChatCompletionMessage
from torpedo import CONFIG
from openai import OpenAI
from commonutils.utils import Singleton

from app.managers.openai_tools.util import get_openai_funcs

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):
    def __init__(self):
        self.client = OpenAI(api_key=config.get("OPENAI_KEY"))

    def get_diagnobot_response(self, final_prompt) -> ChatCompletionMessage:
        completion = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": final_prompt}],
            tools=get_openai_funcs(),
            tool_choice="auto",
            temperature=0.9,
            seed=12345

        )
        return completion.choices[0].message
