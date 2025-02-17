import json
from typing import Any, Dict
from app.backend_common.services.llm.prompts.llm_base_prompts.gpt_4o import BaseGPT4OPrompt
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import BaseCodeReviewPrompt


class GPT4OJsonDataResponsePrompt(BaseCodeReviewPrompt, BaseGPT4OPrompt):


    def get_parsed_result(self, llm_response: str) -> Dict[str, Any]:
        response = llm_response
        parsed_response = json.loads(response)
        return {"data": parsed_response["comments"]}
