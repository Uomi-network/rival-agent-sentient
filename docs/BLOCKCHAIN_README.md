# Real Blockchain ModelProvider

This document describes the complete implementation of a blockchain-based ModelProvider that submits real transactions to the smart contract using the `callAgent()` function.

## Overview

The ModelProvider has been transformed to:

1. **Submit real blockchain transactions** using the `callAgent()` function
2. **Listen for blockchain events** (`RequestSent` and `AgentResult`)
3. **Handle transaction signing** with private keys
4. **Manage gas fees** and transaction confirmation
5. **Provide mock mode** for testing without real transactions

## Smart Contract Integration

### Contract Function Called

```solidity
function callAgent(
    uint256 nftId,
    string inputCidFile,
    string inputData
) external payable
```

**Parameters:**
- `nftId`: The NFT ID of the agent to call
- `inputCidFile`: IPFS CID file (can be empty)
- `inputData`: The actual query/input data

### Events Listened To

**1. RequestSent Event**
```solidity
event RequestSent(
    address indexed sender,
    uint256 indexed requestId, 
    bytes indexed inputUri,
    uint256 nftId
)
```

**2. AgentResult Event**  
```solidity
event AgentResult(
    uint256 indexed requestId,
    bytes indexed output,
    uint256 indexed nftId,
    uint256 validationCount,
    uint256 totalValidator
)
```

## Configuration

### Constructor Parameters

```python
ModelProvider(
    rpc_url: str,                    # Blockchain RPC endpoint
    private_key: Optional[str],      # Private key for signing (None for mock mode)
    contract_address: str,           # Smart contract address
    nft_id: int                     # NFT ID to call
)
```

### Environment Variables

```bash
# Required for real mode
BLOCKCHAIN_RPC_URL=https://your-rpc-endpoint.com
BLOCKCHAIN_PRIVATE_KEY=0x1234...  # Your private key

# Optional (have defaults)
CONTRACT_ADDRESS=0x609a8aeeef8b89be02c5b59a936a520547252824
NFT_ID=11
```

## Usage Examples

### Mock Mode (Testing)

```python
import asyncio
from src.search_agent.providers.model_provider import ModelProvider

async def test_mock():
    provider = ModelProvider(
        rpc_url="https://rpc.ankr.com/eth",
        private_key=None,  # Mock mode
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=11
    )
    
    response = await provider.query("What is blockchain?")
    print(response)

asyncio.run(test_mock())
```

### Real Mode (Production)

```python
import asyncio
import os
from src.search_agent.providers.model_provider import ModelProvider

async def test_real():
    provider = ModelProvider(
        rpc_url=os.getenv("BLOCKCHAIN_RPC_URL"),
        private_key=os.getenv("BLOCKCHAIN_PRIVATE_KEY"),
        contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
        nft_id=11
    )
    
    # This will submit a real transaction
    response = await provider.query("Explain smart contracts")
    print(response)

asyncio.run(test_real())
```

### Streaming Response

```python
async def test_streaming():
    provider = ModelProvider(...)
    
    async for chunk in provider.query_stream("Tell me about DeFi"):
        print(chunk, end="")
```

## Transaction Flow

1. **Submit Transaction**: `callAgent()` function called with query data
2. **Wait for Confirmation**: Transaction receipt received
3. **Listen for RequestSent**: Confirms transaction was accepted
4. **Listen for AgentResult**: Agent processing complete
5. **Extract Output**: Decode output bytes and return to user

## Key Features

### Real Blockchain Integration
- ✅ Web3.py integration for Ethereum-compatible chains
- ✅ Contract ABI loading from `abi.json`
- ✅ Automatic gas estimation and transaction signing
- ✅ Event filtering and listening
- ✅ Transaction receipt waiting

### Mock Mode for Development
- ✅ No real transactions or gas fees
- ✅ Simulated event flow
- ✅ Same interface as real mode
- ✅ Perfect for testing and development

### Error Handling
- ✅ Connection failure handling
- ✅ Transaction failure detection
- ✅ Timeout management (5 minutes default)
- ✅ Gas estimation failures
- ✅ Contract interaction errors

### Request Management
- ✅ Transaction hash tracking
- ✅ Request status monitoring
- ✅ Pending request cancellation
- ✅ Connection status monitoring

## Dependencies

```bash
# Core blockchain dependency
web3==6.15.1

# Automatically installed with web3:
# - eth-account (transaction signing)
# - eth-abi (contract interaction)
# - eth-utils (utilities)
# - hexbytes (data handling)
```

## File Structure

```
examples/search_agent/
├── abi.json                           # Smart contract ABI
├── src/search_agent/providers/
│   └── model_provider.py             # Main blockchain provider
├── real_blockchain_example.py        # Comprehensive example
├── test_blockchain.py               # Simple test script
└── .env.example                     # Environment variables
```

## Error Handling Examples

### Connection Errors
```python
try:
    response = await provider.query("test")
except Exception as e:
    if "Failed to connect" in str(e):
        print("Blockchain connection failed")
    elif "Transaction failed" in str(e):
        print("Transaction was rejected")
    elif "timed out" in str(e):
        print("Request took too long")
```

### Gas Estimation
```python
# The provider automatically handles gas estimation
# Default: 500,000 gas limit, 20 gwei gas price
# Customize in _submit_transaction() if needed
```

## Security Considerations

### Private Key Management
- ✅ Use environment variables for private keys
- ✅ Never commit private keys to version control
- ✅ Use secure key storage in production
- ✅ Consider using hardware wallets for high-value accounts

### Transaction Safety
- ✅ Gas limit estimation to prevent excessive fees
- ✅ Transaction receipt verification
- ✅ Event validation to ensure correct responses
- ✅ Timeout handling to prevent hanging requests

## Monitoring and Debugging

### Connection Status
```python
status = provider.get_connection_status()
print(f"Connected: {status['connected']}")
print(f"Chain ID: {status['chain_id']}")
print(f"Wallet: {status['wallet_address']}")
```

### Pending Requests
```python
pending = provider.get_pending_requests()
for tx_hash, info in pending.items():
    print(f"TX {tx_hash}: {info['status']}")
```

### Logging
The provider uses Python logging with these levels:
- `INFO`: Normal operations, transaction submissions
- `WARNING`: Mock mode usage, minor issues
- `ERROR`: Connection failures, transaction errors

## Production Deployment

### Prerequisites
1. **RPC Endpoint**: Reliable blockchain RPC provider
2. **Private Key**: Funded wallet with ETH for gas
3. **Contract Verification**: Ensure contract exists and is correct
4. **Network Configuration**: Correct chain ID and network settings

### Recommended Settings
```python
# For production use
provider = ModelProvider(
    rpc_url="https://your-premium-rpc.com",  # Use premium RPC
    private_key=os.getenv("BLOCKCHAIN_PRIVATE_KEY"),
    contract_address="0x609a8aeeef8b89be02c5b59a936a520547252824",
    nft_id=11
)

# Adjust timeouts if needed
provider.max_wait_time = 600.0  # 10 minutes for slower networks
provider.polling_interval = 3.0  # 3 seconds for better reliability
```

## Migration from API Version

The blockchain version maintains the same public interface:

```python
# These methods work exactly the same
response = await provider.query("question")
async for chunk in provider.query_stream("question"):
    print(chunk)
```

**Key Differences:**
- Constructor takes blockchain parameters instead of API key
- Responses come from blockchain agents instead of language models
- Transactions require gas fees (in real mode)
- Longer response times due to blockchain confirmation

The SearchAgent and other components require no changes!
