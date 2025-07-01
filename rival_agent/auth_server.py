import asyncio
import os
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sentient_agent_framework.implementation.default_hook import DefaultHook
from sentient_agent_framework.implementation.default_response_handler import DefaultResponseHandler
from sentient_agent_framework.implementation.default_session import DefaultSession
from sentient_agent_framework.interface.agent import AbstractAgent
from sentient_agent_framework.interface.events import DoneEvent
from sentient_agent_framework.interface.identity import Identity
from sentient_agent_framework.interface.request import Request
from typing import Optional


class AuthenticatedServer:
    """
    FastAPI server with simple API key authentication that streams agent output 
    to the client via Server-Sent Events.
    """

    def __init__(
            self,
            agent: AbstractAgent,
            api_key: Optional[str] = None
        ):
        self._agent = agent
        
        # Use provided API key or get from environment
        self._api_key = api_key or os.getenv("RIVAL_API_KEY")
        if not self._api_key:
            # Generate a simple default key if none provided
            self._api_key = "rival_agent_default_key_change_me"
            print(f"WARNING: Using default API key. Set RIVAL_API_KEY environment variable.")
        
        print(f"Server will require API key: {self._api_key}")

        # Create FastAPI app
        self._app = FastAPI(title="Rival Agent API", version="1.0.0")
        
        # Security scheme
        self._security = HTTPBearer()
        
        # Setup routes
        self._setup_routes()

    def _verify_api_key(self, credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer())):
        """Verify the provided API key."""
        if credentials.credentials != self._api_key:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

    def _setup_routes(self):
        """Setup API routes."""
        
        @self._app.get("/")
        async def root():
            return {"message": "Rival Agent API", "status": "running"}
        
        @self._app.get("/health")
        async def health():
            return {"status": "healthy"}
        
        @self._app.post("/assist")
        async def assist_endpoint(
            request: Request,
            api_key: str = Depends(self._verify_api_key)
        ):
            """Endpoint that streams agent output to client as SSE events."""
            return StreamingResponse(
                self.__stream_agent_output(request), 
                media_type="text/event-stream"
            )

    def run(
            self, 
            host: str = "0.0.0.0",
            port: int = 8000
        ):
        """Start the FastAPI server"""
        print(f"Starting authenticated server on {host}:{port}")
        print(f"Use this API key in Authorization header: Bearer {self._api_key}")
        
        uvicorn.run(
            self._app,
            host=host, 
            port=port
        )

    async def __stream_agent_output(self, request):
        """Yield agent output as SSE events."""

        # Get session from request
        session = DefaultSession(request.session)

        # Get identity using processor id from session
        identity = Identity(id=session.processor_id, name=self._agent.name)

        # Create response queue
        response_queue = asyncio.Queue()

        # Create hook
        hook = DefaultHook(response_queue)

        # Create response handler
        response_handler = DefaultResponseHandler(identity, hook)

        # Run the agent's assist function
        asyncio.create_task(self._agent.assist(session, request.query, response_handler))
        
        # Stream the response handler events
        while True:
            event = await response_queue.get()
            yield f"event: {event.event_name}\n"
            yield f"data: {event.model_dump_json()}\n\n"
            response_queue.task_done()
            if type(event) == DoneEvent:
                break
