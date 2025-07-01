#!/usr/bin/env python3
"""
Example of how to use the Rival Agent with authentication.

This example shows:
1. How to start the server with authentication enabled
2. How to make requests with the API key
"""

import os
import asyncio
import aiohttp
import json
from dotenv import load_dotenv

load_dotenv()

async def test_authenticated_request():
    """Test making a request to the authenticated server."""
    
    # The API key - get from environment or use the default
    api_key = os.getenv("RIVAL_API_KEY", "rival_agent_default_key_change_me")
    
    # Server URL
    base_url = "http://localhost:8000"
    
    # Headers with authentication
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Test data
    request_data = {
        "session": {"processor_id": "test_user_123"},
        "query": "What can you tell me about blockchain technology?"
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test health endpoint (no auth required)
            async with session.get(f"{base_url}/health") as response:
                print(f"Health check: {response.status}")
                health_data = await response.json()
                print(f"Health response: {health_data}")
            
            # Test authenticated endpoint
            async with session.post(
                f"{base_url}/assist",
                headers=headers,
                json=request_data
            ) as response:
                print(f"Assist request status: {response.status}")
                
                if response.status == 200:
                    print("Streaming response:")
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if line_str.startswith('data: '):
                            data = line_str[6:]  # Remove 'data: ' prefix
                            try:
                                event_data = json.loads(data)
                                print(f"Event: {event_data}")
                            except json.JSONDecodeError:
                                print(f"Raw data: {data}")
                else:
                    error_text = await response.text()
                    print(f"Error: {error_text}")
                    
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    print("Testing authenticated Rival Agent server...")
    print("Make sure the server is running with RIVAL_USE_AUTH=true")
    print()
    
    asyncio.run(test_authenticated_request())
