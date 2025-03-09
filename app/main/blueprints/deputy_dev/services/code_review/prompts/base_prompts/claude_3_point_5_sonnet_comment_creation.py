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
from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)
from app.backend_common.exception.exception import ParseException
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)


class BaseClaude3Point5SonnetCommentCreationPrompt(BaseClaude3Point5SonnetPrompt):
    @classmethod
    def _parse_text_blocks(cls, text: str) -> Dict[str, List[LLMCommentData]]:
        review_content = None
        # Parse the XML string
        try:
            # Use regular expression to extract the content within <review> tags
            review_content = re.search(r"<review>.*?</review>", text, re.DOTALL)

            if review_content:
                xml_content = review_content.group(0)  # Extract matched XML content
                root = ET.fromstring(xml_content)

                comments: List[LLMCommentData] = []
                root_comments = root.find("comments")
                if root_comments is None:
                    raise ValueError("The XML string does not contain the expected <comments> tags.")

                for comment in root_comments.findall("comment"):
                    corrective_code_element = comment.find("corrective_code")
                    description_element = comment.find("description")
                    file_path_element = comment.find("file_path")
                    line_number_element = comment.find("line_number")
                    confidence_score_element = comment.find("confidence_score")
                    bucket_element = comment.find("bucket")

                    if (
                        description_element is None
                        or file_path_element is None
                        or line_number_element is None
                        or confidence_score_element is None
                        or bucket_element is None
                        or description_element.text is None
                        or file_path_element.text is None
                        or line_number_element.text is None
                        or confidence_score_element.text is None
                        or bucket_element.text is None
                    ):
                        print("XXXXXXXXXXXXXXXX")
                        print(description_element)
                        print(file_path_element)
                        print(line_number_element)
                        print(confidence_score_element)
                        print(bucket_element)
                        print("XXXXXXXXXXXXXXXX")
                        raise ValueError("The XML string does not contain the expected comment elements.")

                    comments.append(
                        LLMCommentData(
                            comment=format_code_blocks(description_element.text),
                            corrective_code=corrective_code_element.text
                            if corrective_code_element is not None
                            else None,
                            file_path=file_path_element.text,
                            line_number=line_number_element.text,
                            confidence_score=float(confidence_score_element.text),
                            bucket=format_comment_bucket_name(bucket_element.text),
                        )
                    )
                return {"comments": comments}
            else:
                raise ValueError("The XML string does not contain the expected <review> tags.")

        except ET.ParseError as exception:
            raise ParseException(
                f"XML parsing error while decoding PR review comments data:  {text}, exception: {exception}"
            )

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, List[LLMCommentData]]]:
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
