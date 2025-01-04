from typing import Dict, List

from torpedo import CONFIG

from app.backend_common.services.llm.providers.anthropic_llm import Anthropic
from app.backend_common.services.llm.providers.openai_llm import OpenaiLLM
from app.backend_common.utils.app_utils import get_task_response
from app.common.constants.constants import LLMProviders

config = CONFIG.config


class MultiAgentsLLMManager:
    REVIEW_FACTORY = {LLMProviders.OPENAI.value: OpenaiLLM, LLMProviders.ANTHROPIC.value: Anthropic}

    @classmethod
    async def get_llm_response(cls, prompt_list: List[Dict[str, str]]):
        """
        Retrieves LLM responses based on the configured LLM type.

        Args:
            prompt_list (List[Dict[str, str]]): List of prompt objects.

        Returns:
            Dict[str, str]: A dictionary mapping prompt keys to LLM responses.
        """
        openai_prompts, anthropic_prompts = cls.parse_prompts(prompt_list)
        tasks = []

        if openai_prompts:
            tasks.extend(OpenaiLLM().create_bulk_tasks(openai_prompts))
        if anthropic_prompts:
            tasks.extend(Anthropic().create_bulk_tasks(anthropic_prompts))

        llm_responses = await get_task_response(tasks, suppress_exception=False)
        return llm_responses

    @classmethod
    def parse_prompts(cls, prompt_list):
        openai_prompts = []
        anthropic_prompts = []
        for prompt in prompt_list:
            provider = config["LLM_MODELS"][prompt["model"]]["PROVIDER"]
            if provider == LLMProviders.OPENAI.value:
                openai_prompts.append(prompt)
            elif provider == LLMProviders.ANTHROPIC.value:
                anthropic_prompts.append(prompt)
        return openai_prompts, anthropic_prompts
