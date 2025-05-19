from math import e
from typing import Any, Dict, List, Optional

from app.backend_common.models.dto.message_thread_dto import (
    MessageThreadDTO,
    MessageType,
    TextBlockData,
    FileBlockData
)
from app.main.blueprints.one_dev.services.past_workflows.constants.serializer_constants import (
    SerializerTypes,
)
from app.main.blueprints.one_dev.services.past_workflows.serializer.base_serializers import (
    BaseSerializer,
)
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    DetailedFocusItem,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.one_dev.services.query_solver.prompts.factory import (
    PromptFeatureFactory,
)
from app.backend_common.service_clients.aws_s3.aws_s3_service_client import AWSS3ServiceClient


class PastChatsSerializer(BaseSerializer):
    async def process_raw_data(self, raw_data: List[MessageThreadDTO], type: SerializerTypes) -> List[Dict[str, Any]]:
        tool_use_map: Dict[str, Any] = {}
        formatted_data: List[Dict[str, Any]] = []
        current_query_write_mode: bool = False
        for item in raw_data:
            message_type = item.message_type
            response_block = item.message_data
            llm_model = item.llm_model
            prompt_feature: Optional[PromptFeatures] = None
            try:
                prompt_feature = PromptFeatures(item.prompt_type)
            except Exception:
                continue

            actor = item.actor.value

            if message_type == MessageType.QUERY:
                text_data = item.message_data[0]
                if (
                    not isinstance(text_data, TextBlockData)
                    or not text_data.content_vars
                    or not isinstance((text_data.content_vars or {}).get("query"), str)
                ):
                    continue                

                focus_objects: List[Dict[str, Any]] = []
                if text_data.content_vars.get("focus_items"):
                    for focus_item in text_data.content_vars["focus_items"]:
                        focus_item_data = DetailedFocusItem(**focus_item)
                        focus_objects.append(
                            {
                                "type": focus_item_data.type.value,
                                "value": focus_item_data.value,
                                "path": focus_item_data.path,
                                "chunks": [
                                    {
                                        "start_line": chunk.source_details.start_line,
                                        "end_line": chunk.source_details.end_line,
                                    }
                                    for chunk in focus_item_data.chunks
                                ],
                            }
                        )

                if text_data.content_vars.get("urls"):
                    for focus_item in text_data.content_vars["urls"]:
                        focus_item_data = DetailedFocusItem(**focus_item)
                        focus_objects.append(
                            {
                                "type": focus_item_data.type.value,
                                "value": focus_item_data.value,
                                "path": focus_item_data.url,
                                "url": focus_item_data.url,
                                "chunks": [],
                            }
                        )

                if "write_mode" in text_data.content_vars:
                    current_query_write_mode = text_data.content_vars["write_mode"]

                content = {"text": text_data.content_vars["query"]}
                if focus_objects:
                    content["focus_items"] = focus_objects

                if len(item.message_data) > 1 and item.message_data[1]:
                    file_data = item.message_data[1]
                    if isinstance(file_data, FileBlockData):
                        s3_key = file_data.content.s3_key
                        presigned_url = await AWSS3ServiceClient().create_presigned_get_url(s3_key)
                    formatted_data.append({"type": "TEXT_BLOCK", "content": content, "s3Reference": {"get_url": presigned_url,"file_type": file_data.content.type}, "actor": actor})
                else:
                    formatted_data.append({"type": "TEXT_BLOCK", "content": content, "actor": actor})

            elif message_type == MessageType.TOOL_RESPONSE:
                tool_use_id = response_block[0].content.tool_use_id
                if tool_use_id not in tool_use_map:
                    continue
                tool_use_request_block = tool_use_map[tool_use_id]
                tool_use_request_block["content"]["result_json"] = response_block[0].content.response
            else:
                parser_class = PromptFeatureFactory.get_prompt(llm_model, prompt_feature)
                parsed_blocks, tool_use_map = parser_class.get_parsed_response_blocks(response_block)
                tool_use_map = tool_use_map
                for block in parsed_blocks:
                    block["actor"] = actor
                    block["write_mode"] = current_query_write_mode
                    formatted_data.append(block)

        return formatted_data
