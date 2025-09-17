"""
Fixtures for testing IdeReviewPreProcessor.

This module provides comprehensive fixtures for testing various scenarios
of the IdeReviewPreProcessor methods including different input combinations,
mock data, and edge cases.
"""

from datetime import datetime
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock

import pytest

from app.backend_common.services.chat_file_upload.dataclasses.chat_file_upload import ChatAttachmentDataWithObjectBytes
from app.main.blueprints.deputy_dev.constants.constants import IdeReviewStatusTypes, ReviewType
from app.main.blueprints.deputy_dev.models.dto.ide_review_dto import IdeReviewDTO
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    FileWiseChanges,
    GetRepoIdRequest,
    ReviewRequest,
)


@pytest.fixture
def sample_get_repo_id_request() -> GetRepoIdRequest:
    """Create a sample GetRepoIdRequest for testing."""
    return GetRepoIdRequest(repo_name="test-repo", origin_url="https://github.com/test-org/test-repo.git")


@pytest.fixture
def sample_file_wise_changes() -> List[FileWiseChanges]:
    """Create sample FileWiseChanges for testing."""
    return [
        FileWiseChanges(
            file_path="src/models/user.py",
            file_name="user.py",
            status="modified",
            line_changes={"added": 10, "removed": 5},
            diff="""@@ -1,5 +1,10 @@
+import os
+import sys
 class User:
     def __init__(self, name: str):
         self.name = name
+        self.id = generate_id()
+    
+    def generate_id(self):
+        return os.urandom(16).hex()
""",
        ),
        FileWiseChanges(
            file_path="src/utils/helper.py",
            file_name="helper.py",
            status="created",
            line_changes={"added": 15, "removed": 0},
            diff=r"""@@ -0,0 +1,15 @@
+def format_name(name: str) -> str:
+    return name.strip().title()
+
+def validate_email(email: str) -> bool:
+    import re
+    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
+    return re.match(pattern, email) is not None
+
+def calculate_age(birth_year: int) -> int:
+    from datetime import datetime
+    current_year = datetime.now().year
+    return current_year - birth_year
+
+def get_file_extension(filename: str) -> str:
+    return filename.split('.')[-1] if '.' in filename else ''
""",
        ),
    ]


@pytest.fixture
def sample_review_request(sample_file_wise_changes: List[FileWiseChanges]) -> ReviewRequest:
    """Create a sample ReviewRequest for testing."""
    return ReviewRequest(
        repo_name="test-repo",
        origin_url="https://github.com/test-org/test-repo.git",
        source_branch="feature/new-feature",
        target_branch="main",
        source_commit="abc123def456",
        target_commit="def456ghi789",
        diff_attachment_id=None,
        file_wise_diff=sample_file_wise_changes,
        review_type=ReviewType.ALL,
    )


@pytest.fixture
def sample_large_review_request() -> ReviewRequest:
    """Create a large ReviewRequest that exceeds token limits."""
    large_diff = """@@ -1,100 +1,200 @@
""" + "\n".join(
        [
            f"+    line_{i} = 'This is a very long line of code that adds complexity to the codebase and might exceed token limits when combined with other similar lines'"
            for i in range(1000)
        ]
    )

    large_changes = [
        FileWiseChanges(
            file_path=f"src/large_file_{i}.py",
            file_name=f"large_file_{i}.py",
            status="created",
            line_changes={"added": 1000, "removed": 0},
            diff=large_diff,
        )
        for i in range(10)
    ]

    return ReviewRequest(
        repo_name="large-repo",
        origin_url="https://github.com/test-org/large-repo.git",
        source_branch="feature/large-feature",
        target_branch="main",
        source_commit="large123commit456",
        target_commit="target789commit012",
        diff_attachment_id=None,
        file_wise_diff=large_changes,
        review_type=ReviewType.ALL,
    )


@pytest.fixture
def sample_empty_diff_request() -> ReviewRequest:
    """Create a ReviewRequest with empty diff."""
    empty_changes = [
        FileWiseChanges(
            file_path="src/empty.py",
            file_name="empty.py",
            status="modified",
            line_changes={"added": 0, "removed": 0},
            diff="",
        )
    ]

    return ReviewRequest(
        repo_name="empty-repo",
        origin_url="https://github.com/test-org/empty-repo.git",
        source_branch="feature/empty",
        target_branch="main",
        source_commit="empty123",
        target_commit="target456",
        diff_attachment_id=None,
        file_wise_diff=empty_changes,
        review_type=ReviewType.ALL,
    )


@pytest.fixture
def sample_pre_process_data(sample_file_wise_changes: List[FileWiseChanges]) -> Dict[str, Any]:
    """Create sample data for pre_process_pr method."""
    return {
        "repo_name": "test-repo",
        "origin_url": "https://github.com/test-org/test-repo.git",
        "source_branch": "feature/new-feature",
        "target_branch": "main",
        "source_commit": "abc123def456",
        "target_commit": "def456ghi789",
        "diff_attachment_id": None,
        "file_wise_diff": [
            {
                "file_path": change.file_path,
                "file_name": change.file_name,
                "status": change.status,
                "line_changes": change.line_changes,
                "diff": change.diff,
            }
            for change in sample_file_wise_changes
        ],
        "review_type": ReviewType.ALL.value,
    }


@pytest.fixture
def sample_large_pre_process_data() -> Dict[str, Any]:
    """Create large sample data that exceeds token limits."""
    large_diff = """@@ -1,100 +1,200 @@
""" + "\n".join([f"+    line_{i} = 'This is a very long line of code that adds complexity'" for i in range(2000)])

    large_file_changes = [
        {
            "file_path": f"src/large_file_{i}.py",
            "file_name": f"large_file_{i}.py",
            "status": "created",
            "line_changes": {"added": 2000, "removed": 0},
            "diff": large_diff,
        }
        for i in range(10)
    ]

    return {
        "repo_name": "large-repo",
        "origin_url": "https://github.com/test-org/large-repo.git",
        "source_branch": "feature/large-feature",
        "target_branch": "main",
        "source_commit": "large123commit456",
        "target_commit": "target789commit012",
        "diff_attachment_id": None,
        "file_wise_diff": large_file_changes,
        "review_type": ReviewType.ALL.value,
    }


@pytest.fixture
def sample_empty_diff_data() -> Dict[str, Any]:
    """Create sample data with empty diff."""
    return {
        "repo_name": "empty-repo",
        "origin_url": "https://github.com/test-org/empty-repo.git",
        "source_branch": "feature/empty",
        "target_branch": "main",
        "source_commit": "empty123",
        "target_commit": "target456",
        "diff_attachment_id": None,
        "file_wise_diff": [
            {
                "file_path": "src/empty.py",
                "file_name": "empty.py",
                "status": "modified",
                "line_changes": {"added": 0, "removed": 0},
                "diff": "",
            }
        ],
        "review_type": ReviewType.ALL.value,
    }


@pytest.fixture
def sample_user_team() -> Mock:
    """Create a mock user team object."""
    team = Mock()
    team.id = 123
    team.team_id = 456
    team.user_id = 789
    team.role = "admin"
    return team


@pytest.fixture
def sample_repo_dto() -> Mock:
    """Create a mock repository DTO."""
    repo = Mock()
    repo.id = 101
    repo.name = "test-repo"
    repo.origin_url = "https://github.com/test-org/test-repo.git"
    repo.team_id = 456
    repo.is_active = True
    return repo


@pytest.fixture
def sample_message_session() -> Mock:
    """Create a mock message session."""
    session = Mock()
    session.id = 987
    session.user_team_id = 123
    session.client = "BACKEND"
    session.client_version = "1.0.0"
    session.session_type = "EXTENSION_REVIEW"
    session.created_at = datetime.now()
    return session


@pytest.fixture
def sample_ide_review_dto() -> IdeReviewDTO:
    """Create a sample IdeReviewDTO for testing."""
    return IdeReviewDTO(
        id=201,
        title=None,
        review_status=IdeReviewStatusTypes.IN_PROGRESS.value,
        repo_id=101,
        user_team_id=123,
        loc=25,
        reviewed_files=["src/models/user.py", "src/utils/helper.py"],
        source_branch="feature/new-feature",
        target_branch="main",
        source_commit="abc123def456",
        target_commit="def456ghi789",
        execution_time_seconds=None,
        fail_message=None,
        review_datetime=None,
        comments=[],
        feedback=None,
        is_deleted=False,
        deletion_datetime=None,
        meta_info={"tokens": 150},
        diff_s3_url="testing",
        session_id=987,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        review_type=ReviewType.ALL.value,
    )


@pytest.fixture
def sample_attachment_data() -> Mock:
    """Create sample attachment data."""
    from app.backend_common.models.dto.chat_attachments_dto import ChatAttachmentsDTO

    attachment = ChatAttachmentsDTO(
        id=1,
        s3_key="attachments/test_diff.txt",
        file_name="test_diff.txt",
        file_type="text/plain",
        status="uploaded",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    return attachment


@pytest.fixture
def sample_attachment_with_object_bytes(sample_attachment_data: Mock) -> ChatAttachmentDataWithObjectBytes:
    """Create sample attachment data with object bytes."""
    object_bytes = b"sample diff content here"
    return ChatAttachmentDataWithObjectBytes(attachment_metadata=sample_attachment_data, object_bytes=object_bytes)


@pytest.fixture
def mock_user_team_repository() -> MagicMock:
    """Create mock UserTeamRepository."""
    repository = MagicMock()
    repository.db_get = AsyncMock()
    return repository


@pytest.fixture
def mock_repo_repository() -> MagicMock:
    """Create mock RepoRepository."""
    repository = MagicMock()
    repository.find_or_create_extension_repo = AsyncMock()
    return repository


@pytest.fixture
def mock_message_sessions_repository() -> MagicMock:
    """Create mock MessageSessionsRepository."""
    repository = MagicMock()
    repository.create_message_session = AsyncMock()
    return repository


@pytest.fixture
def mock_extension_reviews_repository() -> MagicMock:
    """Create mock ExtensionReviewsRepository."""
    repository = MagicMock()
    repository.db_insert = AsyncMock()
    return repository


@pytest.fixture
def mock_chat_attachments_repository() -> MagicMock:
    """Create mock ChatAttachmentsRepository."""
    repository = MagicMock()
    repository.get_attachment_by_id = AsyncMock()
    return repository


@pytest.fixture
def mock_chat_file_upload() -> MagicMock:
    """Create mock ChatFileUpload."""
    service = MagicMock()
    service.get_file_data_by_s3_key = AsyncMock()
    return service


@pytest.fixture
def mock_ide_diff_handler() -> MagicMock:
    """Create mock IdeDiffHandler."""
    handler = MagicMock()
    handler.get_diff_loc = MagicMock(return_value=25)
    handler.get_diff_token_count = MagicMock(return_value=150)
    return handler


@pytest.fixture
def mock_ide_review_cache() -> MagicMock:
    """Create mock IdeReviewCache."""
    cache = MagicMock()
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def invalid_user_team_id() -> int:
    """Invalid user team ID for testing error cases."""
    return 999999


@pytest.fixture
def invalid_attachment_id() -> int:
    """Invalid attachment ID for testing error cases."""
    return 999999


@pytest.fixture
def sample_combined_diff(sample_file_wise_changes: List[FileWiseChanges]) -> str:
    """Create sample combined diff string."""
    return "".join([change.diff for change in sample_file_wise_changes])


@pytest.fixture
def sample_reviewed_files(sample_file_wise_changes: List[FileWiseChanges]) -> List[str]:
    """Create sample list of reviewed files."""
    return [change.file_path for change in sample_file_wise_changes]


@pytest.fixture
def uncommitted_review_request(sample_file_wise_changes: List[FileWiseChanges]) -> ReviewRequest:
    """Create a ReviewRequest for uncommitted changes only."""
    return ReviewRequest(
        repo_name="test-repo",
        origin_url="https://github.com/test-org/test-repo.git",
        source_branch="feature/uncommitted",
        target_branch="main",
        source_commit="uncommitted123",
        target_commit="target456",
        diff_attachment_id=None,
        file_wise_diff=sample_file_wise_changes,
        review_type=ReviewType.UNCOMMITTED,
    )


@pytest.fixture
def committed_review_request(sample_file_wise_changes: List[FileWiseChanges]) -> ReviewRequest:
    """Create a ReviewRequest for committed changes only."""
    return ReviewRequest(
        repo_name="test-repo",
        origin_url="https://github.com/test-org/test-repo.git",
        source_branch="feature/committed",
        target_branch="main",
        source_commit="committed123",
        target_commit="target456",
        diff_attachment_id=None,
        file_wise_diff=sample_file_wise_changes,
        review_type=ReviewType.COMMITTED,
    )


@pytest.fixture
def review_request_with_attachment_id(sample_file_wise_changes: List[FileWiseChanges]) -> ReviewRequest:
    """Create a ReviewRequest with attachment ID."""
    return ReviewRequest(
        repo_name="test-repo",
        origin_url="https://github.com/test-org/test-repo.git",
        source_branch="feature/with-attachment",
        target_branch="main",
        source_commit="attachment123",
        target_commit="target456",
        diff_attachment_id="1",
        file_wise_diff=sample_file_wise_changes,
        review_type=ReviewType.ALL,
    )


@pytest.fixture
def sample_validation_scenarios() -> List[Dict[str, Any]]:
    """Create various validation scenarios for testing."""
    return [
        {
            "name": "valid_small_diff",
            "diff": "small diff content",
            "token_count": 100,
            "expected_valid": True,
            "expected_status": IdeReviewStatusTypes.IN_PROGRESS.value,
        },
        {
            "name": "empty_diff",
            "diff": "",
            "token_count": 0,
            "expected_valid": False,
            "expected_status": IdeReviewStatusTypes.REJECTED_NO_DIFF.value,
        },
        {
            "name": "large_diff_exceeds_limit",
            "diff": "large diff content" * 1000,
            "token_count": 200000,  # This exceeds MAX_PR_DIFF_TOKEN_LIMIT (150000)
            "expected_valid": False,
            "expected_status": IdeReviewStatusTypes.REJECTED_LARGE_SIZE.value,
        },
        {
            "name": "none_diff",
            "diff": None,
            "token_count": 0,
            "expected_valid": False,
            "expected_status": IdeReviewStatusTypes.REJECTED_NO_DIFF.value,
        },
    ]


@pytest.fixture
def expected_pre_process_result() -> Dict[str, Any]:
    """Expected result from successful pre_process_pr method."""
    return {"review_id": 201, "session_id": 987, "repo_id": 101}
