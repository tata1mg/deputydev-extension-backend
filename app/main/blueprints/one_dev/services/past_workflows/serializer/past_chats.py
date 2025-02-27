from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import MessageThreadDTO
from app.main.blueprints.one_dev.constants.serializers_constants import SerializerTypes
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import PromptFeatures
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import PromptFeatureFactory
from app.main.blueprints.one_dev.services.past_workflows.serializer.base_serializers import BaseSerializer

class PastChatsSerializer(BaseSerializer):
    def process_raw_data(self, raw_data: List[MessageThreadDTO], type: SerializerTypes) -> List[Dict[str, Any]]:

        formatted_data = []
        for item in raw_data:
            message_type = item.message_type
            response_block = item.message_data
            llm_model = item.llm_model
            prompt_feature = item.prompt_type
            actor = item.actor.value

            if message_type.value == "QUERY":
                formatted_data.append({
                    "type": "TEXT_BLOCK",
                    "content": {
                        "text": item.query_vars["query"]
                    },
                    "actor": actor
                })
            else:
                parser_class = PromptFeatureFactory.get_prompt(llm_model, PromptFeatures(prompt_feature))
                parsed_blocks = parser_class.get_parsed_response_blocks(response_block)
                for block in parsed_blocks:
                    if block["type"] == "TOOL_USE_RESPONSE_BLOCK":
                        for request_block in formatted_data:
                            if request_block["type"] == "TOOL_USE_REQUEST_BLOCK" and request_block["content"]["tool_use_id"] == block["content"]["tool_use_id"]:
                                # Update the request block with data from the response block
                                request_block["content"]["result_json"] = block["content"]["result_json"]
                                break
                        continue
                    block["actor"] = actor
                    formatted_data.append(block)

        return formatted_data