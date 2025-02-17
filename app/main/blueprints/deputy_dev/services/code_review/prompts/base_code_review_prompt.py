from typing import Optional
from app.backend_common.services.llm.dataclasses.main import UserAndSystemMessages
from app.backend_common.services.llm.prompts.base_prompt import BasePrompt


class BaseCodeReviewPrompt(BasePrompt):
    user_message: str
    system_message: Optional[str]

    def __init__(self, user_message: str, system_message: Optional[str]):
        self.user_message = user_message
        self.system_message = system_message

    def get_prompt(self) -> UserAndSystemMessages:
        return UserAndSystemMessages(user_message=self.user_message, system_message=self.system_message)