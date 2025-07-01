#!/usr/bin/env python3
"""
Example script demonstrating the blockchain-based ModelProvider.
This script shows how to use the transformed ModelProvider that submits
transactions to a blockchain instead of calling an API.
"""

import asyncio
import logging
from src.search_agent.providers.model_provider import ModelProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def main():
    """Demonstrate blockchain-based model interactions"""
    
    # Initialize the blockchain-based model provider
    # Replace these with actual values when integrating with a real blockchain
    model_provider = ModelProvider(
        rpc_url="https://your-blockchain-rpc-url.com",
        private_key="your_private_key_here",  # In production, use environment variables
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=11
    )
    
    print("🔗 Blockchain-based ModelProvider initialized")
    print(f"RPC URL: {model_provider.rpc_url}")
    print(f"Contract Address: {model_provider.contract_address}")
    print(f"NFT ID: {model_provider.nft_id}")
    print("-" * 50)
    
    # Example 1: Simple query
    print("📤 Submitting query to blockchain...")
    query = "What is the weather like today?"
    
    try:
        response = await model_provider.query(query)
        print(f"✅ Response received: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 50)
    
    # Example 2: Streaming query
    print("📤 Submitting streaming query to blockchain...")
    streaming_query = "Tell me a short story about blockchain technology"
    
    try:
        print("📺 Streaming response:")
        async for chunk in model_provider.query_stream(streaming_query):
            print(chunk, end="", flush=True)
        print("\n✅ Streaming completed")
    except Exception as e:
        print(f"❌ Streaming error: {e}")
    
    print("-" * 50)
    
    # Example 3: Check pending requests
    pending = model_provider.get_pending_requests()
    print(f"📋 Pending requests: {len(pending)}")
    for req_id, req_info in pending.items():
        print(f"  Request {req_id}: {req_info['status']}")
    
    print("\n🏁 Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
