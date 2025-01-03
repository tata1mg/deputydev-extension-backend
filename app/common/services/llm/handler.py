from typing import Dict, List

from torpedo import CONFIG

from app.common.constants.constants import LLModels
from app.common.services.llm.dataclasses.main import LLMCallResponse, LLMMeta, LLMUsage
from app.common.services.llm.providers.anthropic_llm import Anthropic
from app.common.services.llm.providers.openai_llm import OpenaiLLM
from app.common.services.prompt.base_prompt import BasePrompt


class LLMHandler:
    model_to_provider_class_map = {
        LLModels.CLAUDE_3_POINT_5_SONNET: Anthropic,
        LLModels.GPT_4O: OpenaiLLM,
    }

    def __init__(self, prompt: BasePrompt):
        self.prompt = prompt

    async def get_llm_response_data(self, previous_responses: List[Dict[str, str]]) -> LLMCallResponse:
        detected_llm = self.prompt.model_name

        if detected_llm not in self.model_to_provider_class_map:
            raise ValueError(f"LLM model {detected_llm} not supported")

        client = self.model_to_provider_class_map[detected_llm]()
        model_config = CONFIG.config.get("LLM_MODELS").get(detected_llm.value)
        prompt = self.prompt.get_prompt()
        llm_message = client.build_llm_messages(prompt, previous_responses)

        response = await client.call_service_client(
            messages=llm_message, model=model_config.get("NAME"), response_type="text"
        )
        parsed_response, input_tokens, output_tokens = await client.parse_response(response)

        return LLMCallResponse(
            raw_prompt=prompt["user_message"],
            raw_llm_response=parsed_response,
            parsed_llm_data=self.prompt.get_parsed_result(parsed_response),
            llm_meta=LLMMeta(
                llm_model=detected_llm,
                prompt_type=self.prompt.prompt_type,
                token_usage=LLMUsage(input=input_tokens, output=output_tokens),
            ),
        )
