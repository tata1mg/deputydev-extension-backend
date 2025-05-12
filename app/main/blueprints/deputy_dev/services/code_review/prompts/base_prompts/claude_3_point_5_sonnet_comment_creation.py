import re
import xml.etree.ElementTree as ET
from typing import Any, AsyncIterator, Dict, List, Tuple

from deputydev_core.utils.context_vars import get_context_value

from app.backend_common.exception.exception import ParseException
from app.backend_common.models.dto.message_thread_dto import (
    MessageData,
    TextBlockData,
    ToolUseRequestData,
)
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
                        raise ValueError("The XML string does not contain the expected comment elements.")

                    comments.append(
                        LLMCommentData(
                            comment=format_code_blocks(description_element.text),
                            corrective_code=(
                                corrective_code_element.text if corrective_code_element is not None else None
                            ),
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
        print(llm_response.content)
        final_content = cls.get_parsed_response_blocks(llm_response.content)

        return final_content

    @classmethod
    def get_parsed_response_blocks(
        cls, response_block: List[MessageData]
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        final_content: List[Dict[str, Any]] = []
        tool_use_map: Dict[str, Any] = {}
        for block in response_block:
            if isinstance(block, ToolUseRequestData):
                final_content.append(block)
                tool_use_map[block.content.tool_use_id] = ToolUseRequestData

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[Any]:
        raise NotImplementedError("Streaming is not supported for comments generation prompts")

    @classmethod
    def get_xml_review_comments_format(cls, bucket: str, agent_name: str, agent_focus_area: str = "") -> str:
        base_format = f"""<review>
            <comments>
            <comment>
            <description>Describe the {agent_focus_area} issue and make sure to enclose description within <![CDATA[ ]]> to avoid XML parsing errors. Don't provide any code block inside this field</description>"""

        if cls.is_corrective_code_enabled(agent_name=agent_name):
            base_format += """
            <corrective_code>Rewrite or create new (in case of missing) code, docstring or documentation for developer
            to directly use it.
            Add this section under <![CDATA[ ]]> for avoiding xml paring error.
            Set this value empty string if there is no suggestive code.
            </corrective_code>"""

        base_format += f"""
            <file_path>file path on which the comment is to be made</file_path>
            <line_number>line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`</line_number>
            <confidence_score>floating point confidence score of the comment between 0.0 to 1.0  upto 2 decimal points</confidence_score>
            <bucket>
            {bucket}
            </bucket>
            </comment>
            <!-- Repeat the <comment> block for each {agent_focus_area} issue found -->
            </comments>
            </review>"""

        return base_format

    @classmethod
    def is_corrective_code_enabled(cls, agent_name):
        agents_config = get_context_value("setting")["code_review_agent"]["agents"]

        return agents_config[agent_name].get("is_corrective_code_enabled", False)
