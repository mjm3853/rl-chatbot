"""Factory and manager for creating and managing multiple chatbot agents of different types."""

import uuid
from typing import Optional, List, Dict, Any, Type, Union
from enum import Enum

from .agents.base import BaseAgent
from .agents.openai import OpenAIAgent
from .tools import ToolRegistry, create_default_tool_registry


class AgentType(Enum):
    """Supported agent framework types."""
    OPENAI = "openai"
    PYDANTIC_AI = "pydantic_ai"
    LANGGRAPH = "langgraph"


class AgentFactory:
    """Factory for creating chatbot agents with shared tool registries."""

    # Map of agent types to their implementation classes
    _AGENT_CLASSES: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.OPENAI: OpenAIAgent,
    }

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initialize agent factory.

        Args:
            tool_registry: Shared tool registry for all agents. If None, creates default registry.
        """
        self.tool_registry = tool_registry or create_default_tool_registry()

    @classmethod
    def register_agent_type(cls, agent_type: AgentType, agent_class: Type[BaseAgent]):
        """
        Register a new agent type.

        Args:
            agent_type: The agent type enum value
            agent_class: The agent class that implements BaseAgent
        """
        cls._AGENT_CLASSES[agent_type] = agent_class

    def create_agent(
        self,
        agent_type: Union[AgentType, str] = AgentType.OPENAI,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        conversation_id: Optional[str] = None,
        **kwargs
    ) -> BaseAgent:
        """
        Create a new agent with the shared tool registry.

        Args:
            agent_type: Type of agent to create (default: OpenAI)
            model: Model name (optional, uses default if not specified)
            temperature: Temperature parameter (optional)
            conversation_id: Conversation ID (optional, generates new if not specified)
            **kwargs: Additional framework-specific parameters

        Returns:
            New BaseAgent instance

        Raises:
            ValueError: If agent_type is not registered
        """
        # Convert string to AgentType if necessary
        if isinstance(agent_type, str):
            try:
                agent_type = AgentType(agent_type.lower())
            except ValueError:
                raise ValueError(
                    f"Unknown agent type: {agent_type}. "
                    f"Available types: {[t.value for t in AgentType]}"
                )

        # Get the agent class
        agent_class = self._AGENT_CLASSES.get(agent_type)
        if not agent_class:
            raise ValueError(
                f"Agent type {agent_type.value} not yet implemented. "
                f"Available types: {[t.value for t in self._AGENT_CLASSES.keys()]}"
            )

        # Create and return the agent
        return agent_class(
            tool_registry=self.tool_registry,
            model=model,
            temperature=temperature,
            conversation_id=conversation_id,
            **kwargs
        )

    def get_tool_registry(self) -> ToolRegistry:
        """Get the shared tool registry."""
        return self.tool_registry

    @classmethod
    def list_available_agent_types(cls) -> List[str]:
        """
        List all available (implemented) agent types.

        Returns:
            List of agent type names
        """
        return [agent_type.value for agent_type in cls._AGENT_CLASSES.keys()]


class AgentPool:
    """Pool for managing multiple chatbot agents of different types."""

    def __init__(
        self,
        factory: Optional[AgentFactory] = None,
        initial_size: int = 0,
        agent_type: Union[AgentType, str] = AgentType.OPENAI,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
    ):
        """
        Initialize agent pool.

        Args:
            factory: Agent factory to use. If None, creates new factory with default tools.
            initial_size: Number of agents to create initially
            agent_type: Type of agents to create
            model: Default model for agents
            temperature: Default temperature for agents
        """
        self.factory = factory or AgentFactory()
        self.agents: Dict[str, BaseAgent] = {}
        self.default_agent_type = agent_type
        self.default_model = model
        self.default_temperature = temperature

        # Create initial agents
        for _ in range(initial_size):
            self.create_agent()

    def create_agent(
        self,
        agent_id: Optional[str] = None,
        agent_type: Optional[Union[AgentType, str]] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        **kwargs
    ) -> BaseAgent:
        """
        Create and register a new agent in the pool.

        Args:
            agent_id: ID for the agent (optional, generates new if not specified)
            agent_type: Type of agent to create (optional, uses pool default if not specified)
            model: Model name (optional, uses pool default if not specified)
            temperature: Temperature parameter (optional, uses pool default if not specified)
            **kwargs: Additional framework-specific parameters

        Returns:
            New BaseAgent instance
        """
        if agent_id is None:
            agent_id = str(uuid.uuid4())

        agent = self.factory.create_agent(
            agent_type=agent_type or self.default_agent_type,
            model=model or self.default_model,
            temperature=temperature or self.default_temperature,
            conversation_id=agent_id,
            **kwargs
        )

        self.agents[agent_id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Get an agent by ID."""
        return self.agents.get(agent_id)

    def remove_agent(self, agent_id: str):
        """Remove an agent from the pool."""
        if agent_id in self.agents:
            del self.agents[agent_id]

    def reset_agent(self, agent_id: str, clear_conversation_id: bool = False):
        """Reset an agent's state."""
        agent = self.agents.get(agent_id)
        if agent:
            agent.reset(clear_conversation_id=clear_conversation_id)

    def reset_all(self, clear_conversation_ids: bool = False):
        """Reset all agents in the pool."""
        for agent in self.agents.values():
            agent.reset(clear_conversation_id=clear_conversation_ids)

    def list_agents(self) -> List[str]:
        """Get list of all agent IDs in the pool."""
        return list(self.agents.keys())

    def size(self) -> int:
        """Get number of agents in the pool."""
        return len(self.agents)

    def get_tool_registry(self) -> ToolRegistry:
        """Get the shared tool registry."""
        return self.factory.get_tool_registry()

    def get_agents_by_type(self, agent_type: Union[AgentType, str]) -> List[BaseAgent]:
        """
        Get all agents of a specific type.

        Args:
            agent_type: The agent type to filter by

        Returns:
            List of agents matching the type
        """
        if isinstance(agent_type, str):
            agent_type_str = agent_type.lower()
        else:
            agent_type_str = agent_type.value

        return [
            agent for agent in self.agents.values()
            if agent.__class__.__module__.split('.')[-2] == agent_type_str
        ]
