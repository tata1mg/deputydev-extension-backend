import json
import re
from typing import Any, Dict
from app.backend_common.services.llm.prompts.llm_base_prompts.claude_3_point_5_sonnet import BaseClaude3Point5SonnetPrompt
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import BaseCodeReviewPrompt


class Claude3Point5JsonDataResponsePrompt(BaseCodeReviewPrompt, BaseClaude3Point5SonnetPrompt):

    def get_parsed_result(self, llm_response: str) -> Dict[str, Any]:
        response = llm_response
        json_match = re.search(r"\{.*\}", llm_response, re.DOTALL)
        if json_match:
            response = json_match.group()
        parsed_response = json.loads(response)
        return {"data": parsed_response["comments"]}

