from typing import Any, Dict, List, Optional

from app.backend_common.models.dto.message_thread_dto import MessageThreadDTO, MessageType, TextBlockData, FileBlockData
from app.backend_common.repository.chat_attachments.repository import ChatAttachmentsRepository
from app.backend_common.services.chat_file_upload.chat_file_upload import ChatFileUpload
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

                if len(item.message_data) > 1:
                    # TODO: This will need to be changed if multi file upload is supported
                    for message_data_obj in item.message_data[1:]:
                        if isinstance(message_data_obj, FileBlockData):
                            attachment_id = message_data_obj.content.attachment_id
                            attachment_data = await ChatAttachmentsRepository.get_attachment_by_id(attachment_id)
                            if not attachment_data:
                                continue
                            elif attachment_data.status == "deleted":
                                formatted_data.append({"type": "TEXT_BLOCK", "content": content, "actor": actor})
                                continue
                            presigned_url = await ChatFileUpload.get_presigned_url_for_fetch_by_s3_key(
                                attachment_data.s3_key
                            )
                            result = {
                                "get_url": presigned_url,
                                "file_type": attachment_data.file_type,
                                "key": attachment_data.id,
                            }
                            formatted_data.append(
                                {"type": "TEXT_BLOCK", "content": content, "s3Reference": result, "actor": actor}
                            )
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
