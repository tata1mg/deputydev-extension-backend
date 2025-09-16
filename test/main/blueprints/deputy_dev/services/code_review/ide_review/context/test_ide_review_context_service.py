from unittest.mock import AsyncMock, Mock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service import (
    IdeReviewContextService,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service_fixtures import (
    IdeReviewContextServiceFixtures,
)


class TestIdeReviewContextService:
    """Test cases for IdeReviewContextService class."""

    def test_init(self) -> None:
        """Test IdeReviewContextService initialization."""
        # Arrange
        review_id = 123

        # Act
        service = IdeReviewContextService(review_id=review_id)

        # Assert
        assert service.review_id == review_id

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_success_without_line_numbers(self, mock_cache: Mock) -> None:
        """Test get_pr_diff returns diff without line numbers."""
        # Arrange
        review_id = 123
        expected_diff = IdeReviewContextServiceFixtures.get_sample_pr_diff()
        mock_cache.get = AsyncMock(return_value=expected_diff)

        service = IdeReviewContextService(review_id=review_id)

        # Act
        result = await service.get_pr_diff(append_line_no_info=False)

        # Assert
        assert result == expected_diff
        mock_cache.get.assert_called_once_with("123")

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.append_line_numbers"
    )
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_success_with_line_numbers(
        self, mock_cache: Mock, mock_append_line_numbers: Mock
    ) -> None:
        """Test get_pr_diff returns diff with line numbers."""
        # Arrange
        review_id = 456
        original_diff = IdeReviewContextServiceFixtures.get_sample_pr_diff()
        expected_diff_with_lines = IdeReviewContextServiceFixtures.get_sample_pr_diff_with_line_numbers()

        mock_cache.get = AsyncMock(return_value=original_diff)
        mock_append_line_numbers.return_value = expected_diff_with_lines

        service = IdeReviewContextService(review_id=review_id)

        # Act
        result = await service.get_pr_diff(append_line_no_info=True)

        # Assert
        assert result == expected_diff_with_lines
        mock_cache.get.assert_called_once_with("456")
        mock_append_line_numbers.assert_called_once_with(original_diff)

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_cache_miss_raises_value_error(self, mock_cache: Mock) -> None:
        """Test get_pr_diff raises ValueError when cache miss occurs."""
        # Arrange
        review_id = 789
        mock_cache.get = AsyncMock(return_value=None)

        service = IdeReviewContextService(review_id=review_id)

        # Act & Assert
        with pytest.raises(ValueError, match=f"PR diff not found in cache for review_id={review_id}"):
            await service.get_pr_diff()

        mock_cache.get.assert_called_once_with("789")

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_default_append_line_no_info_false(self, mock_cache: Mock) -> None:
        """Test get_pr_diff defaults to append_line_no_info=False."""
        # Arrange
        review_id = 111
        expected_diff = IdeReviewContextServiceFixtures.get_sample_pr_diff()
        mock_cache.get = AsyncMock(return_value=expected_diff)

        service = IdeReviewContextService(review_id=review_id)

        # Act
        result = await service.get_pr_diff()

        # Assert
        assert result == expected_diff
        mock_cache.get.assert_called_once_with("111")

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_cache_key_format(self, mock_cache: Mock) -> None:
        """Test get_pr_diff uses correct cache key format."""
        # Arrange
        review_id = 999
        expected_diff = IdeReviewContextServiceFixtures.get_sample_pr_diff()
        mock_cache.get = AsyncMock(return_value=expected_diff)

        service = IdeReviewContextService(review_id=review_id)

        # Act
        await service.get_pr_diff()

        # Assert
        mock_cache.get.assert_called_once_with("999")

    @pytest.mark.asyncio
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.append_line_numbers"
    )
    @patch(
        "app.main.blueprints.deputy_dev.services.code_review.ide_review.context.ide_review_context_service.IdeReviewCache"
    )
    async def test_get_pr_diff_append_line_numbers_called_conditionally(
        self, mock_cache: Mock, mock_append_line_numbers: Mock
    ) -> None:
        """Test append_line_numbers is called only when append_line_no_info=True."""
        # Arrange
        review_id = 222
        original_diff = IdeReviewContextServiceFixtures.get_sample_pr_diff()
        mock_cache.get = AsyncMock(return_value=original_diff)

        service = IdeReviewContextService(review_id=review_id)

        # Act - Test with append_line_no_info=False
        await service.get_pr_diff(append_line_no_info=False)

        # Assert
        mock_append_line_numbers.assert_not_called()

        # Act - Test with append_line_no_info=True
        await service.get_pr_diff(append_line_no_info=True)

        # Assert
        mock_append_line_numbers.assert_called_once_with(original_diff)
