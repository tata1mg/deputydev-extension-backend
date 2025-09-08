"""
Fixtures for testing IdeReviewPostProcessor.

This module provides comprehensive fixtures for testing various scenarios
of the IdeReviewPostProcessor methods including different input combinations,
mock data, and edge cases.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.main.blueprints.deputy_dev.constants.constants import IdeReviewCommentStatus
from app.main.blueprints.deputy_dev.models.dto.ide_reviews_comment_dto import IdeReviewsCommentDTO
from app.main.blueprints.deputy_dev.models.dto.user_agent_dto import UserAgentDTO
from app.main.blueprints.deputy_dev.services.code_review.ide_review.comments.dataclasses.main import LLMCommentData


@pytest.fixture
def sample_user_agent_dto() -> UserAgentDTO:
    """Create a sample UserAgentDTO for testing."""
    return UserAgentDTO(
        id=1,
        agent_name="security_agent",
        display_name="Security Agent",
        user_team_id=123,
        custom_prompt="Review code for security issues",
        confidence_score=0.8,
        objective="Find security vulnerabilities",
        is_custom_agent=False,
        is_deleted=False,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_user_agent_dto_2() -> UserAgentDTO:
    """Create a second sample UserAgentDTO for testing."""
    return UserAgentDTO(
        id=2,
        agent_name="performance_agent",
        display_name="Performance Agent",
        user_team_id=123,
        custom_prompt="Review code for performance issues",
        confidence_score=0.9,
        objective="Find performance bottlenecks",
        is_custom_agent=True,
        is_deleted=False,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_ide_reviews_comment_dto(sample_user_agent_dto: UserAgentDTO) -> IdeReviewsCommentDTO:
    """Create a sample IdeReviewsCommentDTO for testing."""
    return IdeReviewsCommentDTO(
        id=1,
        title="Security Issue",
        review_id=101,
        comment="This code is vulnerable to SQL injection",
        confidence_score=0.8,
        rationale="User input is not properly sanitized",
        corrective_code="Use parameterized queries instead",
        is_deleted=False,
        file_path="src/models/user.py",
        line_hash="abc123def456",
        line_number=25,
        tag="security",
        is_valid=True,
        agents=[sample_user_agent_dto],
        comment_status=IdeReviewCommentStatus.NOT_REVIEWED.value,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_ide_reviews_comment_dto_2(sample_user_agent_dto_2: UserAgentDTO) -> IdeReviewsCommentDTO:
    """Create a second sample IdeReviewsCommentDTO for testing."""
    return IdeReviewsCommentDTO(
        id=2,
        title="Performance Issue",
        review_id=101,
        comment="This loop can be optimized",
        confidence_score=0.9,
        rationale="Using nested loops for simple operations",
        corrective_code="Use built-in functions or list comprehensions",
        is_deleted=False,
        file_path="src/utils/helper.py",
        line_hash="def789ghi012",
        line_number=42,
        tag="performance",
        is_valid=True,
        agents=[sample_user_agent_dto_2],
        comment_status=IdeReviewCommentStatus.NOT_REVIEWED.value,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )


@pytest.fixture
def sample_llm_comment_data() -> LLMCommentData:
    """Create a sample LLMCommentData for testing.""" 
    return LLMCommentData(
        id=1,
        comment="This code is vulnerable to SQL injection",
        title="Security Issue",
        corrective_code="Use parameterized queries instead",
        file_path="src/models/user.py",
        line_number=25,
        line_hash="abc123def456",
        tag="security",
        confidence_score=0.8,
        rationale="User input is not properly sanitized",
        bucket="Security Agent"
    )


@pytest.fixture
def sample_llm_comment_data_without_id():
    """Create a sample LLMCommentData without ID for testing blended comments."""
    from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import CommentBuckets
    
    # Create a mock object that behaves like LLMCommentData but allows dynamic attributes
    comment = Mock()
    comment.id = None
    comment.comment = "Combined security and performance issue"
    comment.title = "Combined Issue"
    comment.corrective_code = "Use parameterized queries and optimize loops"
    comment.file_path = "src/models/user.py"
    comment.line_number = 25
    comment.line_hash = "abc123def456"
    comment.tag = "security,performance"
    comment.confidence_score = 0.85
    comment.rationale = "Multiple issues found in this code section"
    comment.bucket = "Combined Agent"
    comment.is_valid = True
    comment.buckets = [CommentBuckets(name="Combined Agent", agent_id="3")]
    
    return comment


@pytest.fixture
def sample_extension_review() -> Mock:
    """Create a mock extension review object."""
    review = Mock()
    review.id = 101
    review.session_id = "session-123"
    review.review_status = "In Progress"
    review.title = "Code Review"
    return review


@pytest.fixture
def sample_post_process_data() -> Dict[str, Any]:
    """Create sample data for post_process_pr method."""
    return {
        "review_id": 101,
        "user_team_id": 123,
        "additional_metadata": {"source": "IDE"}
    }


@pytest.fixture
def mock_extension_reviews_repository() -> MagicMock:
    """Create a mock ExtensionReviewsRepository."""
    repository = MagicMock()
    repository.db_get = AsyncMock()
    repository.update_review = AsyncMock()
    return repository


@pytest.fixture
def mock_ide_comment_repository() -> MagicMock:
    """Create a mock IdeCommentRepository."""
    repository = MagicMock()
    repository.get_review_comments = AsyncMock()
    repository.update_comments = AsyncMock()
    repository.insert_comments = AsyncMock()
    return repository


@pytest.fixture
def mock_user_agent_repository() -> MagicMock:
    """Create a mock UserAgentRepository."""
    repository = MagicMock()
    repository.db_get = AsyncMock()
    return repository


@pytest.fixture
def mock_llm_handler() -> MagicMock:
    """Create a mock LLMHandler."""
    handler = MagicMock()
    handler.start_llm_query = AsyncMock()
    return handler


@pytest.fixture
def mock_comment_blending_engine() -> MagicMock:
    """Create a mock CommentBlendingEngine."""
    engine = MagicMock()
    engine.blend_comments = AsyncMock()
    return engine


@pytest.fixture
def mock_ide_review_context_service() -> MagicMock:
    """Create a mock IdeReviewContextService."""
    service = MagicMock()
    return service


@pytest.fixture
def sample_formatted_comments(
    sample_llm_comment_data: LLMCommentData,
) -> Dict[str, List[LLMCommentData]]:
    """Create sample formatted comments dictionary."""
    return {
        "security_agent": [sample_llm_comment_data],
        "performance_agent": [sample_llm_comment_data]
    }


@pytest.fixture
def sample_filtered_comments(
    sample_llm_comment_data: LLMCommentData,
    sample_llm_comment_data_without_id
):
    """Create sample filtered comments list."""
    from app.main.blueprints.deputy_dev.services.code_review.common.comments.dataclasses.main import CommentBuckets
    
    # Create a mock object for existing comment with id
    existing_comment = Mock()
    existing_comment.id = sample_llm_comment_data.id
    existing_comment.comment = sample_llm_comment_data.comment
    existing_comment.title = sample_llm_comment_data.title
    existing_comment.corrective_code = sample_llm_comment_data.corrective_code
    existing_comment.file_path = sample_llm_comment_data.file_path
    existing_comment.line_number = sample_llm_comment_data.line_number
    existing_comment.line_hash = sample_llm_comment_data.line_hash
    existing_comment.tag = sample_llm_comment_data.tag
    existing_comment.confidence_score = sample_llm_comment_data.confidence_score
    existing_comment.rationale = sample_llm_comment_data.rationale
    existing_comment.bucket = sample_llm_comment_data.bucket
    existing_comment.is_valid = True
    existing_comment.buckets = [CommentBuckets(name="Security Agent", agent_id="1")]
    
    # sample_llm_comment_data_without_id is already a Mock
    
    return [existing_comment, sample_llm_comment_data_without_id]


@pytest.fixture
def sample_agent_results() -> List[Any]:
    """Create sample agent results."""
    return [
        {"agent_name": "security_agent", "score": 0.8},
        {"agent_name": "performance_agent", "score": 0.9}
    ]


@pytest.fixture
def sample_review_title() -> str:
    """Create sample review title."""
    return "Comprehensive Code Review"


@pytest.fixture
def empty_comments_list() -> List[IdeReviewsCommentDTO]:
    """Create an empty comments list for testing edge cases."""
    return []


@pytest.fixture
def invalid_post_process_data() -> Dict[str, Any]:
    """Create invalid data for testing error cases."""
    return {
        "invalid_key": "invalid_value"
    }


@pytest.fixture
def comments_with_multiple_agents(
    sample_user_agent_dto: UserAgentDTO,
    sample_user_agent_dto_2: UserAgentDTO
) -> List[IdeReviewsCommentDTO]:
    """Create comments with multiple agents for testing."""
    comment = IdeReviewsCommentDTO(
        id=1,
        title="Multi-Agent Issue",
        review_id=101,
        comment="This code has multiple issues",
        confidence_score=0.85,
        rationale="Found by multiple agents",
        corrective_code="Apply multiple fixes",
        is_deleted=False,
        file_path="src/models/user.py",
        line_hash="abc123def456",
        line_number=25,
        tag="security,performance",
        is_valid=True,
        agents=[sample_user_agent_dto, sample_user_agent_dto_2],
        comment_status=IdeReviewCommentStatus.NOT_REVIEWED.value,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )
    return [comment]


@pytest.fixture
def comments_with_no_agents() -> List[IdeReviewsCommentDTO]:
    """Create comments with no agents for testing edge cases."""
    comment = IdeReviewsCommentDTO(
        id=1,
        title="No Agent Issue",
        review_id=101,
        comment="This comment has no agents",
        confidence_score=0.5,
        rationale="System generated",
        corrective_code="Generic fix",
        is_deleted=False,
        file_path="src/models/user.py",
        line_hash="abc123def456", 
        line_number=25,
        tag="generic",
        is_valid=True,
        agents=[],
        comment_status=IdeReviewCommentStatus.NOT_REVIEWED.value,
        created_at=datetime(2023, 1, 1, 12, 0, 0),
        updated_at=datetime(2023, 1, 1, 12, 0, 0)
    )
    return [comment]


@pytest.fixture
def large_comments_dataset(
    sample_user_agent_dto: UserAgentDTO,
    sample_user_agent_dto_2: UserAgentDTO
) -> List[IdeReviewsCommentDTO]:
    """Create a large dataset of comments for performance testing."""
    comments = []
    for i in range(50):
        comment = IdeReviewsCommentDTO(
            id=i + 1,
            title=f"Issue {i + 1}",
            review_id=101,
            comment=f"This is comment number {i + 1}",
            confidence_score=0.5 + (i % 5) * 0.1,
            rationale=f"Rationale for issue {i + 1}",
            corrective_code=f"Fix for issue {i + 1}",
            is_deleted=False,
            file_path=f"src/module_{i % 10}.py",
            line_hash=f"hash{i:03d}",
            line_number=i + 10,
            tag=f"tag_{i % 3}",
            is_valid=True,
            agents=[sample_user_agent_dto if i % 2 == 0 else sample_user_agent_dto_2],
            comment_status=IdeReviewCommentStatus.NOT_REVIEWED.value,
            created_at=datetime(2023, 1, 1, 12, 0, 0),
            updated_at=datetime(2023, 1, 1, 12, 0, 0)
        )
        comments.append(comment)
    return comments