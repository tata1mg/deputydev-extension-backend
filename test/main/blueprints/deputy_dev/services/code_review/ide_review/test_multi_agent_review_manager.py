"""
Unit tests for MultiAgentWebSocketManager.

This module provides comprehensive unit tests for the MultiAgentWebSocketManager class,
covering all methods including execute_agent_task, process_request, process_multiple_agents_with_cache_pattern,
and execute_and_stream_agent with various scenarios including edge cases and error handling.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.main.blueprints.deputy_dev.services.code_review.common.agents.dataclasses.main import AgentTypes
from app.main.blueprints.deputy_dev.services.code_review.ide_review.dataclass.main import (
    AgentRequestItem,
    RequestType,
    WebSocketMessage,
)
from app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager import (
    MultiAgentWebSocketManager,
)
from test.fixtures.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager_fixtures import *


class TestMultiAgentWebSocketManagerInitialization:
    """Test cases for MultiAgentWebSocketManager initialization."""

    def test_init_with_default_parameters(self) -> None:
        """Test initialization with default parameters."""
        manager = MultiAgentWebSocketManager(
            connection_id="test-conn-123",
            review_id=456
        )
        
        assert manager.connection_id == "test-conn-123"
        assert manager.review_id == 456
        assert manager.is_local is False
        assert manager.connection_id_gone is False

    def test_init_with_local_flag(self) -> None:
        """Test initialization with local testing flag."""
        manager = MultiAgentWebSocketManager(
            connection_id="local-test-conn",
            review_id=789,
            is_local=True
        )
        
        assert manager.connection_id == "local-test-conn"
        assert manager.review_id == 789
        assert manager.is_local is True
        assert manager.connection_id_gone is False


class TestMultiAgentWebSocketManagerExecuteAgentTask:
    """Test cases for MultiAgentWebSocketManager.execute_agent_task method."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_success(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
        sample_ide_review_response: Dict[str, Any],
    ) -> None:
        """Test successful agent task execution."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.IdeReviewManager') as mock_ide_manager:
            mock_ide_manager.review_diff = AsyncMock(return_value=sample_ide_review_response)
            
            result = await sample_multi_agent_manager.execute_agent_task(sample_agent_request_query)
            
            assert isinstance(result, WebSocketMessage)
            assert result.type == "REVIEW_COMPLETE"
            assert result.agent_id == sample_agent_request_query.agent_id
            mock_ide_manager.review_diff.assert_called_once_with(sample_agent_request_query)

    @pytest.mark.asyncio
    async def test_execute_agent_task_exception(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
    ) -> None:
        """Test agent task execution with exception."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.IdeReviewManager') as mock_ide_manager:
            mock_ide_manager.review_diff = AsyncMock(side_effect=Exception("Test error"))
            
            result = await sample_multi_agent_manager.execute_agent_task(sample_agent_request_query)
            
            assert isinstance(result, WebSocketMessage)
            assert result.type == "AGENT_FAIL"
            assert result.agent_id == sample_agent_request_query.agent_id
            assert "Test error" in result.data["message"]


class TestMultiAgentWebSocketManagerDetermineEventType:
    """Test cases for MultiAgentWebSocketManager.determine_event_type method."""

    def test_determine_event_type_error_status(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with ERROR status."""
        formatted_result = {"status": "ERROR"}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "AGENT_ERROR"

    def test_determine_event_type_tool_use_request(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with TOOL_USE_REQUEST type."""
        formatted_result = {"type": "TOOL_USE_REQUEST"}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "TOOL_USE_REQUEST"

    def test_determine_event_type_review_complete(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with REVIEW_COMPLETE type."""
        formatted_result = {"type": "REVIEW_COMPLETE"}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "AGENT_COMPLETE"

    def test_determine_event_type_review_error(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with REVIEW_ERROR type."""
        formatted_result = {"type": "REVIEW_ERROR"}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "AGENT_ERROR"

    def test_determine_event_type_unknown_type(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with unknown type."""
        formatted_result = {"type": "UNKNOWN_TYPE"}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "AGENT_COMPLETE"

    def test_determine_event_type_no_type(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
    ) -> None:
        """Test determine_event_type with no type field."""
        formatted_result = {}
        
        result = sample_multi_agent_manager.determine_event_type(formatted_result)
        
        assert result == "AGENT_COMPLETE"


class TestMultiAgentWebSocketManagerProcessRequest:
    """Test cases for MultiAgentWebSocketManager.process_request method."""

    @pytest.mark.asyncio
    async def test_process_request_single_agent(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_single: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_request with single agent."""
        with patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                sample_agent_request_list_single, 
                sample_local_stream_buffer
            )
            
            mock_execute.assert_called_once_with(
                sample_agent_request_list_single[0], 
                sample_local_stream_buffer
            )

    @pytest.mark.asyncio
    async def test_process_request_multiple_agents(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_multiple: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_request with multiple agents."""
        with patch.object(sample_multi_agent_manager, 'process_multiple_agents_with_cache_pattern') as mock_process:
            mock_process.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                sample_agent_request_list_multiple, 
                sample_local_stream_buffer
            )
            
            mock_process.assert_called_once_with(
                sample_agent_request_list_multiple, 
                sample_local_stream_buffer
            )

    @pytest.mark.asyncio
    async def test_process_request_exception_handling(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_single: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_request exception handling."""
        with patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_execute.side_effect = Exception("Test error")
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                sample_agent_request_list_single, 
                sample_local_stream_buffer
            )
            
            mock_push.assert_called()
            call_args = mock_push.call_args[0]
            assert call_args[0].type == "AGENT_FAIL"
            assert "Agent processing error" in call_args[0].data["message"]

    @pytest.mark.asyncio
    async def test_process_request_aws_client_cleanup(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_single: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_request AWS client cleanup."""
        mock_aws_client = AsyncMock()
        sample_multi_agent_manager.aws_client = mock_aws_client
        
        with patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                sample_agent_request_list_single, 
                sample_local_stream_buffer
            )
            
            mock_aws_client.close.assert_called_once()


class TestMultiAgentWebSocketManagerProcessMultipleAgentsWithCachePattern:
    """Test cases for MultiAgentWebSocketManager.process_multiple_agents_with_cache_pattern method."""

    @pytest.mark.asyncio
    async def test_process_multiple_agents_with_cache_establishing_and_utilizing(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_mixed_agent_requests: List[AgentRequestItem],
        sample_user_agent_dtos_mixed: List[MagicMock],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_multiple_agents_with_cache_pattern with both types of agents."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_repo.db_get = AsyncMock(return_value=sample_user_agent_dtos_mixed)
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_mixed_agent_requests, 
                sample_local_stream_buffer
            )
            
            # Should execute all agents
            assert mock_execute.call_count == len(sample_mixed_agent_requests)

    @pytest.mark.asyncio
    async def test_process_multiple_agents_no_valid_user_agents(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_multiple: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_multiple_agents_with_cache_pattern with no valid user agents."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_repo.db_get = AsyncMock(return_value=[])
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_agent_request_list_multiple, 
                sample_local_stream_buffer
            )
            
            # Should not execute any agents
            mock_execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_process_multiple_agents_exception_handling(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_multiple: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_multiple_agents_with_cache_pattern exception handling."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_repo.db_get = AsyncMock(side_effect=Exception("Database error"))
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_agent_request_list_multiple, 
                sample_local_stream_buffer
            )
            
            mock_push.assert_called()
            call_args = mock_push.call_args[0]
            assert call_args[0].type == "AGENT_FAIL"
            assert "Multi-agent processing error" in call_args[0].data["message"]

    @pytest.mark.asyncio
    async def test_process_multiple_agents_only_cache_establishing(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_cache_establishing_agents: List[AgentRequestItem],
        sample_user_agent_dtos_cache_establishing: List[MagicMock],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_multiple_agents_with_cache_pattern with only cache establishing agents."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_repo.db_get = AsyncMock(return_value=sample_user_agent_dtos_cache_establishing)
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_cache_establishing_agents, 
                sample_local_stream_buffer
            )
            
            assert mock_execute.call_count == len(sample_cache_establishing_agents)

    @pytest.mark.asyncio
    async def test_process_multiple_agents_only_cache_utilizing(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_cache_utilizing_agents: List[AgentRequestItem],
        sample_user_agent_dtos_cache_utilizing: List[MagicMock],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_multiple_agents_with_cache_pattern with only cache utilizing agents."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_repo.db_get = AsyncMock(return_value=sample_user_agent_dtos_cache_utilizing)
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_cache_utilizing_agents, 
                sample_local_stream_buffer
            )
            
            assert mock_execute.call_count == len(sample_cache_utilizing_agents)


class TestMultiAgentWebSocketManagerExecuteAndStreamAgent:
    """Test cases for MultiAgentWebSocketManager.execute_and_stream_agent method."""

    @pytest.mark.asyncio
    async def test_execute_and_stream_agent_query_request(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
        sample_websocket_message_success: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test execute_and_stream_agent with query request."""
        with patch.object(sample_multi_agent_manager, 'execute_agent_task') as mock_execute, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_execute.return_value = sample_websocket_message_success
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.execute_and_stream_agent(
                sample_agent_request_query, 
                sample_local_stream_buffer
            )
            
            # Should send AGENT_START message and the result
            assert mock_push.call_count == 2
            first_call = mock_push.call_args_list[0][0][0]
            assert first_call.type == "AGENT_START"
            assert first_call.agent_id == sample_agent_request_query.agent_id

    @pytest.mark.asyncio
    async def test_execute_and_stream_agent_tool_use_response_request(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_tool_use_response: AgentRequestItem,
        sample_websocket_message_success: WebSocketMessage,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test execute_and_stream_agent with tool use response request."""
        with patch.object(sample_multi_agent_manager, 'execute_agent_task') as mock_execute, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_execute.return_value = sample_websocket_message_success
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.execute_and_stream_agent(
                sample_agent_request_tool_use_response, 
                sample_local_stream_buffer
            )
            
            # Should only send the result (no AGENT_START for tool use response)
            assert mock_push.call_count == 1

    @pytest.mark.asyncio
    async def test_execute_and_stream_agent_exception_handling(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test execute_and_stream_agent exception handling."""
        with patch.object(sample_multi_agent_manager, 'execute_agent_task') as mock_execute, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_execute.side_effect = Exception("Test execution error")
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.execute_and_stream_agent(
                sample_agent_request_query, 
                sample_local_stream_buffer
            )
            
            # Should send AGENT_START and AGENT_FAIL messages
            assert mock_push.call_count == 2
            fail_call = mock_push.call_args_list[1][0][0]
            assert fail_call.type == "AGENT_FAIL"
            assert fail_call.agent_id == sample_agent_request_query.agent_id
            assert "Test execution error" in fail_call.data["message"]


class TestMultiAgentWebSocketManagerEdgeCases:
    """Test cases for MultiAgentWebSocketManager edge cases."""

    @pytest.mark.asyncio
    async def test_execute_agent_task_with_different_result_types(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
    ) -> None:
        """Test execute_agent_task with different result types."""
        test_cases = [
            {"type": "TOOL_USE_REQUEST", "expected_type": "TOOL_USE_REQUEST"},
            {"type": "REVIEW_COMPLETE", "expected_type": "REVIEW_COMPLETE"},
            {"type": "REVIEW_ERROR", "expected_type": "REVIEW_ERROR"},
            {"status": "ERROR", "expected_type": "AGENT_FAIL"},
        ]
        
        for case in test_cases:
            with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.IdeReviewManager') as mock_ide_manager:
                mock_ide_manager.review_diff = AsyncMock(return_value=case)
                
                result = await sample_multi_agent_manager.execute_agent_task(sample_agent_request_query)
                
                assert isinstance(result, WebSocketMessage)
                assert result.type == case["expected_type"]

    @pytest.mark.asyncio
    async def test_process_request_with_empty_agent_list(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test process_request with empty agent list."""
        empty_agent_list: List[AgentRequestItem] = []
        
        with patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            mock_execute.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                empty_agent_list, 
                sample_local_stream_buffer
            )
            
            # Should not call execute_and_stream_agent for empty list
            mock_execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_concurrent_agent_execution(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_list_multiple: List[AgentRequestItem],
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test concurrent execution of multiple agents."""
        execution_order = []
        
        async def mock_execute_and_stream_agent(agent_request: AgentRequestItem, buffer: Dict[str, List[str]]) -> None:
            execution_order.append(agent_request.agent_id)
            await asyncio.sleep(0.01)  # Simulate async work
        
        with patch.object(sample_multi_agent_manager, 'execute_and_stream_agent', side_effect=mock_execute_and_stream_agent), \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo:
            
            # Mock user agents with non-cache establishing types
            mock_user_agents = [
                MagicMock(id=req.agent_id, agent_name="CODE_COMMUNICATION") 
                for req in sample_agent_request_list_multiple
            ]
            mock_repo.db_get = AsyncMock(return_value=mock_user_agents)
            
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                sample_agent_request_list_multiple, 
                sample_local_stream_buffer
            )
            
            # All agents should have been executed
            assert len(execution_order) == len(sample_agent_request_list_multiple)


class TestMultiAgentWebSocketManagerIntegration:
    """Integration test cases for MultiAgentWebSocketManager."""

    @pytest.mark.asyncio
    async def test_end_to_end_single_agent_flow(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_agent_request_query: AgentRequestItem,
        sample_local_stream_buffer: Dict[str, List[str]],
        sample_ide_review_response: Dict[str, Any],
    ) -> None:
        """Test end-to-end flow for single agent."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.IdeReviewManager') as mock_ide_manager, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            mock_ide_manager.review_diff = AsyncMock(return_value=sample_ide_review_response)
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                [sample_agent_request_query], 
                sample_local_stream_buffer
            )
            
            # Should send AGENT_START and final result
            assert mock_push.call_count == 2

    @pytest.mark.asyncio
    async def test_end_to_end_multi_agent_flow(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_mixed_agent_requests: List[AgentRequestItem],
        sample_user_agent_dtos_mixed: List[MagicMock],
        sample_local_stream_buffer: Dict[str, List[str]],
        sample_ide_review_response: Dict[str, Any],
    ) -> None:
        """Test end-to-end flow for multiple agents."""
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.IdeReviewManager') as mock_ide_manager, \
             patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'push_to_connection_stream') as mock_push:
            
            mock_ide_manager.review_diff = AsyncMock(return_value=sample_ide_review_response)
            mock_repo.db_get = AsyncMock(return_value=sample_user_agent_dtos_mixed)
            mock_push.return_value = AsyncMock()
            
            await sample_multi_agent_manager.process_request(
                sample_mixed_agent_requests, 
                sample_local_stream_buffer
            )
            
            # Should send messages for all agents
            assert mock_push.call_count >= len(sample_mixed_agent_requests)


class TestMultiAgentWebSocketManagerPerformance:
    """Performance test cases for MultiAgentWebSocketManager."""

    @pytest.mark.asyncio
    async def test_large_number_of_agents(
        self,
        sample_multi_agent_manager: MultiAgentWebSocketManager,
        sample_local_stream_buffer: Dict[str, List[str]],
    ) -> None:
        """Test handling large number of agents."""
        # Create a large number of agent requests
        large_agent_list = [
            AgentRequestItem(
                agent_id=i,
                review_id=456,
                type=RequestType.QUERY,
                payload={"content": f"Test content {i}"}
            )
            for i in range(50)
        ]
        
        # Mock user agents for all requests
        mock_user_agents = [
            MagicMock(id=i, agent_name="CODE_COMMUNICATION") 
            for i in range(50)
        ]
        
        with patch('app.main.blueprints.deputy_dev.services.code_review.ide_review.multi_agent_review_manager.UserAgentRepository') as mock_repo, \
             patch.object(sample_multi_agent_manager, 'execute_and_stream_agent') as mock_execute:
            
            mock_repo.db_get = AsyncMock(return_value=mock_user_agents)
            mock_execute.return_value = AsyncMock()
            
            start_time = asyncio.get_event_loop().time()
            await sample_multi_agent_manager.process_multiple_agents_with_cache_pattern(
                large_agent_list, 
                sample_local_stream_buffer
            )
            end_time = asyncio.get_event_loop().time()
            
            # Should complete within reasonable time (adjust as needed)
            execution_time = end_time - start_time
            assert execution_time < 5.0  # 5 seconds threshold
            assert mock_execute.call_count == 50