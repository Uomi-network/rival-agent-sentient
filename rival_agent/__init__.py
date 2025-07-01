"""
Rival Agent - A blockchain-powered AI agent with search capabilities.

This package provides a production-ready AI agent that combines:
- Blockchain AI model interactions via smart contracts
- Internet search capabilities via Tavily API
- Sentient Agent Framework integration

Main Components:
- RivalAgent: The main agent class
- ModelProvider: Blockchain AI model provider
- SearchProvider: Internet search provider
"""

from .rival_agent import RivalAgent, create_agent, main
from .providers import ModelProvider, SearchProvider

__version__ = "1.0.0"
__author__ = "Rival Agent Team"
__all__ = ["RivalAgent", "create_agent", "main", "ModelProvider", "SearchProvider"]
