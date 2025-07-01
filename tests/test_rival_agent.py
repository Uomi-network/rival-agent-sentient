"""
Tests for the RivalAgent class
"""

import pytest
import os
from unittest.mock import AsyncMock, MagicMock, patch
from rival_agent import RivalAgent, create_agent


class TestRivalAgent:
    """Test suite for RivalAgent class"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing"""
        with patch.dict(os.environ, {
            'BLOCKCHAIN_RPC_URL': 'https://test-rpc.com',
            'TAVILY_API_KEY': 'test-tavily-key',
            'CONTRACT_ADDRESS': '0x609a8aeeef8b89be02c5b59a936a520547252824',
            'NFT_ID': '3'
        }):
            yield

    @patch('rival_agent.rival_agent.ModelProvider')
    @patch('rival_agent.rival_agent.SearchProvider')
    def test_init_success(self, mock_search_provider, mock_model_provider, mock_env_vars):
        """Test successful initialization of RivalAgent"""
        agent = RivalAgent(name="TestRival")
        
        assert agent.name == "TestRival"
        mock_model_provider.assert_called_once()
        mock_search_provider.assert_called_once()

    def test_init_missing_rpc_url(self):
        """Test initialization fails when BLOCKCHAIN_RPC_URL is missing"""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="BLOCKCHAIN_RPC_URL is not set"):
                RivalAgent()

    def test_init_missing_tavily_key(self):
        """Test initialization fails when TAVILY_API_KEY is missing"""
        with patch.dict(os.environ, {
            'BLOCKCHAIN_RPC_URL': 'https://test-rpc.com'
        }, clear=True):
            with pytest.raises(ValueError, match="TAVILY_API_KEY is not set"):
                RivalAgent()

    @patch('rival_agent.rival_agent.ModelProvider')
    @patch('rival_agent.rival_agent.SearchProvider')
    def test_get_status(self, mock_search_provider, mock_model_provider, mock_env_vars):
        """Test get_status method"""
        # Mock the model provider's get_connection_status method
        mock_model_provider.return_value.get_connection_status.return_value = {
            'connected': True,
            'contract_address': '0x609a8aeeef8b89be02c5b59a936a520547252824',
            'nft_id': 3
        }
        mock_model_provider.return_value.get_pending_requests.return_value = {}
        
        agent = RivalAgent(name="TestRival")
        status = agent.get_status()
        
        assert status['name'] == "TestRival"
        assert 'blockchain_status' in status
        assert 'pending_requests' in status
        assert status['pending_requests'] == 0

    def test_create_agent_factory(self):
        """Test the create_agent factory function"""
        with patch('rival_agent.rival_agent.RivalAgent') as mock_rival_agent:
            create_agent(name="FactoryTest")
            mock_rival_agent.assert_called_once_with(name="FactoryTest")

    @pytest.mark.asyncio
    @patch('rival_agent.rival_agent.ModelProvider')
    @patch('rival_agent.rival_agent.SearchProvider')
    async def test_assist_success(self, mock_search_provider, mock_model_provider, mock_env_vars):
        """Test successful assist method execution"""
        # Setup mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.prompt = "test query"
        mock_response_handler = AsyncMock()
        mock_text_stream = AsyncMock()
        mock_response_handler.create_text_stream.return_value = mock_text_stream
        
        # Mock search results
        mock_search_results = {
            "results": [{"title": "Test", "content": "Test content"}],
            "images": []
        }
        mock_search_provider.return_value.search.return_value = mock_search_results
        
        # Mock model provider streaming
        async def mock_query_stream(query):
            yield "Test "
            yield "response"
        
        mock_model_provider.return_value.query_stream = mock_query_stream
        
        # Create agent and run assist
        agent = RivalAgent(name="TestRival")
        await agent.assist(mock_session, mock_query, mock_response_handler)
        
        # Verify calls
        mock_response_handler.emit_text_block.assert_called()
        mock_response_handler.emit_json.assert_called()
        mock_text_stream.emit_chunk.assert_called()
        mock_text_stream.complete.assert_called_once()
        mock_response_handler.complete.assert_called_once()

    @pytest.mark.asyncio
    @patch('rival_agent.rival_agent.ModelProvider')
    @patch('rival_agent.rival_agent.SearchProvider')
    async def test_assist_error_handling(self, mock_search_provider, mock_model_provider, mock_env_vars):
        """Test error handling in assist method"""
        # Setup mocks
        mock_session = MagicMock()
        mock_query = MagicMock()
        mock_query.prompt = "test query"
        mock_response_handler = AsyncMock()
        
        # Make search provider raise an exception
        mock_search_provider.return_value.search.side_effect = Exception("Search failed")
        
        # Create agent and run assist
        agent = RivalAgent(name="TestRival")
        await agent.assist(mock_session, mock_query, mock_response_handler)
        
        # Verify error handling
        mock_response_handler.emit_text_block.assert_called_with("ERROR", "❌ Error: Search failed")
        mock_response_handler.complete.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__])
