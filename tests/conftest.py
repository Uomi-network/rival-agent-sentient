"""
Test configuration and fixtures
"""

import pytest
import asyncio
import os
from unittest.mock import patch


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_env_clean():
    """Clean environment for testing"""
    with patch.dict(os.environ, {}, clear=True):
        yield


@pytest.fixture
def mock_env_minimal():
    """Minimal environment variables for testing"""
    with patch.dict(os.environ, {
        'BLOCKCHAIN_RPC_URL': 'https://test-rpc.com',
        'TAVILY_API_KEY': 'test-tavily-key',
        'CONTRACT_ADDRESS': '0x609a8aeeef8b89be02c5b59a936a520547252824',
        'NFT_ID': '3'
    }):
        yield


@pytest.fixture
def mock_env_full():
    """Full environment variables for testing"""
    with patch.dict(os.environ, {
        'BLOCKCHAIN_RPC_URL': 'https://test-rpc.com',
        'BLOCKCHAIN_PRIVATE_KEY': '0x1234567890abcdef',
        'TAVILY_API_KEY': 'test-tavily-key',
        'CONTRACT_ADDRESS': '0x609a8aeeef8b89be02c5b59a936a520547252824',
        'NFT_ID': '3',
        'HOST': '127.0.0.1',
        'PORT': '8000',
        'LOG_LEVEL': 'DEBUG',
        'DEBUG': 'true',
        'ENVIRONMENT': 'test'
    }):
        yield
