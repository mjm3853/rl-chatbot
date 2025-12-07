"""Base interface for all chatbot agents.

This module defines the abstract base class that all agent implementations
must inherit from, ensuring a consistent interface across different frameworks
(OpenAI, Pydantic AI, LangGraph, etc.).
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseAgent(ABC):
    """
    Abstract base class for all chatbot agents.

    All agent implementations (OpenAI, Pydantic AI, LangGraph, etc.) must
    implement this interface to be compatible with the evaluation and RL
    training frameworks.
    """

    @abstractmethod
    def chat(self, user_message: str, **kwargs) -> str:
        """
        Process a user message and return a response.

        Args:
            user_message: The user's input message
            **kwargs: Additional framework-specific parameters

        Returns:
            The agent's response as a string
        """
        pass

    @abstractmethod
    def reset(self, clear_conversation_id: bool = False):
        """
        Reset the agent's conversation state.

        Args:
            clear_conversation_id: Whether to generate a new conversation ID
        """
        pass

    @abstractmethod
    def get_conversation_id(self) -> str:
        """
        Get the current conversation ID.

        Returns:
            The conversation ID as a string
        """
        pass

    @abstractmethod
    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """
        Get tool calls from the last interaction.

        Returns:
            List of dictionaries containing tool call information.
            Each dict should have at least: {"name": str, "arguments": str/dict}
        """
        pass

    @property
    @abstractmethod
    def model(self) -> str:
        """
        Get the model name/identifier.

        Returns:
            Model name as a string
        """
        pass

    @property
    @abstractmethod
    def temperature(self) -> float:
        """
        Get the temperature parameter.

        Returns:
            Temperature value as a float
        """
        pass

    def get_config(self) -> Dict[str, Any]:
        """
        Get the agent's configuration.

        Returns:
            Dictionary with agent configuration
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "conversation_id": self.get_conversation_id(),
            "framework": self.__class__.__module__.split('.')[-2],  # Extract framework name
        }


class AgentCapabilities:
    """
    Mixin class for optional agent capabilities.

    Agents can inherit from this to provide additional functionality
    beyond the base interface.
    """

    def supports_streaming(self) -> bool:
        """Whether the agent supports streaming responses."""
        return False

    def supports_multimodal(self) -> bool:
        """Whether the agent supports multimodal inputs (images, audio, etc.)."""
        return False

    def supports_function_calling(self) -> bool:
        """Whether the agent supports function/tool calling."""
        return True

    def get_supported_tools(self) -> List[str]:
        """
        Get list of tool names this agent can use.

        Returns:
            List of tool names
        """
        return []
