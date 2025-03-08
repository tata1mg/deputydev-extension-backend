import re
import xml.etree.ElementTree as ET
from typing import Any, Dict

from app.backend_common.services.llm.providers.anthropic.prompts.base_prompts.claude_3_point_5_sonnet import (
    BaseClaude3Point5SonnetPrompt,
)
from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)
from app.common.exception.exception import ParseException
from app.main.blueprints.deputy_dev.services.code_review.prompts.base_code_review_prompt import (
    BaseCodeReviewPrompt,
)


class Claude3Point5XMLDataResponsePrompt(BaseCodeReviewPrompt, BaseClaude3Point5SonnetPrompt):
    def get_parsed_result(self, llm_response: str) -> Dict[str, Any]:
        review_content = None
        # Parse the XML string
        try:
            # Use regular expression to extract the content within <review> tags
            review_content = re.search(r"<review>.*?</review>", llm_response, re.DOTALL)

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
                f"XML parsing error while decoding PR review comments data:  {llm_response}, exception: {exception}"
            )
