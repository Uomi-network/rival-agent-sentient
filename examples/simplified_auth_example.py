#!/usr/bin/env python3

"""
Example of using the simplified AuthenticatedServer.

This demonstrates how the AuthenticatedServer extends the DefaultServer
and simply adds authentication middleware without duplicating code.
"""

import os
from rival_agent.auth_server import AuthenticatedServer
from rival_agent.rival_agent import RivalAgent


def main():
    """Run the authenticated server example."""
    
    # Create an agent (you would normally configure this properly)
    agent = RivalAgent(
        model_provider=None,  # Configure with your provider
        search_provider=None   # Configure with your provider
    )
    
    # Create authenticated server with custom API key
    server = AuthenticatedServer(
        agent=agent,
        api_key="my_secure_api_key_123"
    )
    
    # Start the server (this will block)
    print("Starting server...")
    print("Endpoints:")
    print("  GET  /health (no auth required)")
    print("  POST /assist (requires Bearer token)")
    print()
    print("Example curl command:")
    print("curl -X POST http://localhost:8000/assist \\")
    print("     -H 'Authorization: Bearer my_secure_api_key_123' \\")
    print("     -H 'Content-Type: application/json' \\")
    print("     -d '{\"query\": \"Hello, how can you help me?\", \"session\": \"test\"}'")
    
    server.run(host="localhost", port=8000)


if __name__ == "__main__":
    main()
