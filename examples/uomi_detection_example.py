#!/usr/bin/env python3
"""
Example usage of the ModelProvider with uomi detection feature.

This script demonstrates how to use the enhanced ModelProvider that 
automatically detects "uomi" in responses and handles prize distribution.
"""

import asyncio
import os
from rival_agent.providers.model_provider import ModelProvider

async def game_session_example():
    """Example of a complete game session with uomi detection"""
    
    # Initialize the provider
    provider = ModelProvider(
        rpc_url=os.getenv("RPC_URL", "http://localhost:8545"),
        private_key=os.getenv("PRIVATE_KEY"),  # Use environment variable
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=3
    )
    
    print("🎮 Starting game session...")
    print("=" * 50)
    
    # Simulate a game session
    game_queries = [
        "What is the meaning of life?",
        "How do I win this game?",
        "Tell me about cryptocurrency",
        "Is the answer uomi?",  # This will trigger the game block
        "What happens now?"     # This will show the blocked message
    ]
    
    for i, query in enumerate(game_queries, 1):
        print(f"\n📝 Query {i}: {query}")
        
        # Check if game is blocked before making query
        if provider.is_game_blocked():
            print("⚠️  Game is blocked - showing blocked message")
        
        # Make the query
        response = await provider.query(query)
        print(f"🤖 Response: {response}")
        
        # Check if game was blocked by this query
        if provider.is_game_blocked():
            print("🚫 Game has been blocked!")
            break
    
    # Handle wallet address collection
    print("\n" + "=" * 50)
    print("💰 Prize Distribution Phase")
    print("=" * 50)
    
    # Simulate user providing wallet address
    wallet_inputs = [
        "My wallet is 0x742d35Cc6634C0532925a3b8D4031c4A8dF1c3f1",
        "Please send the prize to: 0x1234567890123456789012345678901234567890"
    ]
    
    for wallet_input in wallet_inputs:
        print(f"\n💬 User input: {wallet_input}")
        
        # Process wallet and send prize
        result = await provider.process_and_send_prize(wallet_input)
        
        if result["success"]:
            print(f"✅ {result['message']}")
            break
        else:
            print(f"❌ {result['message']}")
    
    # Show final game status
    print("\n" + "=" * 50)
    print("📊 Final Game Status")
    print("=" * 50)
    
    status = provider.get_game_status()
    print(f"Game blocked: {status['game_blocked']}")
    if status['winner']:
        print(f"Winner wallet: {status['winner']['wallet_address']}")
        print(f"Prize sent: {status['winner']['prize_sent']}")
    
    # Show log file if it exists
    if os.path.exists(status['log_file']):
        print(f"\n📋 Log file: {status['log_file']}")
        with open(status['log_file'], 'r') as f:
            print("Recent events:")
            lines = f.readlines()
            for line in lines[-3:]:  # Show last 3 events
                print(f"  {line.strip()}")

async def streaming_example():
    """Example of streaming with uomi detection"""
    
    print("\n\n🎬 Streaming Example")
    print("=" * 50)
    
    provider = ModelProvider(
        rpc_url=os.getenv("RPC_URL", "http://localhost:8545"),
        private_key=os.getenv("PRIVATE_KEY"),
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=3
    )
    
    query = "I think the secret word might be uomi"
    print(f"🔄 Streaming query: {query}")
    print("📡 Response (streaming):")
    
    async for chunk in provider.query_stream(query):
        print(chunk, end='', flush=True)
    
    print(f"\n\n🎮 Game blocked: {provider.is_game_blocked()}")

if __name__ == "__main__":
    print("ModelProvider Uomi Detection Example")
    print("=" * 60)
    print("This example demonstrates the complete workflow:")
    print("1. Normal game queries")
    print("2. Uomi detection and game blocking")
    print("3. Wallet address collection")
    print("4. Prize distribution")
    print("5. Streaming responses")
    print("=" * 60)
    
    # Run examples
    asyncio.run(game_session_example())
    asyncio.run(streaming_example())
