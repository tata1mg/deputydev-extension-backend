"""
Test to verify that query ID consistency is maintained between streaming and response metadata.
This test ensures that the query ID used in the stream matches the query ID in the response metadata.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

from app.backend_common.utils.dataclasses.main import AuthData, ClientData
from app.main.blueprints.one_dev.services.query_solver.core.core_processor import CoreProcessor
from app.main.blueprints.one_dev.services.query_solver.dataclasses.main import (
    LLMModel,
    QuerySolverInput,
    ResponseMetadataContent,
)
from app.main.blueprints.one_dev.services.query_solver.query_solver import QuerySolver
from app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler import StreamHandler


class MockStreamMessage(BaseModel):
    """Mock stream message for testing."""
    type: str
    data: dict = {}


class TestQueryIdConsistency:
    """Test suite for verifying query ID consistency across the system."""
    
    @pytest.fixture
    def sample_payload(self):
        """Create a sample QuerySolverInput payload for testing."""
        return QuerySolverInput(
            query="Test query",
            session_id=12345,
            user_team_id=1,
            session_type="test",
            llm_model=LLMModel.GPT_4_POINT_1,
            os_name="macOS",
            shell="zsh",
        )
    
    @pytest.fixture
    def client_data(self):
        """Create sample client data."""
        return ClientData(
            user_id=1,
            user_team_id=1,
            user_name="test_user",
            client_version="1.0.0",
            client_type="vscode",
        )
    
    @pytest.fixture
    def auth_data(self):
        """Create sample auth data."""
        return AuthData(
            user_id=1,
            user_team_id=1,
            session_refresh_token=None,
        )

    @patch('app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler.StreamHandler.push_to_stream')
    @patch('app.main.blueprints.one_dev.services.query_solver.core.core_processor.CoreProcessor.solve_query')
    async def test_query_id_consistency_in_streaming_flow(
        self, 
        mock_solve_query,
        mock_push_to_stream,
        sample_payload,
        client_data,
    ):
        """
        Test that the query ID used in streaming matches the one in response metadata.
        """
        # Setup the test query ID
        test_query_id = "test_query_id_12345"
        
        # Mock the response metadata content with the query ID
        class MockResponseMetadata(BaseModel):
            content: ResponseMetadataContent
            type: str = "RESPONSE_METADATA"
        
        # Create a mock stream iterator that yields response metadata
        async def mock_stream_iterator():
            yield MockResponseMetadata(
                content=ResponseMetadataContent(
                    query_id=test_query_id,
                    session_id=sample_payload.session_id
                ),
                type="RESPONSE_METADATA"
            )
        
        # Configure the mock to return our iterator
        mock_solve_query.return_value = mock_stream_iterator()
        
        # Create CoreProcessor instance and call solve_query_with_streaming
        core_processor = CoreProcessor()
        
        # Test that when we call solve_query_with_streaming with a specific query_id,
        # the same query_id is used throughout the chain
        await core_processor.solve_query_with_streaming(
            payload=sample_payload,
            client_data=client_data,
            query_id=test_query_id,
        )
        
        # Verify that solve_query was called with the correct query_id
        mock_solve_query.assert_called_once()
        call_args = mock_solve_query.call_args
        
        # Check that query_id was passed to solve_query
        assert call_args.kwargs['query_id'] == test_query_id
        
        # Verify that push_to_stream was called with the same query_id as stream_id
        push_calls = mock_push_to_stream.call_args_list
        assert len(push_calls) >= 1  # At least the initialization event
        
        # Check that all stream pushes used the correct stream_id (query_id)
        for call in push_calls:
            assert call.kwargs['stream_id'] == test_query_id

    @patch('app.main.blueprints.one_dev.services.query_solver.core.core_processor.CoreProcessor._handle_new_query')
    async def test_query_id_passed_to_handle_new_query(
        self,
        mock_handle_new_query,
        sample_payload,
        client_data,
    ):
        """
        Test that query_id is correctly passed from solve_query to _handle_new_query.
        """
        test_query_id = "test_query_id_54321"
        
        # Mock the _handle_new_query method
        async def mock_iterator():
            yield MockStreamMessage(type="test", data={"query_id": test_query_id})
        
        mock_handle_new_query.return_value = mock_iterator()
        
        # Create CoreProcessor and call solve_query with a specific query_id
        core_processor = CoreProcessor()
        
        result = await core_processor.solve_query(
            payload=sample_payload,
            client_data=client_data,
            query_id=test_query_id,
        )
        
        # Consume the iterator to trigger the call
        async for item in result:
            pass
        
        # Verify that _handle_new_query was called with the query_id
        mock_handle_new_query.assert_called_once()
        call_args = mock_handle_new_query.call_args
        assert call_args.args[6] == test_query_id  # query_id is the 7th positional argument

    @patch('app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler.StreamHandler.stream_from')
    @patch('app.main.blueprints.one_dev.services.query_solver.query_solver.QuerySolver.start_query_solver_with_task')
    async def test_stream_id_matches_query_id_in_websocket_flow(
        self,
        mock_start_query_solver_with_task,
        mock_stream_from,
        sample_payload,
        client_data,
        auth_data,
    ):
        """
        Test that in the WebSocket flow, the stream_id used for StreamHandler.stream_from
        matches the query_id returned by start_query_solver_with_task.
        """
        test_query_id = "websocket_test_query_id"
        
        # Mock the start_query_solver_with_task to return our test query_id
        mock_task = AsyncMock()
        mock_start_query_solver_with_task.return_value = (test_query_id, mock_task)
        
        # Mock the stream_from method
        async def mock_stream_iterator():
            yield MockStreamMessage(type="test", data={"query_id": test_query_id})
        
        mock_stream_from.return_value = mock_stream_iterator
        
        # Mock WebSocket
        mock_ws = AsyncMock()
        
        # Create QuerySolver and execute query processing
        query_solver = QuerySolver()
        
        # Mock the _wait_for_stream_initialization method to avoid Redis dependency
        with patch.object(query_solver, '_wait_for_stream_initialization', return_value=None):
            await query_solver.execute_query_processing(
                payload=sample_payload,
                client_data=client_data,
                auth_data=auth_data,
                ws=mock_ws,
            )
        
        # Verify that stream_from was called with the same query_id as stream_id
        mock_stream_from.assert_called_once()
        call_args = mock_stream_from.call_args
        assert call_args.kwargs['stream_id'] == test_query_id

    def test_query_id_generation_uniqueness(self):
        """
        Test that generated query IDs are unique.
        """
        query_ids = set()
        
        # Generate multiple query IDs and ensure they're unique
        for _ in range(100):
            query_id = uuid4().hex
            assert query_id not in query_ids
            query_ids.add(query_id)
        
        assert len(query_ids) == 100

    @patch('app.main.blueprints.one_dev.services.query_solver.stream_handler.stream_handler.StreamHandler._redis_xread')
    async def test_stream_handler_uses_correct_stream_key(self, mock_redis_xread):
        """
        Test that StreamHandler uses the correct stream key based on the stream_id.
        """
        test_stream_id = "test_stream_12345"
        
        # Mock Redis response
        mock_redis_xread.return_value = []
        
        # Get stream iterator
        stream_iterator = StreamHandler.stream_from(stream_id=test_stream_id, offset_id="0")
        
        # Try to consume one item (this will trigger the Redis call)
        try:
            async for item in stream_iterator():
                break
        except Exception:
            pass  # We expect this to fail due to mocking, but we want to check the call
        
        # Verify that Redis was called with the correct stream key
        expected_stream_key = StreamHandler._get_stream_key(test_stream_id)
        mock_redis_xread.assert_called()
        call_args = mock_redis_xread.call_args
        streams_dict = call_args.args[0]
        assert expected_stream_key in streams_dict


if __name__ == "__main__":
    pytest.main([__file__])