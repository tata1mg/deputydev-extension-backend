import asyncio
import json
from typing import Any, Dict, List, Optional, Tuple

from deputydev_core.llm_handler.core.handler import LLMHandler
from deputydev_core.utils.app_logger import AppLogger

from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    CommentBuckets,
    ParsedAggregatedCommentData,
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.dataclasses.main import (
    PromptFeatures,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.agents.agent_factory import (
    AgentFactory,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.comments.dataclasses.main import (
    LLMCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from app.main.blueprints.deputy_dev.utils import extract_line_number_from_llm_response


class CommentBlendingEngine:
    def __init__(
        self,
        llm_comments: Dict[str, list[LLMCommentData]],
        context_service: IdeReviewContextService,
        llm_handler: LLMHandler[PromptFeatures],
        session_id: int,
        agents: Optional[List[UserAgentDTO]] = None,
    ) -> None:
        self.llm_comments = llm_comments
        self.llm_handler = llm_handler
        self.agents: Dict[str, UserAgentDTO] = {agent.agent_name: agent for agent in agents}
        self.filtered_comments: List[ParsedCommentData] = []
        self.invalid_comments: List[ParsedCommentData] = []
        self.context_service = context_service
        self.MAX_RETRIES = 2
        self.agent_results: Dict[str, list[LLMCommentData]] = {}
        self.session_id = session_id
        self.review_title = "Code Quality and Functionality Review"

    async def blend_comments(self) -> tuple[list[ParsedCommentData], dict[str, list], str]:
        # this function can contain other operations in future
        self.apply_agent_confidence_score_limit()
        await self.validate_comments()
        await self.process_all_comments()
        self.filtered_comments.extend(self.invalid_comments)
        return self.filtered_comments, self.agent_results, self.review_title

    def apply_agent_confidence_score_limit(self) -> None:
        """
        Filters comments based on confidence score limit and reformats them to a standard list structure.
        """
        confidence_filtered_comments: List[ParsedCommentData] = []
        for agent, comments in self.llm_comments.items():
            confidence_threshold = self.agents[agent].confidence_score
            comments: Optional[List[LLMCommentData]] = comments
            if not comments:
                continue

            for comment in comments:
                if comment.confidence_score >= confidence_threshold:
                    confidence_filtered_comments.append(
                        ParsedCommentData(
                            id=comment.id,
                            title=comment.title,
                            file_path=comment.file_path,
                            line_number=str(comment.line_number),
                            comment=comment.comment,
                            tag=comment.tag,
                            line_hash=comment.line_hash,
                            buckets=[
                                CommentBuckets(
                                    name=comment.bucket,
                                    agent_id=str(self.agents[agent].id),
                                )
                            ],
                            confidence_score=comment.confidence_score,
                            corrective_code=comment.corrective_code,
                            rationale=comment.rationale,
                        )
                    )

        self.filtered_comments = confidence_filtered_comments

    def extract_validated_comments(self, response_content: Dict[str, Any]) -> List[ParsedCommentData]:
        """Extracts and returns validated comments from LLM validated comment response."""
        validated_comments: List[ParsedCommentData] = []
        for comment, validation in zip(self.filtered_comments, response_content.get("comments", [])):
            is_valid = validation.get("is_valid", None)
            comment.is_valid = is_valid

            if is_valid is False:
                self.invalid_comments.append(comment)
            else:
                # Collect valid or unvalidated comments in the Filterd comment list
                validated_comments.append(comment)
        return validated_comments

    async def validate_comments(self) -> None:
        """
        Validates each filtered comment against the PR diff using LLM.
        """
        if not self.filtered_comments:
            return

        # Attempt validation with retries
        for attempt in range(self.MAX_RETRIES):
            try:
                comment_validation_agent = AgentFactory.comment_validation_agent(
                    self.context_service, self.filtered_comments, self.llm_handler
                )
                agent_result = await comment_validation_agent.run_agent(session_id=self.session_id)
                self.agent_results[agent_result.agent_name] = agent_result
                if agent_result.prompt_tokens_exceeded:  # Case when we exceed tokens of gpt
                    return

                if agent_result.agent_result is None:
                    raise ValueError("Agent result is None")

                self.filtered_comments = self.extract_validated_comments(agent_result.agent_result)
                self.review_title = agent_result.agent_result.get("title")
                return

            except json.JSONDecodeError as e:
                AppLogger.log_warn(
                    f"Retry {attempt + 1}/{self.MAX_RETRIES}  Json decode error in comments Re-Validation call: {str(e)}"
                )

            except asyncio.TimeoutError as timeout_err:
                AppLogger.log_warn(
                    f"Retry {attempt + 1}/{self.MAX_RETRIES}: Timeout error in comments Re-Validation call {str(timeout_err)}"
                )

            except Exception as e:  # noqa: BLE001
                AppLogger.log_warn(f"Retry {attempt + 1}/{self.MAX_RETRIES}  comments Re-Validation call: {str(e)}")

            if attempt == self.MAX_RETRIES - 1:
                AppLogger.log_warn(f"Comments Re-Validation failed after {self.MAX_RETRIES} attempts")
                break
            await asyncio.sleep(1)

    def aggregate_comments_by_line(self) -> Dict[str, Dict[str, ParsedAggregatedCommentData]]:
        """
        Aggregates comments by file path and line number.

        Returns:
            Dict[str, Dict[str, ParsedAggregatedCommentData]]: Aggregated comments.
        """
        aggregated_comments: Dict[str, Dict[str, ParsedAggregatedCommentData]] = {}

        for comment in self.filtered_comments:
            file_path = comment.file_path  # Extract the file path
            line_number = str(extract_line_number_from_llm_response(comment.line_number))

            # Create file wise and line wise mapping
            if file_path not in aggregated_comments:
                aggregated_comments[file_path] = {}
            if line_number not in aggregated_comments[file_path]:
                aggregated_comments[file_path][line_number] = ParsedAggregatedCommentData(
                    titles=[],
                    file_path=file_path,
                    line_number=line_number,
                    line_hash=comment.line_hash,
                    tags=[],
                    comments=[],
                    comment_ids=[],
                    buckets=[],
                    agent_ids=[],
                    corrective_code=[],
                    confidence_scores=[],
                    model=comment.model,
                    is_valid=comment.is_valid,
                    confidence_score=comment.confidence_score,
                    rationales=[],
                )

            # Add the single comment's data to the lists
            aggregated_comments[file_path][line_number].titles.append(comment.title)
            aggregated_comments[file_path][line_number].comments.append(comment.comment)
            aggregated_comments[file_path][line_number].comment_ids.append(comment.id)
            aggregated_comments[file_path][line_number].buckets.append(comment.buckets[0])
            aggregated_comments[file_path][line_number].tags.append(comment.tag)
            corrective_code = comment.corrective_code
            aggregated_comments[file_path][line_number].corrective_code.append(
                corrective_code.strip() if corrective_code else ""
            )
            aggregated_comments[file_path][line_number].confidence_scores.append(comment.confidence_score)
            aggregated_comments[file_path][line_number].rationales.append(comment.rationale)

        return aggregated_comments

    def split_single_and_multi_comments(self) -> Tuple[List[ParsedCommentData], List[ParsedAggregatedCommentData]]:
        """
        Separates single-line comments from multi-line comments.
        """
        aggregated = self.aggregate_comments_by_line()
        single_comments: List[ParsedCommentData] = []
        multi_comments: List[ParsedAggregatedCommentData] = []

        for file_path, lines in aggregated.items():
            for line_number, data in lines.items():
                if len(data.comments) == 1:
                    single_comments.append(
                        ParsedCommentData(
                            id=data.comment_ids[0],
                            title=data.titles[0],
                            file_path=file_path,
                            line_number=line_number,
                            line_hash=data.line_hash,
                            tag=data.tags[0],
                            comment=data.comments[0],
                            buckets=data.buckets,
                            corrective_code=data.corrective_code[0] if data.corrective_code else "",
                            confidence_score=data.confidence_scores[0],
                            model=data.model,
                            is_valid=data.is_valid,
                            rationale=data.rationales[0],
                        )
                    )
                else:
                    # Calculate the average confidence score for multi-line comments
                    data.confidence_score = round(sum(data.confidence_scores) / len(data.confidence_scores), 2)
                    multi_comments.append(data)

        return single_comments, multi_comments

    async def process_all_comments(self) -> None:
        """
        Processes all comments with a single LLM call and returns a unified list.
        """
        if not self.filtered_comments:
            return None

        single_comments, multi_comments = self.split_single_and_multi_comments()

        processed_comments = single_comments

        # If there are no multi-line comments, return just the single comments
        if not multi_comments:
            self.filtered_comments = processed_comments
            return

        # Attempt summarization with retries
        for attempt in range(self.MAX_RETRIES):
            comment_summarization_agent = AgentFactory.comment_summarization_agent(
                self.context_service, multi_comments, self.llm_handler
            )
            agent_result = await comment_summarization_agent.run_agent(session_id=self.session_id)
            self.agent_results[agent_result.agent_name] = agent_result
            if agent_result.prompt_tokens_exceeded:  # Case when we exceed tokens of gpt
                return

            if agent_result.agent_result is None:
                raise ValueError("Agent result is None")

            for comment in agent_result.agent_result["comments"]:
                processed_comments.append(
                    ParsedCommentData(
                        id=comment.get("id"),
                        title=comment.get("title"),
                        file_path=comment.get("file_path"),
                        line_number=comment.get("line_number"),
                        line_hash=comment.get("line_hash"),
                        tag=comment.get("tag"),
                        comment=comment.get("comment"),
                        buckets=comment.get("buckets"),
                        confidence_score=comment.get("confidence_score"),
                        corrective_code=comment.get("corrective_code"),
                        model=comment.get("model"),
                        is_valid=comment.get("is_valid"),
                        is_summarized=True,
                        rationale=comment.get("rationale"),
                    )
                )
            self.filtered_comments = processed_comments
            return
