import os
from fastapi import Request as FastAPIRequest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from sentient_agent_framework import DefaultServer
from sentient_agent_framework.interface.agent import AbstractAgent
from typing import Optional


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle API key authentication for all requests except health endpoints.
    """
    
    def __init__(self, app, api_key: str):
        super().__init__(app)
        self.api_key = api_key
    
    async def dispatch(self, request: FastAPIRequest, call_next):
        # Skip authentication for health and root endpoints
        if request.url.path in ["/", "/health"]:
            return await call_next(request)
        
        # Check for Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return Response(
                content='{"detail": "Authorization header missing"}',
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Verify Bearer token format
        if not authorization.startswith("Bearer "):
            return Response(
                content='{"detail": "Invalid authorization format"}',
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Extract and verify API key
        token = authorization.split(" ", 1)[1]
        if token != self.api_key:
            return Response(
                content='{"detail": "Invalid API key"}',
                status_code=401,
                headers={"WWW-Authenticate": "Bearer"},
                media_type="application/json"
            )
        
        # Continue with the request
        return await call_next(request)


class AuthenticatedServer(DefaultServer):
    """
    Extended DefaultServer that adds API key authentication middleware.
    
    This server extends the base DefaultServer from the Sentient Agent Framework
    and adds authentication via middleware instead of manual verification.
    """

    def __init__(
            self,
            agent: AbstractAgent,
            api_key: Optional[str] = None
    ):
        """Initialize the authenticated server with an agent and API key."""
        # Initialize the parent DefaultServer
        super().__init__(agent)
        
        # Store authentication settings
        self._api_key = api_key or os.getenv("RIVAL_API_KEY")
        if not self._api_key:
            # Generate a simple default key if none provided
            self._api_key = "rival_agent_default_key_change_me"
            print(f"WARNING: Using default API key. Set RIVAL_API_KEY environment variable.")
        
        # Add authentication middleware to the existing app
        self._app.add_middleware(
            AuthenticationMiddleware,
            api_key=self._api_key
        )
        
        # Add a health endpoint that doesn't require authentication
        @self._app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        print(f"Server will require API key: {self._api_key}")

    def run(
            self, 
            host: str = "0.0.0.0",
            port: int = 8000
        ):
        """Start the authenticated server."""
        print(f"Starting authenticated server on {host}:{port}")
        print(f"Use this API key in Authorization header: Bearer {self._api_key}")
        
        # Use the parent's run method which already handles the FastAPI app
        super().run(host, port)
