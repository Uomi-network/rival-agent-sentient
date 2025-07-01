"""
Rival Agent Providers

This module contains the core providers for the Rival Agent:
- ModelProvider: Blockchain-based AI model provider that submits transactions to smart contracts  
"""

from .model_provider import ModelProvider
from .search_provider import SearchProvider

__all__ = ["ModelProvider", "SearchProvider"]
