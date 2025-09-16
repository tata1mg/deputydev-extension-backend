"""
Unit tests for IdeReviewPreProcessor.

This module provides comprehensive unit tests for the IdeReviewPreProcessor class,
covering all methods including pre_process_pr, get_repo_id, run_validation, and 
_get_attachment_data_and_metadata with various scenarios including edge cases 
and error handling.
"""

from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.backend_common.models.dto.message_sessions_dto import MessageSessionData
from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import ChatAttachmentDataWithObjectBytes
from app.main.blueprints.deputy_dev.constants.constants import IdeReviewStatusTypes, ReviewType
from app.main.blueprints.deputy_dev.models.dto.ide_review_dto import IdeReviewDTO
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    FileWiseChanges,
    GetRepoIdRequest,
    ReviewRequest,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor import IdeReviewPreProcessor
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor_fixtures import *


class TestIdeReviewPreProcessorInitialization:
    """Test cases for IdeReviewPreProcessor initialization."""

    def test_initialization_default_values(self) -> None:
        """Test that IdeReviewPreProcessor initializes with correct default values."""
        processor = IdeReviewPreProcessor()
        
        assert processor.extension_repo_dto is None
        assert processor.session_id is None
        assert processor.review_dto is None
        assert processor.review_status == IdeReviewStatusTypes.IN_PROGRESS.value
        assert processor.is_valid is True


class TestIdeReviewPreProcessorGetAttachmentDataAndMetadata:
    """Test cases for IdeReviewPreProcessor._get_attachment_data_and_metadata method."""

    @pytest.mark.asyncio
    async def test_get_attachment_data_and_metadata_success(
        self,
        sample_attachment_data: MagicMock,
        sample_attachment_with_object_bytes: ChatAttachmentDataWithObjectBytes,
    ) -> None:
        """Test successful retrieval of attachment data and metadata."""
        attachment_id = 1
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ChatAttachmentsRepository') as mock_attachments_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ChatFileUpload') as mock_file_upload:
            
            # Setup mocks
            mock_attachments_repo.get_attachment_by_id = AsyncMock(return_value=sample_attachment_data)
            mock_file_upload.get_file_data_by_s3_key = AsyncMock(return_value=sample_attachment_with_object_bytes.object_bytes)
            
            # Execute
            processor = IdeReviewPreProcessor()
            result = await processor._get_attachment_data_and_metadata(attachment_id)
            
            # Verify
            assert isinstance(result, ChatAttachmentDataWithObjectBytes)
            assert result.attachment_metadata == sample_attachment_data
            assert result.object_bytes == sample_attachment_with_object_bytes.object_bytes
            mock_attachments_repo.get_attachment_by_id.assert_called_once_with(attachment_id=attachment_id)
            mock_file_upload.get_file_data_by_s3_key.assert_called_once_with(s3_key=sample_attachment_data.s3_key)

    @pytest.mark.asyncio
    async def test_get_attachment_data_and_metadata_attachment_not_found(
        self,
        invalid_attachment_id: int,
    ) -> None:
        """Test error handling when attachment is not found."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ChatAttachmentsRepository') as mock_attachments_repo:
            
            # Setup mocks
            mock_attachments_repo.get_attachment_by_id = AsyncMock(return_value=None)
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(ValueError, match=f"Attachment with id {invalid_attachment_id} not found"):
                await processor._get_attachment_data_and_metadata(invalid_attachment_id)
            
            mock_attachments_repo.get_attachment_by_id.assert_called_once_with(attachment_id=invalid_attachment_id)

    @pytest.mark.asyncio
    async def test_get_attachment_data_and_metadata_s3_error(
        self,
        sample_attachment_data: MagicMock,
    ) -> None:
        """Test error handling when S3 retrieval fails."""
        attachment_id = 1
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ChatAttachmentsRepository') as mock_attachments_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ChatFileUpload') as mock_file_upload:
            
            # Setup mocks
            mock_attachments_repo.get_attachment_by_id = AsyncMock(return_value=sample_attachment_data)
            mock_file_upload.get_file_data_by_s3_key = AsyncMock(side_effect=Exception("S3 error"))
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(Exception, match="S3 error"):
                await processor._get_attachment_data_and_metadata(attachment_id)
            
            mock_attachments_repo.get_attachment_by_id.assert_called_once_with(attachment_id=attachment_id)
            mock_file_upload.get_file_data_by_s3_key.assert_called_once_with(s3_key=sample_attachment_data.s3_key)


class TestIdeReviewPreProcessorGetRepoId:
    """Test cases for IdeReviewPreProcessor.get_repo_id method."""

    @pytest.mark.asyncio
    async def test_get_repo_id_success(
        self,
        sample_get_repo_id_request: GetRepoIdRequest,
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
    ) -> None:
        """Test successful retrieval of repo ID."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            
            # Execute
            processor = IdeReviewPreProcessor()
            result = await processor.get_repo_id(sample_get_repo_id_request, user_team_id)
            
            # Verify
            assert result == sample_repo_dto
            mock_user_team_repo.db_get.assert_called_once_with(filters={"id": user_team_id}, fetch_one=True)
            mock_repo_repo.find_or_create_extension_repo.assert_called_once_with(
                repo_name=sample_get_repo_id_request.repo_name,
                repo_origin=sample_get_repo_id_request.origin_url,
                team_id=sample_user_team.team_id
            )

    @pytest.mark.asyncio
    async def test_get_repo_id_user_team_not_found(
        self,
        sample_get_repo_id_request: GetRepoIdRequest,
        invalid_user_team_id: int,
    ) -> None:
        """Test error handling when user team is not found."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=None)
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(ValueError, match=f"User team with id {invalid_user_team_id} not found"):
                await processor.get_repo_id(sample_get_repo_id_request, invalid_user_team_id)
            
            mock_user_team_repo.db_get.assert_called_once_with(filters={"id": invalid_user_team_id}, fetch_one=True)

    @pytest.mark.asyncio
    async def test_get_repo_id_repo_creation_error(
        self,
        sample_get_repo_id_request: GetRepoIdRequest,
        sample_user_team: MagicMock,
    ) -> None:
        """Test error handling when repo creation fails."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(side_effect=Exception("Database error"))
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(Exception, match="Database error"):
                await processor.get_repo_id(sample_get_repo_id_request, user_team_id)
            
            mock_user_team_repo.db_get.assert_called_once_with(filters={"id": user_team_id}, fetch_one=True)
            mock_repo_repo.find_or_create_extension_repo.assert_called_once_with(
                repo_name=sample_get_repo_id_request.repo_name,
                repo_origin=sample_get_repo_id_request.origin_url,
                team_id=sample_user_team.team_id
            )


class TestIdeReviewPreProcessorRunValidation:
    """Test cases for IdeReviewPreProcessor.run_validation method."""

    @pytest.mark.asyncio
    async def test_run_validation_valid_diff(self) -> None:
        """Test validation with valid diff and token count."""
        processor = IdeReviewPreProcessor()
        review_diff = "valid diff content"
        token_count = 100
        
        await processor.run_validation(review_diff, token_count)
        
        assert processor.is_valid is True
        assert processor.review_status == IdeReviewStatusTypes.IN_PROGRESS.value

    @pytest.mark.asyncio
    async def test_run_validation_empty_diff(self) -> None:
        """Test validation with empty diff."""
        processor = IdeReviewPreProcessor()
        review_diff = ""
        token_count = 0
        
        await processor.run_validation(review_diff, token_count)
        
        assert processor.is_valid is False
        assert processor.review_status == IdeReviewStatusTypes.REJECTED_NO_DIFF.value

    @pytest.mark.asyncio
    async def test_run_validation_none_diff(self) -> None:
        """Test validation with None diff."""
        processor = IdeReviewPreProcessor()
        review_diff = None
        token_count = 0
        
        await processor.run_validation(review_diff, token_count)
        
        assert processor.is_valid is False
        assert processor.review_status == IdeReviewStatusTypes.REJECTED_NO_DIFF.value

    @pytest.mark.asyncio
    async def test_run_validation_large_token_count(self) -> None:
        """Test validation with token count exceeding limit."""
        processor = IdeReviewPreProcessor()
        review_diff = "valid diff content"
        token_count = 200000  # This exceeds MAX_PR_DIFF_TOKEN_LIMIT (150000)
        
        await processor.run_validation(review_diff, token_count)
        
        assert processor.is_valid is False
        assert processor.review_status == IdeReviewStatusTypes.REJECTED_LARGE_SIZE.value

    @pytest.mark.asyncio
    async def test_run_validation_empty_diff_with_large_tokens(self) -> None:
        """Test validation with empty diff and large token count (empty diff takes precedence)."""
        processor = IdeReviewPreProcessor()
        review_diff = ""
        token_count = 50000
        
        await processor.run_validation(review_diff, token_count)
        
        assert processor.is_valid is False
        assert processor.review_status == IdeReviewStatusTypes.REJECTED_NO_DIFF.value

    @pytest.mark.asyncio
    async def test_run_validation_scenarios(
        self,
        sample_validation_scenarios: List[Dict[str, Any]],
    ) -> None:
        """Test various validation scenarios."""
        for scenario in sample_validation_scenarios:
            processor = IdeReviewPreProcessor()
            
            await processor.run_validation(scenario["diff"], scenario["token_count"])
            
            assert processor.is_valid == scenario["expected_valid"], f"Failed for scenario: {scenario['name']}"
            assert processor.review_status == scenario["expected_status"], f"Failed for scenario: {scenario['name']}"


class TestIdeReviewPreProcessorPreProcessPr:
    """Test cases for IdeReviewPreProcessor.pre_process_pr method."""

    @pytest.mark.asyncio
    async def test_pre_process_pr_success(
        self,
        sample_pre_process_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
        sample_ide_review_dto: IdeReviewDTO,
        sample_combined_diff: str,
        sample_reviewed_files: List[str],
        expected_pre_process_result: Dict[str, Any],
    ) -> None:
        """Test successful pre-processing of PR."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeReviewCache') as mock_cache:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
            mock_ext_reviews_repo.db_insert = AsyncMock(return_value=sample_ide_review_dto)
            mock_cache.set = AsyncMock()
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 25
            diff_handler_instance.get_diff_token_count.return_value = 150
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute
            processor = IdeReviewPreProcessor()
            result = await processor.pre_process_pr(sample_pre_process_data, user_team_id)
            
            # Verify
            assert result == expected_pre_process_result
            assert processor.extension_repo_dto == sample_repo_dto
            assert processor.session_id == sample_message_session.id
            assert processor.review_dto == sample_ide_review_dto
            assert processor.is_valid is True
            assert processor.review_status == IdeReviewStatusTypes.IN_PROGRESS.value
            
            # Verify repository calls
            mock_user_team_repo.db_get.assert_called_once_with(filters={"id": user_team_id}, fetch_one=True)
            mock_repo_repo.find_or_create_extension_repo.assert_called_once()
            mock_session_repo.create_message_session.assert_called_once()
            mock_ext_reviews_repo.db_insert.assert_called_once()
            mock_cache.set.assert_called_once_with(key=str(sample_ide_review_dto.id), value=sample_combined_diff)

    @pytest.mark.asyncio
    async def test_pre_process_pr_with_empty_diff(
        self,
        sample_empty_diff_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
    ) -> None:
        """Test pre-processing with empty diff."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeReviewCache') as mock_cache:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
            
            # Create rejected review DTO
            rejected_review_dto = IdeReviewDTO(
                id=202,
                review_status=IdeReviewStatusTypes.REJECTED_NO_DIFF.value,
                repo_id=sample_repo_dto.id,
                user_team_id=user_team_id,
                loc=0,
                reviewed_files=["src/empty.py"],
                source_branch="feature/empty",
                target_branch="main",
                source_commit="empty123",
                target_commit="target456",
                meta_info={"tokens": 0},
                diff_s3_url="testing",
                session_id=sample_message_session.id,
                review_type=ReviewType.ALL.value
            )
            mock_ext_reviews_repo.db_insert = AsyncMock(return_value=rejected_review_dto)
            mock_cache.set = AsyncMock()
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 0
            diff_handler_instance.get_diff_token_count.return_value = 0
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute
            processor = IdeReviewPreProcessor()
            result = await processor.pre_process_pr(sample_empty_diff_data, user_team_id)
            
            # Verify
            assert result["review_id"] == rejected_review_dto.id
            assert result["session_id"] == sample_message_session.id
            assert result["repo_id"] == sample_repo_dto.id
            assert processor.is_valid is False
            assert processor.review_status == IdeReviewStatusTypes.REJECTED_NO_DIFF.value
            
            # Cache should not be set for invalid reviews
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_process_pr_with_large_diff(
        self,
        sample_large_pre_process_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
    ) -> None:
        """Test pre-processing with large diff exceeding token limits."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeReviewCache') as mock_cache:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
            
            # Create large size rejected review DTO
            large_rejected_review_dto = IdeReviewDTO(
                id=203,
                review_status=IdeReviewStatusTypes.REJECTED_LARGE_SIZE.value,
                repo_id=sample_repo_dto.id,
                user_team_id=user_team_id,
                loc=10000,
                reviewed_files=[f"src/large_file_{i}.py" for i in range(10)],
                source_branch="feature/large-feature",
                target_branch="main",
                source_commit="large123commit456",
                target_commit="target789commit012",
                meta_info={"tokens": 200000},
                diff_s3_url="testing",
                session_id=sample_message_session.id,
                review_type=ReviewType.ALL.value
            )
            mock_ext_reviews_repo.db_insert = AsyncMock(return_value=large_rejected_review_dto)
            mock_cache.set = AsyncMock()
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 10000
            diff_handler_instance.get_diff_token_count.return_value = 200000  # Exceeds MAX_PR_DIFF_TOKEN_LIMIT
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute
            processor = IdeReviewPreProcessor()
            result = await processor.pre_process_pr(sample_large_pre_process_data, user_team_id)
            
            # Verify
            assert result["review_id"] == large_rejected_review_dto.id
            assert processor.is_valid is False
            assert processor.review_status == IdeReviewStatusTypes.REJECTED_LARGE_SIZE.value
            
            # Cache should not be set for invalid reviews
            mock_cache.set.assert_not_called()

    @pytest.mark.asyncio
    async def test_pre_process_pr_user_team_not_found(
        self,
        sample_pre_process_data: Dict[str, Any],
        invalid_user_team_id: int,
    ) -> None:
        """Test pre-processing when user team is not found."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=None)
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 25
            diff_handler_instance.get_diff_token_count.return_value = 150
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(AttributeError):  # The actual error is AttributeError when trying to access team_id on None
                await processor.pre_process_pr(sample_pre_process_data, invalid_user_team_id)

    @pytest.mark.asyncio
    async def test_pre_process_pr_with_different_review_types(
        self,
        uncommitted_review_request: ReviewRequest,
        committed_review_request: ReviewRequest,
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
    ) -> None:
        """Test pre-processing with different review types."""
        user_team_id = 123
        
        test_cases = [
            {
                "request": uncommitted_review_request,
                "expected_type": ReviewType.UNCOMMITTED.value
            },
            {
                "request": committed_review_request,
                "expected_type": ReviewType.COMMITTED.value
            }
        ]
        
        for test_case in test_cases:
            with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
                 patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
                 patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
                 patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
                 patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler, \
                 patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeReviewCache') as mock_cache:
                
                # Setup mocks
                mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
                mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
                mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
                
                review_dto = IdeReviewDTO(
                    id=204,
                    review_status=IdeReviewStatusTypes.IN_PROGRESS.value,
                    repo_id=sample_repo_dto.id,
                    user_team_id=user_team_id,
                    loc=25,
                    reviewed_files=["src/models/user.py", "src/utils/helper.py"],
                    source_branch=test_case["request"].source_branch,
                    target_branch=test_case["request"].target_branch,
                    source_commit=test_case["request"].source_commit,
                    target_commit=test_case["request"].target_commit,
                    meta_info={"tokens": 150},
                    diff_s3_url="testing",
                    session_id=sample_message_session.id,
                    review_type=test_case["expected_type"]
                )
                mock_ext_reviews_repo.db_insert = AsyncMock(return_value=review_dto)
                mock_cache.set = AsyncMock()
                
                # Setup diff handler
                diff_handler_instance = MagicMock()
                diff_handler_instance.get_diff_loc.return_value = 25
                diff_handler_instance.get_diff_token_count.return_value = 150
                mock_diff_handler.return_value = diff_handler_instance
                
                # Convert request to dict format
                request_data = {
                    "repo_name": test_case["request"].repo_name,
                    "origin_url": test_case["request"].origin_url,
                    "source_branch": test_case["request"].source_branch,
                    "target_branch": test_case["request"].target_branch,
                    "source_commit": test_case["request"].source_commit,
                    "target_commit": test_case["request"].target_commit,
                    "diff_attachment_id": test_case["request"].diff_attachment_id,
                    "file_wise_diff": [
                        {
                            "file_path": change.file_path,
                            "file_name": change.file_name,
                            "status": change.status,
                            "line_changes": change.line_changes,
                            "diff": change.diff
                        } for change in test_case["request"].file_wise_diff
                    ],
                    "review_type": test_case["request"].review_type.value
                }
                
                # Execute
                processor = IdeReviewPreProcessor()
                result = await processor.pre_process_pr(request_data, user_team_id)
                
                # Verify
                assert result["review_id"] == review_dto.id
                assert processor.review_dto.review_type == test_case["expected_type"]

    @pytest.mark.asyncio
    async def test_pre_process_pr_database_error_during_session_creation(
        self,
        sample_pre_process_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
    ) -> None:
        """Test pre-processing when session creation fails."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(side_effect=Exception("Database error"))
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 25
            diff_handler_instance.get_diff_token_count.return_value = 150
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(Exception, match="Database error"):
                await processor.pre_process_pr(sample_pre_process_data, user_team_id)

    @pytest.mark.asyncio
    async def test_pre_process_pr_database_error_during_review_insertion(
        self,
        sample_pre_process_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
    ) -> None:
        """Test pre-processing when review insertion fails."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler:
            
            # Setup mocks
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
            mock_ext_reviews_repo.db_insert = AsyncMock(side_effect=Exception("Database insert error"))
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 25
            diff_handler_instance.get_diff_token_count.return_value = 150
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute and verify
            processor = IdeReviewPreProcessor()
            with pytest.raises(Exception, match="Database insert error"):
                await processor.pre_process_pr(sample_pre_process_data, user_team_id)


class TestIdeReviewPreProcessorIntegration:
    """Integration test cases for IdeReviewPreProcessor."""

    @pytest.mark.asyncio
    async def test_pre_process_pr_end_to_end_flow(
        self,
        sample_pre_process_data: Dict[str, Any],
        sample_user_team: MagicMock,
        sample_repo_dto: MagicMock,
        sample_message_session: MagicMock,
        sample_ide_review_dto: IdeReviewDTO,
    ) -> None:
        """Test complete end-to-end flow of pre_process_pr method."""
        user_team_id = 123
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.UserTeamRepository') as mock_user_team_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.RepoRepository') as mock_repo_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.MessageSessionsRepository') as mock_session_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.ExtensionReviewsRepository') as mock_ext_reviews_repo, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeDiffHandler') as mock_diff_handler, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.pre_processors.ide_review_pre_processor.IdeReviewCache') as mock_cache:
            
            # Setup complete mock chain
            mock_user_team_repo.db_get = AsyncMock(return_value=sample_user_team)
            mock_repo_repo.find_or_create_extension_repo = AsyncMock(return_value=sample_repo_dto)
            mock_session_repo.create_message_session = AsyncMock(return_value=sample_message_session)
            mock_ext_reviews_repo.db_insert = AsyncMock(return_value=sample_ide_review_dto)
            mock_cache.set = AsyncMock()
            
            # Setup diff handler
            diff_handler_instance = MagicMock()
            diff_handler_instance.get_diff_loc.return_value = 25
            diff_handler_instance.get_diff_token_count.return_value = 150
            mock_diff_handler.return_value = diff_handler_instance
            
            # Execute
            processor = IdeReviewPreProcessor()
            
            # Verify initial state
            assert processor.extension_repo_dto is None
            assert processor.session_id is None
            assert processor.review_dto is None
            assert processor.review_status == IdeReviewStatusTypes.IN_PROGRESS.value
            assert processor.is_valid is True
            
            # Execute pre-processing
            result = await processor.pre_process_pr(sample_pre_process_data, user_team_id)
            
            # Verify final state
            assert processor.extension_repo_dto == sample_repo_dto
            assert processor.session_id == sample_message_session.id
            assert processor.review_dto == sample_ide_review_dto
            assert processor.is_valid is True
            assert processor.review_status == IdeReviewStatusTypes.IN_PROGRESS.value
            
            # Verify result
            expected_result = {
                "review_id": sample_ide_review_dto.id,
                "session_id": sample_message_session.id,
                "repo_id": sample_repo_dto.id,
            }
            assert result == expected_result
            
            # Verify all components were called in correct order
            mock_user_team_repo.db_get.assert_called_once()
            mock_repo_repo.find_or_create_extension_repo.assert_called_once()
            mock_session_repo.create_message_session.assert_called_once()
            mock_diff_handler.assert_called_once()
            mock_ext_reviews_repo.db_insert.assert_called_once()
            mock_cache.set.assert_called_once()
            
            # Verify message session data structure
            session_call_args = mock_session_repo.create_message_session.call_args[1]
            session_data = session_call_args["message_session_data"]
            assert isinstance(session_data, MessageSessionData)
            assert session_data.user_team_id == user_team_id
            assert session_data.client.value == "BACKEND"
            assert session_data.client_version == "1.0.0"
            assert session_data.session_type == "EXTENSION_REVIEW"