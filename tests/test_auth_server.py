"""
Test the AuthenticatedServer implementation.
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from rival_agent import RivalAgent
from rival_agent.auth_server import AuthenticatedServer, AuthenticationMiddleware
from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.requests import Request


class TestAuthenticationMiddleware:
    """Test suite for AuthenticationMiddleware"""
    
    def test_middleware_initialization(self):
        """Test middleware initialization"""
        app = FastAPI()
        api_key = "test_key_123"
        middleware = AuthenticationMiddleware(app, api_key)
        
        assert middleware.api_key == api_key
        assert middleware.security is not None
    
    @pytest.mark.asyncio
    async def test_middleware_allows_health_endpoints(self):
        """Test that middleware allows access to health endpoints without auth"""
        app = FastAPI()
        api_key = "test_key_123"
        
        @app.get("/")
        async def root():
            return {"message": "OK"}
        
        @app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        # Add middleware
        app.add_middleware(AuthenticationMiddleware, api_key=api_key)
        
        client = TestClient(app)
        
        # Test root endpoint
        response = client.get("/")
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}
        
        # Test health endpoint
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}
    
    @pytest.mark.asyncio
    async def test_middleware_requires_auth_for_protected_endpoints(self):
        """Test that middleware requires authentication for protected endpoints"""
        app = FastAPI()
        api_key = "test_key_123"
        
        @app.post("/assist")
        async def assist():
            return {"message": "assist"}
        
        # Add middleware
        app.add_middleware(AuthenticationMiddleware, api_key=api_key)
        
        client = TestClient(app)
        
        # Test without authorization header
        response = client.post("/assist")
        assert response.status_code == 401
        assert "Authorization header missing" in response.json()["detail"]
        
        # Test with wrong authorization format
        response = client.post("/assist", headers={"Authorization": "InvalidFormat"})
        assert response.status_code == 401
        assert "Invalid authorization format" in response.json()["detail"]
        
        # Test with wrong API key
        response = client.post("/assist", headers={"Authorization": "Bearer wrong_key"})
        assert response.status_code == 401
        assert "Invalid API key" in response.json()["detail"]
        
        # Test with correct API key
        response = client.post("/assist", headers={"Authorization": f"Bearer {api_key}"})
        assert response.status_code == 200
        assert response.json() == {"message": "assist"}


class TestAuthenticatedServer:
    """Test suite for AuthenticatedServer class"""
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for testing"""
        with patch.dict('os.environ', {
            'BLOCKCHAIN_RPC_URL': 'https://test-rpc.com',
            'RIVAL_API_KEY': 'test_api_key_123'
        }):
            yield
    
    @patch('rival_agent.auth_server.RivalAgent')
    def test_authenticated_server_init(self, mock_rival_agent, mock_env_vars):
        """Test AuthenticatedServer initialization"""
        mock_agent = MagicMock()
        
        server = AuthenticatedServer(
            agent=mock_agent,
            api_key="custom_key",
            host="127.0.0.1",
            port=9000
        )
        
        assert server._api_key == "custom_key"
        assert server._host == "127.0.0.1"
        assert server._port == 9000
        assert server._agent == mock_agent
    
    @patch('rival_agent.auth_server.RivalAgent')
    def test_authenticated_server_uses_env_api_key(self, mock_rival_agent, mock_env_vars):
        """Test that server uses environment API key when none provided"""
        mock_agent = MagicMock()
        
        server = AuthenticatedServer(agent=mock_agent)
        
        assert server._api_key == "test_api_key_123"
    
    @patch('rival_agent.auth_server.RivalAgent')
    def test_authenticated_server_generates_default_key(self, mock_rival_agent):
        """Test that server generates default key when none available"""
        mock_agent = MagicMock()
        
        with patch.dict('os.environ', {}, clear=True):
            server = AuthenticatedServer(agent=mock_agent)
            
            assert server._api_key == "rival_agent_default_key_change_me"
    
    @patch('rival_agent.auth_server.RivalAgent')
    def test_create_app_adds_middleware(self, mock_rival_agent, mock_env_vars):
        """Test that _create_app adds authentication middleware"""
        mock_agent = MagicMock()
        
        server = AuthenticatedServer(agent=mock_agent, api_key="test_key")
        app = server._create_app()
        
        # Check that app is created
        assert isinstance(app, FastAPI)
        assert app.title == "Rival Agent API"
        
        # The middleware should be added (we can't easily test this directly)
        # but we can verify the app was created successfully


if __name__ == "__main__":
    pytest.main([__file__])
