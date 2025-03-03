from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import (
    MessageThreadDTO,
    MessageType,
)
from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
)
from app.main.blueprints.one_dev.services.past_workflows.serializer.base_serializers import (
    BaseSerializer,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import (
    PromptFeatureFactory,
)


class PastChatsSerializer(BaseSerializer):
    def process_raw_data(self, raw_data: List[MessageThreadDTO], type: SerializerTypes) -> List[Dict[str, Any]]:
        tool_use_map: Dict[str, Any] = {}
        formatted_data: List[Dict[str, Any]] = []
        for item in raw_data:
            message_type = item.message_type
            response_block = item.message_data
            llm_model = item.llm_model
            prompt_feature = item.prompt_type
            actor = item.actor.value

            if message_type == MessageType("QUERY"):
                formatted_data.append(
                    {"type": "TEXT_BLOCK", "content": {"text": item.query_vars["query"]}, "actor": actor}
                )
            elif message_type == MessageType("TOOL_RESPONSE"):
                tool_use_id = response_block[0].content.tool_use_id
                if tool_use_id not in tool_use_map:
                    continue
                tool_use_request_block = tool_use_map[tool_use_id]
                tool_use_request_block["content"]["result_json"] = response_block[0].content.response
            else:
                parser_class = PromptFeatureFactory.get_prompt(llm_model, PromptFeatures(prompt_feature))
                parsed_blocks, tool_use_map = parser_class.get_parsed_response_blocks(response_block)
                tool_use_map = tool_use_map
                for block in parsed_blocks:
                    block["actor"] = actor
                    formatted_data.append(block)

        return formatted_data
