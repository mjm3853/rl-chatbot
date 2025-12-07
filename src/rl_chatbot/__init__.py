"""RL Chatbot: Reinforcement Learning for Tool-Calling Chatbots"""

__version__ = "0.1.0"

# Core agent framework
from .agents.base import BaseAgent, AgentCapabilities
from .agents.openai import OpenAIAgent

# Factory and pool for multi-agent management
from .factory import AgentFactory, AgentPool, AgentType

# Tools
from .tools import Tool, ToolRegistry, create_default_tool_registry

# Evaluation
from .evaluation.evaluator import Evaluator, MultiAgentEvaluator
from .evaluation.metrics import Metrics, MetricCalculator

# RL Training
from .rl.trainer import RLTrainer, MultiAgentRLTrainer
from .rl.reward import RewardFunction

__all__ = [
    # Version
    "__version__",
    # Agents
    "BaseAgent",
    "AgentCapabilities",
    "OpenAIAgent",
    # Factory
    "AgentFactory",
    "AgentPool",
    "AgentType",
    # Tools
    "Tool",
    "ToolRegistry",
    "create_default_tool_registry",
    # Evaluation
    "Evaluator",
    "MultiAgentEvaluator",
    "Metrics",
    "MetricCalculator",
    # RL Training
    "RLTrainer",
    "MultiAgentRLTrainer",
    "RewardFunction",
]

