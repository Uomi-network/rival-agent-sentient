#!/usr/bin/env python3
"""
Test script to demonstrate the real blockchain ModelProvider functionality
"""

import asyncio
import sys
import os

# Add the current directory to Python path
sys.path.append('.')

from src.search_agent.providers.model_provider import ModelProvider

async def test_blockchain_provider():
    """Test the blockchain-based ModelProvider"""
    print("🧪 Testing Real Blockchain ModelProvider")
    print("-" * 40)
    
    # Initialize with mock configuration (no private key for testing)
    provider = ModelProvider(
        rpc_url="https://rpc.ankr.com/eth",  # Public Ethereum RPC
        private_key=None,  # Will use mock mode
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=11
    )
    
    print(f"✅ Provider initialized")
    print(f"   RPC URL: {provider.rpc_url}")
    print(f"   Contract: {provider.contract_address}")
    print(f"   NFT ID: {provider.nft_id}")
    print(f"   Private Key: {'MOCK' if not provider.private_key else 'REAL'}")
    
    # Check connection status
    status = provider.get_connection_status()
    print(f"   Connected: {status['connected']}")
    print(f"   Chain ID: {status.get('chain_id', 'Unknown')}")
    
    # Test simple query
    print("\n📤 Testing simple query...")
    try:
        response = await provider.query("What is blockchain technology?")
        print(f"✅ Response: {response}")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    # Test streaming query
    print("\n📤 Testing streaming query...")
    try:
        print("📺 Stream: ", end="")
        async for chunk in provider.query_stream("Explain smart contracts briefly"):
            print(chunk, end="")
        print("\n✅ Streaming completed")
    except Exception as e:
        print(f"❌ Streaming error: {e}")
    
    # Check pending requests
    pending = provider.get_pending_requests()
    print(f"\n📋 Pending requests: {len(pending)}")
    for tx_hash, req_info in pending.items():
        print(f"  TX {tx_hash[:10]}...: {req_info['status']}")
    
    print("\n🎉 Test completed!")

if __name__ == "__main__":
    asyncio.run(test_blockchain_provider())
