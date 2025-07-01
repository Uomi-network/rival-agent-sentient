# Rival Agent 🤖⚡

A blockchain-powered AI agent that combines internet search capabilities with smart contract interactions to provide intelligent, decentralized responses.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Production Ready](https://img.shields.io/badge/production-ready-green.svg)](https://github.com/your-org/rival-agent)

## 🚀 Features

- **🔗 Blockchain AI Integration**: Submit queries to smart contracts and receive AI-generated responses
- **⚡ Streaming Responses**: Real-time response streaming for better user experience
- **🔒 Secure Transaction Signing**: Support for private key management and transaction signing
- **🧪 Mock Mode**: Test without real blockchain transactions
- **📊 Production Ready**: Comprehensive logging, error handling, and monitoring

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   User Query    │───▶│   Rival Agent    │───▶│  Blockchain AI  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                              ┌─────────────────┐
                                              │ Smart Contract  │
                                              │   (callAgent)   │
                                              └─────────────────┘
```

## 📦 Installation

### From Source

```bash
git clone https://github.com/Uomi-Network/rival-agent-sentient.git
cd rival-agent-sentient
pip install -e .
```

### Development Installation

```bash
git clone https://github.com/Uomi-Network/rival-agent-sentient.git
cd rival-agent-sentient
pip install -e ".[dev]"
```

## ⚙️ Configuration

1. **Copy environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Configure environment variables:**
   ```bash
   # Required
   BLOCKCHAIN_RPC_URL="https://your-rpc-endpoint.com"
   
   # Optional for testing (uses mock mode if not provided)
   BLOCKCHAIN_PRIVATE_KEY="0x..."
   CONTRACT_ADDRESS="0x609a8aeeef8b89be02c5b59a936a520547252824"
   NFT_ID="3"
   ```

## 🚀 Quick Start

### Command Line

```bash
# Start the agent server
rival-agent
```

### Python Code

```python
from rival_agent import RivalAgent

# Create and run agent
agent = RivalAgent(name="MyRival")

# Get agent status
status = agent.get_status()
print(f"Blockchain connected: {status['blockchain_status']['connected']}")
```

### Advanced Usage

```python
import asyncio
from rival_agent.providers import ModelProvider, SearchProvider

async def main():
    # Initialize providers directly
    model_provider = ModelProvider(
        rpc_url="https://your-rpc.com",
        private_key="0x...",
        contract_address="0x...",
        nft_id=3
    )
    
     
    # Query blockchain AI
    response = await model_provider.query("What is DeFi?")
    print(response)
    

asyncio.run(main())
```

## 🧪 Testing

### Mock Mode (No Blockchain Transactions)

```python
from rival_agent import RivalAgent

# Initialize without private key for testing
agent = RivalAgent()
# Agent will run in mock mode automatically
```

### Unit Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=rival_agent

# Run specific test
pytest tests/test_model_provider.py
```

## 🔧 API Reference

### RivalAgent

Main agent class that combines search and blockchain AI capabilities.

```python
class RivalAgent(AbstractAgent):
    def __init__(self, name: str = "Rival")
    async def assist(self, session, query, response_handler)
    def get_status(self) -> dict
```

### ModelProvider

Blockchain AI model provider for smart contract interactions.

```python
class ModelProvider:
    def __init__(self, rpc_url, private_key=None, contract_address, nft_id)
    async def query(self, query: str) -> str
    async def query_stream(self, query: str) -> AsyncIterator[str]
    def get_connection_status(self) -> dict
```


## 🌐 Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8000
CMD ["rival-agent"]
```

### Docker Compose

```yaml
version: '3.8'
services:
  rival-agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - BLOCKCHAIN_RPC_URL=${BLOCKCHAIN_RPC_URL}
      - BLOCKCHAIN_PRIVATE_KEY=${BLOCKCHAIN_PRIVATE_KEY}
      - CONTRACT_ADDRESS=${CONTRACT_ADDRESS}
      - NFT_ID=${NFT_ID}
```

### Production Environment

```bash
# Set production environment variables
export ENVIRONMENT="production"
export LOG_LEVEL="INFO"
export HOST="0.0.0.0"
export PORT="8000"

# Run with production settings
rival-agent
```

## 🔒 Security

### Private Key Management

- **Never commit private keys** to version control
- Use environment variables or secure vaults
- Consider hardware wallet integration for high-value operations
- Enable mock mode for development/testing

### Transaction Safety

- Automatic gas estimation and limits
- Transaction receipt verification
- Event validation and monitoring
- Timeout handling for stuck transactions

## 📊 Monitoring

### Health Checks

```python
# Check agent status
status = agent.get_status()
print(f"Blockchain connected: {status['blockchain_status']['connected']}")
print(f"Pending requests: {status['pending_requests']}")
```

### Logging

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Clone repository
git clone https://github.com/your-org/rival-agent.git
cd rival-agent

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [https://rival-agent.readthedocs.io/](https://rival-agent.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/your-org/rival-agent/issues)
- **Discord**: [Join our community](https://discord.gg/rival-agent)

## 🙏 Acknowledgments

- [Sentient Agent Framework](https://github.com/sentient-ai/agent-framework)
- [Web3.py](https://github.com/ethereum/web3.py)

---

**Built with ❤️ by the Rival Agent Team**
