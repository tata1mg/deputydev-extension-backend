from typing import Any, Dict, List

from app.backend_common.models.dto.message_thread_dto import LLModels
from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import (
    AgentRunResult,
    AgentTypes,
)
from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import (
    CommentBuckets,
    ParsedAggregatedCommentData,
    ParsedCommentData,
)
from app.main.blueprints.deputy_dev.services.code_review.common.prompts.base_prompts.dataclasses.main import (
    LLMCommentData,
)


class CommentBlendingEngineFixtures:
    """Fixtures for CommentBlendingEngine tests."""

    @staticmethod
    def get_mock_setting() -> Dict[str, Any]:
        """Return mock setting configuration."""
        return {
            "code_review_agent": {
                "agents": {
                    "security_agent": {"confidence_score": 0.7},
                    "error_agent": {"confidence_score": 0.8},
                    "performance_agent": {"confidence_score": 0.6},
                }
            }
        }

    @staticmethod
    def get_agent_settings() -> Dict[str, Dict[str, str]]:
        """Return agent settings mapping."""
        return {
            "security_agent": {"agent_id": "security_001"},
            "error_agent": {"agent_id": "error_001"},
            "performance_agent": {"agent_id": "performance_001"},
        }

    @staticmethod
    def get_sample_llm_comments() -> Dict[str, AgentRunResult]:
        """Return sample LLM comments."""
        return {
            "security_agent": AgentRunResult(
                agent_name="security_agent",
                agent_type=AgentTypes.SECURITY,
                model=LLModels.CLAUDE_3_POINT_7_SONNET,
                agent_result={
                    "comments": [
                        LLMCommentData(
                            comment="Security vulnerability detected",
                            file_path="src/auth.py",
                            line_number="25",
                            confidence_score=0.8,
                            bucket="security",
                            corrective_code="# Use secure authentication",
                            rationale="Insecure authentication method",
                        )
                    ]
                },
                prompt_tokens_exceeded=False,
            )
        }

    @staticmethod
    def get_llm_comments_with_various_confidence() -> Dict[str, AgentRunResult]:
        """Return LLM comments with various confidence scores."""
        return {
            "security_agent": AgentRunResult(
                agent_name="security_agent",
                agent_type=AgentTypes.SECURITY,
                model=LLModels.CLAUDE_3_POINT_7_SONNET,
                agent_result={
                    "comments": [
                        LLMCommentData(
                            comment="High confidence comment",
                            file_path="src/main.py",
                            line_number="10",
                            confidence_score=0.9,
                            bucket="security",
                            corrective_code="# Secure code",
                            rationale="Clear security issue",
                        ),
                        LLMCommentData(
                            comment="Low confidence comment",
                            file_path="src/util.py",
                            line_number="5",
                            confidence_score=0.5,
                            bucket="security",
                            corrective_code="# Maybe secure",
                            rationale="Possible security issue",
                        ),
                    ]
                },
                prompt_tokens_exceeded=False,
            )
        }

    @staticmethod
    def get_parsed_comments() -> List[ParsedCommentData]:
        """Return list of parsed comments."""
        return [
            ParsedCommentData(
                file_path="src/main.py",
                line_number="10",
                comment="Test comment 1",
                buckets=[CommentBuckets(name="security", agent_id="sec_001")],
                confidence_score=0.8,
                corrective_code="# Fixed code",
                model="claude-3-sonnet",
                rationale="Test rationale",
                is_valid=None,
            ),
            ParsedCommentData(
                file_path="src/util.py",
                line_number="15",
                comment="Test comment 2",
                buckets=[CommentBuckets(name="error", agent_id="err_001")],
                confidence_score=0.7,
                corrective_code="# Another fix",
                model="claude-3-sonnet",
                rationale="Another rationale",
                is_valid=None,
            ),
        ]

    @staticmethod
    def get_parsed_comments_multiple_lines() -> List[ParsedCommentData]:
        """Return parsed comments with multiple comments on same line."""
        return [
            ParsedCommentData(
                file_path="src/main.py",
                line_number="10",
                comment="First comment on line 10",
                buckets=[CommentBuckets(name="security", agent_id="sec_001")],
                confidence_score=0.8,
                corrective_code="# Fix 1",
                model="claude-3-sonnet",
                rationale="Rationale 1",
            ),
            ParsedCommentData(
                file_path="src/main.py",
                line_number="10",
                comment="Second comment on line 10",
                buckets=[CommentBuckets(name="performance", agent_id="perf_001")],
                confidence_score=0.7,
                corrective_code="# Fix 2",
                model="claude-3-sonnet",
                rationale="Rationale 2",
            ),
            ParsedCommentData(
                file_path="src/util.py",
                line_number="20",
                comment="Single comment on line 20",
                buckets=[CommentBuckets(name="error", agent_id="err_001")],
                confidence_score=0.9,
                corrective_code="# Fix 3",
                model="claude-3-sonnet",
                rationale="Rationale 3",
            ),
        ]

    @staticmethod
    def get_validation_response() -> Dict[str, Any]:
        """Return validation response from LLM."""
        return {"comments": [{"is_valid": True}, {"is_valid": False}]}

    @staticmethod
    def get_mock_agent_result() -> AgentRunResult:
        """Return mock agent result."""
        return AgentRunResult(
            agent_name="comment_validator",
            agent_type=AgentTypes.COMMENT_VALIDATION,
            model=LLModels.GPT_4_POINT_1,
            agent_result={"comments": [{"is_valid": True}, {"is_valid": False}]},
            prompt_tokens_exceeded=False,
        )

    @staticmethod
    def get_aggregated_comments() -> Dict[str, Dict[str, ParsedAggregatedCommentData]]:
        """Return aggregated comments structure."""
        return {
            "src/main.py": {
                "10": ParsedAggregatedCommentData(
                    file_path="src/main.py",
                    line_number="10",
                    comments=["Comment 1", "Comment 2"],
                    buckets=[
                        CommentBuckets(name="security", agent_id="sec_001"),
                        CommentBuckets(name="performance", agent_id="perf_001"),
                    ],
                    agent_ids=["sec_001", "perf_001"],
                    corrective_code=["# Fix 1", "# Fix 2"],
                    confidence_scores=[0.8, 0.7],
                    model="claude-3-sonnet",
                    is_valid=True,
                    confidence_score=0.75,
                    rationales=["Rationale 1", "Rationale 2"],
                )
            },
            "src/util.py": {
                "20": ParsedAggregatedCommentData(
                    file_path="src/util.py",
                    line_number="20",
                    comments=["Single comment"],
                    buckets=[CommentBuckets(name="error", agent_id="err_001")],
                    agent_ids=["err_001"],
                    corrective_code=["# Fix 3"],
                    confidence_scores=[0.9],
                    model="claude-3-sonnet",
                    is_valid=True,
                    confidence_score=0.9,
                    rationales=["Rationale 3"],
                )
            },
        }

    @staticmethod
    def get_summarization_agent_result() -> AgentRunResult:
        """Return summarization agent result."""
        return AgentRunResult(
            agent_name="comment_summarizer",
            model=LLModels.GPT_4_POINT_1,
            agent_result={
                "comments": [
                    {
                        "file_path": "src/main.py",
                        "line_number": "10",
                        "comment": "Summarized comment for line 10",
                        "buckets": [CommentBuckets(name="security", agent_id="sec_001")],
                        "confidence_score": 0.75,
                        "corrective_code": "# Summarized fix",
                        "model": "gpt-4",
                        "is_valid": True,
                        "rationale": "Combined rationale",
                    }
                ]
            },
            prompt_tokens_exceeded=False,
        )

    @staticmethod
    def get_empty_llm_comments() -> Dict[str, AgentRunResult]:
        """Return empty LLM comments."""
        return {}

    @staticmethod
    def get_llm_comments_with_no_agent_result() -> Dict[str, AgentRunResult]:
        """Return LLM comments with None agent_result."""
        return {
            "security_agent": AgentRunResult(
                agent_name="security_agent",
                model=LLModels.CLAUDE_3_POINT_7_SONNET,
                agent_result=None,
                prompt_tokens_exceeded=False,
            )
        }

    @staticmethod
    def get_confidence_score_thresholds() -> Dict[str, float]:
        """Return confidence score thresholds for different agents."""
        return {"security_agent": 0.7, "error_agent": 0.8, "performance_agent": 0.6, "maintainability_agent": 0.5}

    @staticmethod
    def get_various_session_ids() -> List[int]:
        """Return various session IDs for testing."""
        return [1, 123, 456, 789, 0, -1, 9999999]
