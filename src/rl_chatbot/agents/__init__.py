"""
Agents module for different chatbot frameworks.

This module provides a unified interface for chatbot agents from different
frameworks (OpenAI, Pydantic AI, LangGraph, etc.).
"""

from .base import BaseAgent, AgentCapabilities

# Import available agent implementations
from .openai import OpenAIAgent

__all__ = [
    "BaseAgent",
    "AgentCapabilities",
    "OpenAIAgent",
]
