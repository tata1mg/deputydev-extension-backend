import re

from app.common.services.prompt.llm_base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)


class Claude3Point5ChunkDescriptionGenerationPrompt(BaseClaude3Point5SonnetPrompt):
    prompt_type = "CHUNK_DESCRIPTION_GENERATION"

    @classmethod
    def get_prompt(cls, params: dict):
        user_message = f"""Given are few chunks of code numbered from 1, 2, and so on. Please analyse each of them and provide a single liner small natural language description for each of them

            The chunks are as follows:
            {params.get("code_block")}

            Provide your responses like this -
            <descriptions>
            <chunk id=1>description of chunk 1</chunk>
            <chunk id=2>description of chunk 2</chunk>
            <chunk id=3>description of chunk 3</chunk>
            ...
            </descriptions>
        """
        system_message = "You are a code analysis expert"

        return {"system_message": system_message, "user_message": user_message}

    @classmethod
    def get_parsed_result(cls, llm_response: str) -> dict:
        descriptions = re.findall(r"<chunk id=\d+>.*?</chunk>", llm_response)
        descriptions = [re.sub(r"<chunk id=\d+>|</chunk>", "", description) for description in descriptions]
        return {"descriptions": descriptions}
