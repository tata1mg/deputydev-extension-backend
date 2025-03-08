import asyncio
import json
import re
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple

from deputydev_core.utils.app_logger import AppLogger
from torpedo import CONFIG, Task

from app.backend_common.constants.constants import LLMProviders
from app.backend_common.exception import RetryException
from app.backend_common.exception.exception import ParseException
from app.backend_common.utils.formatting import (
    format_code_blocks,
    format_comment_bucket_name,
)


class BaseLLMProvider(ABC):
    """Abstract LLM interface"""

    def __init__(self, llm_type):
        self.llm_type = llm_type

    def create_bulk_tasks(self, prompts: List[Dict[str, str]]) -> list:
        if not prompts:
            return []
        tasks = [
            Task(
                self.get_llm_response(
                    self.build_llm_message(prompt),
                    prompt.get("model"),
                    prompt.get("structure_type"),
                    prompt.get("parse", False),  # default value for parse if false
                ),
                result_key=prompt["key"],
            )
            for prompt in prompts
        ]
        return tasks

    @abstractmethod
    def build_llm_message(self, prompt: Dict[str, str], previous_responses: List[Dict[str, str]] = []) -> str:
        """
        Formats the conversation as required by the specific LLM.
        Args:
            prompt (Dict[str, str]): A prompt object containing system and user messages.
        Returns:
            Any: Formatted conversation ready to be sent to the LLM.
        """
        raise NotImplementedError("Must implement format_conversation in subclass")

    @abstractmethod
    async def parse_response(self, response: Dict[str, Any]) -> Tuple[str, int, int]:
        """
        Parses the LLM response.
        Args:
            response : The raw response from the LLM.
        Returns:
            tuple: Parsed response, input tokens, and output tokens.
        """
        raise NotImplementedError("Must implement parse_response in subclass")

    async def call_service_client(self, messages: List[Dict[str, str]], model, response_type):
        """
        Calls the OpenAI service client.

        Args:
            messages (List[Dict[str, str]]): Formatted conversation messages.

        Returns:
            str: The response from the GPT model.
        """
        raise NotImplementedError()

    async def get_llm_response(
        self,
        conversation_message,
        model: str,
        structure_type: str,
        parse: bool = True,
        max_retry: int = 2,
    ) -> dict:
        """
        Gets the LLM response with retry mechanism.
        Args:
            conversation_message (Any): The conversation messages formatted for the LLM.
            model (str): The LLM model to use.
            structure_type (str): The type of response expected ("text", "json").
            parse (bool): If True, parse the response according to the structure_type. Default is True.
            max_retry (int): Number of retries in case of failure. Default is 2.
        Returns:
            tuple: Parsed response from the LLM and LLM response tokens type.
        """

        model_config = CONFIG.config.get("LLM_MODELS").get(model)
        last_exception = None
        for i in range(max_retry):
            try:
                llm_response = await self.call_service_client(
                    conversation_message, model_config.get("NAME"), structure_type
                )
                return await self.handle_response(llm_response, structure_type, parse, model)
            except (ParseException, ValueError) as e:
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry} {e}")
                last_exception = e
            except Exception as e:
                AppLogger.log_warn(f"Retry {i + 1}/{max_retry}  Error while fetching data from LLM: {e}")
                last_exception = e
                await asyncio.sleep(60)
            if i + 1 == max_retry:
                raise RetryException(f"Retried due to llm client call failed {last_exception}")

    def parse_json_response(self, response):
        if self.llm_type == LLMProviders.ANTHROPIC.value:
            json_match = re.search(r"\{.*\}", response, re.DOTALL)
            if json_match:
                response = json_match.group()
        parsed_response = json.loads(response)
        return parsed_response["comments"]

    def parse_xml_response(self, xml_string: str):
        review_content = None
        # Parse the XML string
        try:
            # Use regular expression to extract the content within <review> tags
            review_content = re.search(r"<review>.*?</review>", xml_string, re.DOTALL)

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
                return comments
            else:
                raise ValueError("The XML string does not contain the expected <review> tags.")

        except ET.ParseError as exception:
            raise ParseException(
                f"XML parsing error while decoding PR review comments data:  {xml_string}, exception: {exception}"
            )

    async def handle_response(self, llm_response: Any, structure_type: str, parse: bool, model: str) -> Dict[str, Any]:
        """
        Handles the LLM response based on whether parsing is required.
        Args:
            llm_response (Any): The raw LLM response.
            structure_type (str): The structure type of the response ('text' or 'json').
        Returns:
            Dict[str, Any]: Parsed response with input and output tokens.
        """
        response, input_tokens, output_tokens = await self.parse_response(llm_response)
        final_response = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "structure_type": structure_type,
            "model": model,
        }
        parsed_response = []
        if not parse:  # Text case
            parsed_response = format_code_blocks(response)
        elif structure_type == "json":
            parsed_response = self.parse_json_response(response)
        elif structure_type == "xml":
            parsed_response = self.parse_xml_response(response)
        final_response["response"] = parsed_response
        return final_response
