from torpedo import CONFIG
from openai import OpenAI
from commonutils.utils import Singleton

config = CONFIG.config


class OpenAIServiceClient(metaclass=Singleton):

    def __init__(self):
        self.client = OpenAI(api_key=config.get("OPENAI_KEY"))

    def get_diagnobot_response(self, final_prompt):
        completion = self.client.chat.completions.create(
            model="gpt-4-1106-preview",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": final_prompt}],
        )
        return completion.choices[0].message.content
