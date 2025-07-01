#!/usr/bin/env python3
"""
Real blockchain example - shows how to use ModelProvider with actual blockchain transactions.
This example demonstrates both mock mode (for testing) and real mode (for production).
"""

import asyncio
import sys
import os
import logging

# Add the current directory to Python path
sys.path.append('.')

from src.search_agent.providers.model_provider import ModelProvider

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_mock_mode():
    """Test with mock mode (no real blockchain transactions)"""
    print("🧪 Testing Mock Mode (No Real Transactions)")
    print("-" * 50)
    
    provider = ModelProvider(
        rpc_url="https://rpc.ankr.com/eth",  # Real RPC but no private key
        private_key=None,  # Mock mode
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=11
    )
    
    status = provider.get_connection_status()
    print(f"📊 Connection Status:")
    print(f"   RPC URL: {status['rpc_url']}")
    print(f"   Connected: {status['connected']}")
    print(f"   Contract: {status['contract_address']}")
    print(f"   Wallet: {status['wallet_address']}")
    print(f"   NFT ID: {status['nft_id']}")
    
    print(f"\n📤 Submitting query...")
    response = await provider.query("Explain blockchain consensus mechanisms")
    print(f"✅ Response: {response}")
    
    return provider

async def test_real_mode_setup():
    """Show how to set up real mode (with actual private key)"""
    print("\n🔐 Real Mode Setup Instructions")
    print("-" * 50)
    
    print("To use real blockchain transactions, you need:")
    print("1. Set environment variable BLOCKCHAIN_PRIVATE_KEY=your_private_key")
    print("2. Set environment variable BLOCKCHAIN_RPC_URL=your_rpc_endpoint")
    print("3. Ensure your wallet has enough ETH for gas fees")
    print("4. Make sure the contract exists at the specified address")
    
    # Check if real credentials are available
    private_key = os.getenv("BLOCKCHAIN_PRIVATE_KEY")
    rpc_url = os.getenv("BLOCKCHAIN_RPC_URL")
    
    if private_key and rpc_url:
        print("\n✅ Real credentials found! Testing real mode...")
        
        provider = ModelProvider(
            rpc_url=rpc_url,
            private_key=private_key,
            contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
            nft_id=11
        )
        
        status = provider.get_connection_status()
        print(f"📊 Real Connection Status:")
        print(f"   Connected: {status['connected']}")
        print(f"   Chain ID: {status.get('chain_id', 'Unknown')}")
        print(f"   Wallet: {status['wallet_address']}")
        
        if status['connected']:
            print(f"\n📤 Submitting REAL transaction...")
            try:
                response = await provider.query("What is DeFi?")
                print(f"✅ Real Response: {response}")
            except Exception as e:
                print(f"❌ Real transaction failed: {e}")
        else:
            print("❌ Failed to connect to blockchain")
    else:
        print("\n📝 No real credentials provided - staying in mock mode")
        print("   To test real mode, set these environment variables:")
        print("   export BLOCKCHAIN_PRIVATE_KEY='0x...'")
        print("   export BLOCKCHAIN_RPC_URL='https://...'")

async def demonstrate_events():
    """Demonstrate the event system"""
    print("\n📡 Event System Demonstration")
    print("-" * 50)
    
    print("The ModelProvider listens for these blockchain events:")
    print("1. RequestSent - When callAgent() transaction is confirmed")
    print("   - Contains: sender, requestId, inputUri, nftId")
    print("2. AgentResult - When the agent provides output")
    print("   - Contains: requestId, output, nftId, validationCount, totalValidator")
    
    print("\nEvent flow:")
    print("1. Submit callAgent() transaction → RequestSent event")
    print("2. Agent processes request → AgentResult event")
    print("3. Extract output from AgentResult.output")

async def main():
    """Main demonstration function"""
    print("🚀 Blockchain ModelProvider Demonstration")
    print("=" * 60)
    
    # Test mock mode
    provider = await test_mock_mode()
    
    # Show real mode setup
    await test_real_mode_setup()
    
    # Demonstrate event system
    await demonstrate_events()
    
    print("\n🎯 Key Features:")
    print("✅ Real blockchain transaction submission via callAgent()")
    print("✅ Event listening for RequestSent and AgentResult")
    print("✅ Mock mode for testing without real transactions")
    print("✅ Automatic gas estimation and transaction signing")
    print("✅ Contract ABI loading and function calling")
    print("✅ Streaming response support")
    print("✅ Request tracking and timeout handling")
    
    print("\n📋 Summary:")
    print("- Mock mode: Perfect for development and testing")
    print("- Real mode: Ready for production blockchain interactions")
    print("- Maintains same interface as original ModelProvider")
    print("- Fully compatible with existing SearchAgent code")

if __name__ == "__main__":
    asyncio.run(main())
