from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import MessageThreadDTO
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.serializer.base_serializers import BaseSerializer

class PastChatsSerializer(BaseSerializer):
    def process_raw_data(self, raw_data: List[MessageThreadDTO], type: str) -> List[Dict[str, Any]]:

        formatted_data = []
        for item in raw_data:
            response_block = item.message_data
            llm_model = item.llm_model
            prompt_feature = item.prompt_type
            parser_class = PromptFeatureFactory.get_prompt(llm_model, PromptFeatures(prompt_feature))
            parsed_blocks = parser_class.get_parsed_response_blocks(response_block)
            for block in parsed_blocks:
                block["actor"] = item.actor.value
                formatted_data.append(block)

        return formatted_data