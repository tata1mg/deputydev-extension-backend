import re
import xml.etree.ElementTree as ET
from typing import Any, AsyncIterator, Dict, List

from app.backend_common.models.dto.message_thread_dto import TextBlockData
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
)
from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)
from app.common.exception.exception import ParseException


class BaseClaude3Point5SonnetCommentCreationPrompt(BaseClaude3Point5SonnetPrompt):
    @classmethod
    def _parse_text_blocks(cls, text: str) -> Dict[str, Any]:
        review_content = None
        # Parse the XML string
        try:
            # Use regular expression to extract the content within <review> tags
            review_content = re.search(r"<review>.*?</review>", text, re.DOTALL)

            if review_content:
                xml_content = review_content.group(0)  # Extract matched XML content
                root = ET.fromstring(xml_content)

                comments = []
                for comment in root.find("comments").findall("comment"):
                    comment_dict = {
                        "comment": format_code_blocks(comment.find("description").text),
                        "corrective_code": comment.find("corrective_code").text,
                        "file_path": comment.find("file_path").text,
                        "line_number": comment.find("line_number").text,
                        "confidence_score": float(comment.find("confidence_score").text),
                        "bucket": format_comment_bucket_name(comment.find("bucket").text),
                    }
                    comments.append(comment_dict)
                return {"data": comments}
            else:
                raise ValueError("The XML string does not contain the expected <review> tags.")

        except ET.ParseError as exception:
            raise ParseException(
                f"XML parsing error while decoding PR review comments data:  {text}, exception: {exception}"
            )

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:
        all_comments: List[Dict[str, Any]] = []
        for response_data in llm_response.content:
            if isinstance(response_data, TextBlockData):
                comments = cls._parse_text_blocks(response_data.content.text)
                if comments:
                    all_comments.append(comments)

        return all_comments

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming is not supported for comments generation prompts")
