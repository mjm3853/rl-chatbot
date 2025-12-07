# Adding a New Agent Framework

This guide shows how to add support for a new agent framework (e.g., Pydantic AI, LangGraph, AutoGPT, etc.) to the RL Chatbot project.

## Overview

The RL Chatbot project supports multiple agent frameworks through a common `BaseAgent` interface. This allows different agent implementations to work seamlessly with the evaluation and RL training systems.

## Step 1: Create Agent Implementation Directory

Create a new directory under `src/rl_chatbot/agents/` for your framework:

```bash
mkdir -p src/rl_chatbot/agents/your_framework
touch src/rl_chatbot/agents/your_framework/__init__.py
touch src/rl_chatbot/agents/your_framework/agent.py
```

## Step 2: Implement the BaseAgent Interface

Create your agent class in `agent.py` that inherits from `BaseAgent`:

```python
"""Your framework-based chatbot agent implementation."""

import uuid
from typing import Optional, List, Dict, Any

from ..base import BaseAgent, AgentCapabilities
from ...tools import ToolRegistry


class YourFrameworkAgent(BaseAgent, AgentCapabilities):
    """A chatbot agent using Your Framework."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        conversation_id: Optional[str] = None,
        **kwargs  # Framework-specific parameters
    ):
        # Initialize framework client
        self._model = model or "gpt-4o"
        self._temperature = temperature if temperature is not None else 1.0
        self._conversation_id = conversation_id or str(uuid.uuid4())
        self._tool_registry = tool_registry or self._create_default_registry()
        self._last_tool_calls: List[Dict[str, Any]] = []

        # TODO: Initialize your framework here
        # self.client = YourFramework(...)

    def _create_default_registry(self) -> ToolRegistry:
        from ...tools import create_default_tool_registry
        return create_default_tool_registry()

    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model

    @property
    def temperature(self) -> float:
        """Get the temperature parameter."""
        return self._temperature

    @property
    def tool_registry(self) -> ToolRegistry:
        """Get the tool registry."""
        return self._tool_registry

    def reset(self, clear_conversation_id: bool = False):
        """Reset the agent's conversation state."""
        self._last_tool_calls = []
        if clear_conversation_id:
            self._conversation_id = str(uuid.uuid4())
        # TODO: Reset your framework's state

    def get_conversation_id(self) -> str:
        """Get the current conversation ID."""
        return self._conversation_id

    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """Get tool calls from the last interaction."""
        return self._last_tool_calls

    def chat(self, user_message: str, **kwargs) -> str:
        """
        Process a user message.

        Args:
            user_message: The user's input message
            **kwargs: Framework-specific parameters

        Returns:
            The agent's response as a string
        """
        # TODO: Implement using your framework's API
        # 1. Send user message to framework
        # 2. Handle tool calling if needed
        # 3. Track tool calls in self._last_tool_calls
        # 4. Return final response
        raise NotImplementedError("Implement chat() for your framework")

    # Optional: Override capability methods
    def supports_streaming(self) -> bool:
        """Whether the agent supports streaming."""
        return True  # or False

    def supports_multimodal(self) -> bool:
        """Whether the agent supports multimodal inputs."""
        return False  # or True

    def get_supported_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self._tool_registry.list_tools()]

    # Helper methods for tool execution
    def _prepare_tools(self):
        """Convert ToolRegistry to your framework's tool format."""
        # TODO: Convert tools to framework-specific format
        pass

    def _run_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return its result."""
        tool = self._tool_registry.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            result = tool.execute(**args)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"
```

## Step 3: Export Your Agent

Update `src/rl_chatbot/agents/your_framework/__init__.py`:

```python
"""Your Framework agent implementation."""

from .agent import YourFrameworkAgent

__all__ = ["YourFrameworkAgent"]
```

## Step 4: Register Agent Type

Update `src/rl_chatbot/agents/__init__.py` to export your agent:

```python
from .your_framework import YourFrameworkAgent

__all__ = [
    "BaseAgent",
    "AgentCapabilities",
    "OpenAIAgent",
    "YourFrameworkAgent",  # Add your agent
]
```

## Step 5: Add Agent Type to Factory

Update `src/rl_chatbot/factory.py` to register your agent type:

```python
from .agents.your_framework import YourFrameworkAgent

class AgentType(Enum):
    """Supported agent framework types."""
    OPENAI = "openai"
    YOUR_FRAMEWORK = "your_framework"  # Add your type


class AgentFactory:
    _AGENT_CLASSES: Dict[AgentType, Type[BaseAgent]] = {
        AgentType.OPENAI: OpenAIAgent,
        AgentType.YOUR_FRAMEWORK: YourFrameworkAgent,  # Register your agent
    }
```

## Step 6: Add Dependencies

If your framework requires additional dependencies, add them to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies
    "your-framework>=1.0.0",  # Add your framework
]
```

Or as an optional dependency group:

```toml
[project.optional-dependencies]
your_framework = [
    "your-framework>=1.0.0",
]
```

## Step 7: Test Your Implementation

Create a test to verify your agent works:

```python
from rl_chatbot import AgentFactory, AgentType

# Test creating your agent
factory = AgentFactory()
agent = factory.create_agent(agent_type=AgentType.YOUR_FRAMEWORK)

# Test basic chat
response = agent.chat("Hello!")
print(f"Response: {response}")

# Test with tool calling
response = agent.chat("What is 5 + 3?")
print(f"Response: {response}")
print(f"Tool calls: {agent.get_last_tool_calls()}")

# Test with evaluator
from rl_chatbot import Evaluator
evaluator = Evaluator(agent)
# ... run evaluation
```

## Step 8: Create Examples

Add usage examples to `examples/your_framework_example.py` showing:
- Basic agent usage
- Tool calling
- Evaluation
- RL training (optional)

## Step 9: Update Documentation

Update the following files:
- `README.md`: Add your framework to the list of supported frameworks
- `CLAUDE.md`: Add implementation notes and gotchas
- `docs/`: Create framework-specific documentation if needed

## Framework-Specific Notes

### Mapping Tools

Each framework has its own way of defining tools. You need to convert from `ToolRegistry` format to your framework's format:

**ToolRegistry format:**
```python
{
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform calculations",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {"type": "string"}
            }
        }
    }
}
```

Convert this to your framework's expected format in `_prepare_tools()`.

### Handling Tool Calls

Extract tool calls from your framework's response and store them in the expected format:

```python
self._last_tool_calls.append({
    "id": tool_call_id,  # Unique identifier
    "name": function_name,  # Tool name
    "arguments": function_args,  # Arguments as string or dict
})
```

### Error Handling

Implement robust error handling for:
- API failures
- Tool execution errors
- Invalid tool calls
- Timeout/rate limits

## Examples

See existing implementations:
- `src/rl_chatbot/agents/openai/` - Full OpenAI implementation
- `src/rl_chatbot/agents/pydantic_ai/` - Placeholder for Pydantic AI
- `src/rl_chatbot/agents/langgraph/` - Placeholder for LangGraph

## Testing

Your agent should work with all existing evaluation and RL training code:

```python
from rl_chatbot import (
    AgentFactory,
    AgentType,
    Evaluator,
    MultiAgentEvaluator,
    RLTrainer,
)

# Single agent evaluation
agent = factory.create_agent(agent_type=AgentType.YOUR_FRAMEWORK)
evaluator = Evaluator(agent)
results = evaluator.evaluate_batch(test_cases)

# Multi-agent comparison (your framework vs OpenAI)
agents = [
    factory.create_agent(agent_type=AgentType.YOUR_FRAMEWORK),
    factory.create_agent(agent_type=AgentType.OPENAI),
]
multi_eval = MultiAgentEvaluator(agents)
comparison = multi_eval.compare_agents(test_cases)

# RL training
trainer = RLTrainer(agent)
trainer.train(test_cases, num_episodes=10)
```

## Need Help?

- Check existing implementations in `src/rl_chatbot/agents/`
- Review the `BaseAgent` interface in `src/rl_chatbot/agents/base.py`
- Look at framework-specific examples in `examples/`
- Open an issue for questions or problems
