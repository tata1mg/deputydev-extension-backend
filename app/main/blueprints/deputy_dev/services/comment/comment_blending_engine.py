import asyncio
import json
from typing import List

from app.main.blueprints.deputy_dev.constants.constants import LLMModelNames
from app.main.blueprints.deputy_dev.loggers import AppLogger
from app.main.blueprints.deputy_dev.services.code_review.agent_services.openai.openai_comment_summarization_agent import (
    OpenAICommentSummarizationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.agent_services.openai.openai_comment_validation_agent import (
    OpenAICommentValidationAgent,
)
from app.main.blueprints.deputy_dev.services.code_review.context.context_service import (
    ContextService,
)
from app.main.blueprints.deputy_dev.services.llm.openai_llm import OpenaiLLM
from app.main.blueprints.deputy_dev.services.workspace.context_vars import (
    get_context_value,
)
from app.main.blueprints.deputy_dev.utils import extract_line_number_from_llm_response


class CommentBlendingEngine:
    def __init__(self, llm_comments: dict, context_service: ContextService):
        self.llm_comments = llm_comments
        self.llm_confidence_score_limit = self.get_confidence_score_limit()
        self.filtered_comments = []
        self.invalid_comments = []
        self.context_service = context_service

        self.llm_service = OpenaiLLM()
        self.MAX_RETRIES = 2

    @staticmethod
    def get_confidence_score_limit():
        llm_confidence_score_limit = {}
        for agent, setting in get_context_value("setting")["code_review_agent"]["agents"].items():
            llm_confidence_score_limit[agent] = {"confidence_score_limit": setting["confidence_score"]}
        return llm_confidence_score_limit

    async def blend_comments(self):
        # this function can contain other operations in future
        self.apply_agent_confidence_score_limit()
        await self.validate_comments()
        await self.process_all_comments()
        self.filtered_comments.extend(self.invalid_comments)
        return self.filtered_comments

    def apply_agent_confidence_score_limit(self):
        """
        Filters comments based on confidence score limit and reformats them to a standard list structure.
        """
        confidence_filtered_comments = []
        agent_settings = get_context_value("setting")["code_review_agent"]["agents"]
        for agent, data in self.llm_comments.items():
            confidence_threshold = self.llm_confidence_score_limit[agent]["confidence_score_limit"]
            comments = data.get("response", [])

            if not isinstance(comments, list) or not comments:
                continue

            for comment in comments:
                if comment["confidence_score"] >= confidence_threshold:
                    confidence_filtered_comments.append(
                        {
                            "file_path": comment["file_path"],
                            "line_number": comment["line_number"],
                            "comment": comment["comment"],
                            "buckets": [{"name": comment["bucket"], "agent_id": agent_settings[agent]["agent_id"]}],
                            "confidence_score": comment["confidence_score"],
                            "corrective_code": comment.get("corrective_code", ""),
                            "model": data.get("model"),
                            "is_valid": None,  # Default to None
                        }
                    )

        self.filtered_comments = confidence_filtered_comments

    async def validate_comments(self):
        """
        Validates each filtered comment against the PR diff using LLM.
        """
        if not self.filtered_comments:
            return

        validation_data = self.filtered_comments

        # Attempt validation with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                prompt = await OpenAICommentValidationAgent(self.context_service).get_system_n_user_prompt(
                    validation_data
                )
                if prompt.get("exceeds_tokens"):  # Case when we exceed tokens of gpt
                    return
                conversation_messages = self.llm_service.build_llm_message(prompt)
                response = await self.llm_service.call_service_client(
                    messages=conversation_messages,
                    model=LLMModelNames.GPT_4_O.value,
                    response_type=prompt.get("structure_type"),
                )
                self.filtered_comments = self.extract_validated_comments(
                    json.loads(response.choices[0].message.content)
                )
                return

            except json.JSONDecodeError as e:
                AppLogger.log_warn(
                    f"Retry {attempt + 1}/{self.MAX_RETRIES}  Json decode error in comments Re-Validation call: {str(e)}"
                )

            except asyncio.TimeoutError as timeout_err:
                AppLogger.log_warn(
                    f"Retry {attempt + 1}/{self.MAX_RETRIES}: Timeout error in comments Re-Validation call {str(timeout_err)}"
                )

            except Exception as e:
                AppLogger.log_warn(f"Retry {attempt + 1}/{self.MAX_RETRIES}  comments Re-Validation call: {str(e)}")

            if attempt == self.MAX_RETRIES - 1:
                AppLogger.log_warn(f"Comments Re-Validation failed after {self.MAX_RETRIES} attempts")
                break
            await asyncio.sleep(1)

    def extract_validated_comments(self, response_content: dict) -> List[dict]:
        """Extracts and returns validated comments from LLM validated comment response."""
        validated_comments = []
        for comment, validation in zip(self.filtered_comments, response_content.get("comments", [])):
            is_valid = validation.get("is_valid", None)
            comment["is_valid"] = is_valid

            if is_valid is False:
                self.invalid_comments.append(comment)
            else:
                # Collect valid or unvalidated comments in the Filterd comment list
                validated_comments.append(comment)
        return validated_comments

    def aggregate_comments_by_line(self):
        """
        Aggregates comments by file path and line number.

        Returns:
            dict: A dictionary where each file path maps to line numbers, and each line number maps to
                  a structure containing aggregated comments, buckets, and corrective codes.
        """
        aggregated_comments = {}

        for comment in self.filtered_comments:
            file_path = comment["file_path"]  # Extract the file path
            line_number = str(extract_line_number_from_llm_response(comment["line_number"]))

            # Create file wise and line wise mapping
            if file_path not in aggregated_comments:
                aggregated_comments[file_path] = {}
            if line_number not in aggregated_comments[file_path]:
                aggregated_comments[file_path][line_number] = {
                    "file_path": file_path,
                    "line_number": line_number,
                    "comments": [],
                    "buckets": [],
                    "agent_ids": [],
                    "corrective_code": [],
                    "confidence_scores": [],  # Will be used to calculate average confidence score of combined comments
                    "model": comment.get("model"),
                    "is_valid": comment["is_valid"],
                }

            # Add the single comment's data to the lists
            aggregated_comments[file_path][line_number]["comments"].append(comment["comment"])
            aggregated_comments[file_path][line_number]["buckets"].append(comment["buckets"][0])
            corrective_code = comment.get("corrective_code")
            aggregated_comments[file_path][line_number]["corrective_code"].append(
                corrective_code.strip() if corrective_code else ""
            )
            aggregated_comments[file_path][line_number]["confidence_scores"].append(comment["confidence_score"])

        return aggregated_comments

    def split_single_and_multi_comments(self):
        """
        Separates single-line comments from multi-line comments.
        """
        aggregated = self.aggregate_comments_by_line()
        single_comments = []
        multi_comments = []

        for file_path, lines in aggregated.items():
            for line_number, data in lines.items():
                if len(data["comments"]) == 1:
                    single_comments.append(
                        {
                            "file_path": file_path,
                            "line_number": line_number,
                            "comment": data["comments"][0],
                            "buckets": data["buckets"],
                            "corrective_code": data["corrective_code"][0] if data["corrective_code"] else "",
                            "confidence_score": data["confidence_scores"][0],
                            "model": data["model"],
                            "is_valid": data["is_valid"],
                        }
                    )
                else:
                    data["confidence_score"] = round(sum(data["confidence_scores"]) / len(data["confidence_scores"]), 2)
                    multi_comments.append(data)

        return {"single_comments": single_comments, "multi_comments": multi_comments}

    async def process_all_comments(self):
        """
        Processes all comments with a single LLM call and returns a unified list.
        """
        if not self.filtered_comments:
            return

        split_comments = self.split_single_and_multi_comments()
        single_comments = split_comments["single_comments"]
        multi_comments = split_comments["multi_comments"]

        # Process single comments
        processed_comments = [
            {
                "file_path": comment["file_path"],
                "line_number": comment["line_number"],
                "comment": comment["comment"],
                "buckets": comment["buckets"],
                "corrective_code": comment["corrective_code"],
                "confidence_score": comment["confidence_score"],
                "model": comment["model"],
                "is_valid": comment["is_valid"],
            }
            for comment in single_comments
        ]

        # If there are no multi-line comments, return just the single comments
        if not multi_comments:
            self.filtered_comments = processed_comments
            return

            # Attempt validation with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                prompt = await OpenAICommentSummarizationAgent(self.context_service).get_system_n_user_prompt(
                    multi_comments
                )
                if prompt.get("exceeds_tokens"):  # Case when we exceed tokens of gpt
                    return
                conversation_messages = self.llm_service.build_llm_message(prompt)
                response = await self.llm_service.call_service_client(
                    messages=conversation_messages,
                    model=LLMModelNames.GPT_4_O.value,
                    response_type=prompt.get("structure_type"),
                )
                summarized_comments = json.loads(response.choices[0].message.content)
                for comment in summarized_comments.get("comments", []):
                    comment["is_summarized"] = True
                processed_comments.extend(summarized_comments.get("comments"))

                self.filtered_comments = processed_comments
                return

            except json.JSONDecodeError as e:
                AppLogger.log_warn(
                    f"Retry {attempt + 1}/{self.MAX_RETRIES}  Json decode error during comment summarization: {str(e)}"
                )

            except asyncio.TimeoutError as timeout_err:
                AppLogger.log_warn(
                    f"Timeout on attempt {attempt + 1}/{self.MAX_RETRIES} during comment summarization: {str(timeout_err)}"
                )

            except Exception as e:
                AppLogger.log_warn(f"Retry {attempt + 1}/{self.MAX_RETRIES}  comments summarization call: {e}")
            if attempt == self.MAX_RETRIES - 1:

                AppLogger.log_warn(f"Summarization failed after {self.MAX_RETRIES} attempts")
                break
            await asyncio.sleep(1)
