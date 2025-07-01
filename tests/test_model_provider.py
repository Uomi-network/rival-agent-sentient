"""
Tests for the ModelProvider class
"""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from rival_agent.providers.model_provider import ModelProvider, BlockchainEvent


class TestModelProvider:
    """Test suite for ModelProvider class"""

    @pytest.fixture
    def mock_web3(self):
        """Mock Web3 instance"""
        with patch('rival_agent.providers.model_provider.Web3') as mock_w3:
            mock_instance = MagicMock()
            mock_instance.is_connected.return_value = True
            mock_instance.eth.chain_id = 1
            mock_w3.return_value = mock_instance
            yield mock_instance

    @pytest.fixture  
    def mock_account(self):
        """Mock Account for transaction signing"""
        with patch('rival_agent.providers.model_provider.Account') as mock_acc:
            mock_account_instance = MagicMock()
            mock_account_instance.address = "0x1234567890123456789012345678901234567890"
            mock_acc.from_key.return_value = mock_account_instance
            yield mock_account_instance

    def test_init_with_private_key(self, mock_web3, mock_account):
        """Test initialization with private key"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key="0x1234",
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        assert provider.rpc_url == "https://test-rpc.com"
        assert provider.private_key == "0x1234"
        assert provider.nft_id == 3
        assert provider.account is not None

    def test_init_without_private_key(self, mock_web3):
        """Test initialization without private key (mock mode)"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        assert provider.private_key is None
        assert provider.account is None
        assert provider.wallet_address == "0x0000000000000000000000000000000000000000"

    @pytest.mark.asyncio
    async def test_query_mock_mode(self, mock_web3):
        """Test query method in mock mode"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        response = await provider.query("test query")
        assert "test query" in response
        assert isinstance(response, str)

    @pytest.mark.asyncio
    async def test_query_stream_mock_mode(self, mock_web3):
        """Test query_stream method in mock mode"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        chunks = []
        async for chunk in provider.query_stream("test query"):
            chunks.append(chunk)
        
        response = "".join(chunks)
        assert "test query" in response

    def test_get_connection_status(self, mock_web3):
        """Test get_connection_status method"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        status = provider.get_connection_status()
        
        assert status['rpc_url'] == "https://test-rpc.com"
        assert status['nft_id'] == 3
        assert 'connected' in status
        assert 'chain_id' in status

    def test_get_pending_requests(self, mock_web3):
        """Test get_pending_requests method"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        pending = provider.get_pending_requests()
        assert isinstance(pending, dict)

    @pytest.mark.asyncio
    async def test_cancel_request(self, mock_web3):
        """Test cancel_request method"""
        provider = ModelProvider(
            rpc_url="https://test-rpc.com",
            private_key=None,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=3
        )
        
        # Add a mock request
        provider.pending_requests["0x123"] = {"status": "pending"}
        
        # Cancel the request
        result = await provider.cancel_request("0x123")
        assert result is True
        assert "0x123" not in provider.pending_requests

        # Try to cancel non-existent request
        result = await provider.cancel_request("0x456")
        assert result is False

    def test_blockchain_event_dataclass(self):
        """Test BlockchainEvent dataclass"""
        event = BlockchainEvent(
            event_type="RequestSent",
            request_id=12345,
            data={"test": "data"}
        )
        
        assert event.event_type == "RequestSent"
        assert event.request_id == 12345
        assert event.data == {"test": "data"}


if __name__ == "__main__":
    pytest.main([__file__])
