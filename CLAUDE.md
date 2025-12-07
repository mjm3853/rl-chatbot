# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

RL Chatbot is a learning project for practicing reinforcement learning with tool-calling chatbots. It provides a complete scaffold for building, evaluating, and training chatbots using OpenAI's Responses API.

## Development Commands

### Setup
```bash
# Install dependencies (recommended)
uv sync

# Or using pip
pip install -e .

# Set up environment
cp .env.sample .env
# Then edit .env and add OPENAI_API_KEY
```

### Running Components
```bash
# Run interactive chatbot (CLI)
uv run chatbot

# Evaluate chatbot on test cases (CLI)
uv run evaluate

# Run RL training (CLI)
uv run train

# Start API server
uv run server
# Access API docs at http://localhost:8000/docs
```

### Testing & Code Quality
```bash
# Run tests
pytest tests/

# Format code
black src/ tests/

# Lint code
ruff check src/ tests/
```

## Architecture

### Core Components

1. **BaseAgent Interface** (`src/rl_chatbot/agents/base.py`)
   - Abstract base class that all agent implementations must inherit from
   - Defines common interface: `chat()`, `reset()`, `get_conversation_id()`, `get_last_tool_calls()`
   - Properties: `model`, `temperature`
   - Optional capabilities mixin: streaming, multimodal, function calling support
   - Enables framework-agnostic evaluation and RL training

2. **Agent Implementations** (`src/rl_chatbot/agents/`)
   - **OpenAIAgent** (`agents/openai/`): Uses OpenAI Responses API with function calling
     - Built-in agentic loop handles tool calls automatically
     - Stateful multi-turn conversations with context management
     - Tracks tool calls via `get_last_tool_calls()` for evaluation
     - Supports `previous_response_id` for response chaining
   - **PydanticAIAgent** (`agents/pydantic_ai/`): Placeholder for Pydantic AI implementation
   - **LangGraphAgent** (`agents/langgraph/`): Placeholder for LangGraph implementation
   - All implementations share the same BaseAgent interface

3. **Tool System** (`src/rl_chatbot/tools/`)
   - Modular architecture: one tool per file for easy addition/removal
   - **Base classes** (`tools/base.py`):
     - `Tool`: Pydantic model with name, description, parameters, function
     - `ToolRegistry`: Manages tool registration and schema generation
   - **Default tools**:
     - `calculate.py`: Mathematical expression evaluation
     - `search.py`: Web search (mock implementation)
     - `weather.py`: Weather information (mock implementation)
   - **Adding new tools**: See `src/rl_chatbot/tools/README.md` for detailed guide
     1. Create new file with tool function and `create_*_tool()` factory
     2. Register in `__init__.py`'s `create_default_tool_registry()`
     3. Tool automatically available to all agents!
   - **Shared across multiple agents** for resource efficiency

4. **Multi-Agent System** (`src/rl_chatbot/factory.py`)
   - **AgentFactory**: Creates agents of different types with shared tool registries
     - Supports multiple frameworks via `AgentType` enum (OPENAI, PYDANTIC_AI, LANGGRAPH)
     - `create_agent(agent_type, model, temperature, ...)`  - Framework-agnostic creation
     - Extensible: register new agent types with `register_agent_type()`
   - **AgentPool**: Manages multiple agents with shared resources
     - Can contain agents of different frameworks
     - Supports different configurations (models, temperatures) per agent
     - Enables batch operations and agent comparison
     - `get_agents_by_type()` - Filter agents by framework

5. **Evaluation Framework** (`src/rl_chatbot/evaluation/`)
   - Works with any agent implementing BaseAgent interface
   - **Evaluator**: Runs test cases and computes metrics for single agent
   - **MultiAgentEvaluator**: Evaluates and compares multiple agents (can mix frameworks)
   - **MetricCalculator**: Computes task success, tool efficiency, response quality
   - **Metrics dataclass**: Container for evaluation scores
   - Supports batch evaluation, agent ranking, and saving results to JSON

6. **RL Training** (`src/rl_chatbot/rl/`)
   - Works with any agent implementing BaseAgent interface
   - **RLTrainer**: Scaffold for single-agent RL training loop (episode collection, checkpointing)
   - **MultiAgentRLTrainer**: Trains multiple agents and selects best performer (can mix frameworks)
   - **RewardFunction**: Computes composite rewards for training
   - Currently a scaffold - full RL implementation (PPO, DQN) intended for future development

7. **API Server** (`src/rl_chatbot/server/`)
   - FastAPI-based REST API for UI integration
   - SQLite database with SQLModel ORM for persistence
   - WebSocket support for real-time chat and progress updates
   - **Key endpoints**:
     - `/api/v1/agents` - Agent CRUD
     - `/api/v1/chat` - REST and WebSocket chat
     - `/api/v1/conversations` - Conversation history
     - `/api/v1/test-cases` - Test case management
     - `/api/v1/evaluations` - Run evaluations with progress via WebSocket
     - `/api/v1/training` - Run training with progress via WebSocket
     - `/api/v1/tools` - List available tools
   - **Database migrations**: Managed with Alembic (`uv run alembic upgrade head`)

### Key Design Patterns

**OpenAI Responses API Flow**:
- Uses `client.responses.create()` instead of `client.chat.completions.create()`
- Input: Can be string or array of items (messages, function_call_output, etc.)
- Output: Returns response with `output_text` and `output` array of items
- Items: Union types including `message`, `function_call`, `function_call_output`, `reasoning`
- Built-in agentic loop: Model can call multiple tools within one request
- Stateful by default: Uses `store: true` for conversation continuity
- Context management: Append `response.output` to context for multi-turn

**Tool Execution Pattern**:
1. Prepare tools in internally-tagged format (name, description, parameters at top level)
2. Send request with tools and input (context)
3. Model returns `output` array with items including `function_call` items
4. Extract and track function calls with `call_id`
5. Execute tools locally via ToolRegistry
6. Append `function_call_output` items to context with `call_id` and `output`
7. Send follow-up request with updated context
8. Model processes tool results and returns final response

**Evaluation Pattern**:
- Test cases include: user_input, expected_output, expected_tools, task_type
- Metrics weighted: task_success (0.5), tool_efficiency (0.3), response_quality (0.2)
- Task types: exact_match, contains, semantic (placeholder)

**Multi-Agent Pattern**:
- **Shared Tool Registry**: Single registry shared across all agents for efficiency
- **AgentFactory**: Creates agents with consistent tool access
- **AgentPool**: Manages multiple agents with different configurations
  - Each agent has unique conversation_id
  - All agents share same tool implementations
  - Supports batch reset and agent lifecycle management
- **Multi-Agent Evaluation**: Compare agents on same test cases, rank by metrics
- **Multi-Agent Training**: Train multiple agents independently, select best performer

## Environment Configuration

Required in `.env`:
- `OPENAI_API_KEY` - Required for API calls
- `OPENAI_MODEL` - Default: gpt-4o
- `OPENAI_TEMPERATURE` - Default: 0.7
- `WANDB_API_KEY` - Optional for experiment tracking

## Important Implementation Notes

### RL Training Status
- Current implementation is a scaffold/template
- Missing: Gymnasium environment wrapper, actual policy network, RL algorithm integration
- Stable-baselines3 included as dependency but not integrated
- Training loop collects episodes and rewards but doesn't update policy

### Test Cases
- Sample test cases in evaluator.py (create_sample_test_cases)
- Evaluator expects JSON file format: list of dicts with user_input, expected_output, expected_tools, task_type
- Results saved to `data/evaluation_results.json`

## Project Structure
```
src/rl_chatbot/
├── agents/                    # Agent implementations for different frameworks
│   ├── base.py               # BaseAgent interface - all agents must implement
│   ├── openai/               # OpenAI Responses API implementation
│   │   └── agent.py          # OpenAIAgent class
│   ├── pydantic_ai/          # Pydantic AI implementation (placeholder)
│   └── langgraph/            # LangGraph implementation (placeholder)
├── tools/                     # Tool definitions and registry
│   ├── base.py               # Tool and ToolRegistry classes
│   ├── calculate.py          # Calculator tool
│   ├── search.py             # Search tool (mock)
│   └── weather.py            # Weather tool (mock)
├── factory.py                 # AgentFactory and AgentPool for multi-agent
├── evaluation/
│   ├── evaluator.py          # Single and multi-agent evaluators
│   └── metrics.py            # Metric calculations
├── rl/
│   ├── trainer.py            # RL trainers (scaffold)
│   └── reward.py             # Reward function
└── server/                    # FastAPI server
    ├── main.py               # FastAPI app entry point
    ├── config.py             # Server configuration
    ├── database.py           # SQLite database connection
    ├── models/               # SQLModel database models
    ├── schemas/              # Pydantic request/response schemas
    ├── routers/              # API route handlers
    ├── services/             # Business logic layer
    └── websocket/            # WebSocket handlers

migrations/                    # Alembic database migrations
data/                         # Database and evaluation results
```

## Dependencies
- Primary package manager: `uv` (fast, modern)
- Python: >=3.10
- Key libraries: openai>=1.0.0, gymnasium, stable-baselines3, wandb (optional)
- Dev tools: black (line-length 100), ruff, pytest

## Common Development Tasks

### Adding New Tools
1. Create function in `tools.py`
2. Add Tool registration in `create_default_tool_registry()`
3. Include JSON schema for parameters
4. Tools automatically available to all agents through shared registry

### Creating Test Cases
- Format: `{"user_input": str, "expected_output": str, "expected_tools": List[str], "task_type": str}`
- Save as JSON array in `data/` directory
- Use with `evaluator.evaluate_from_file(filepath)`

### Working with Multiple Agents

**Creating an Agent Pool**:
```python
from rl_chatbot.chatbot import AgentPool

# Create pool with 3 agents sharing tools
pool = AgentPool(initial_size=3, model="gpt-4o")

# Get an agent
agent = pool.get_agent(agent_id)

# Reset all agents
pool.reset_all()
```

**Using Agent Factory**:
```python
from rl_chatbot.chatbot import AgentFactory

factory = AgentFactory()  # Creates shared tool registry

# Create agents with different configs
agent1 = factory.create_agent(temperature=0.5)
agent2 = factory.create_agent(temperature=1.5)
```

**Evaluating Multiple Agents**:
```python
from rl_chatbot.evaluation.evaluator import MultiAgentEvaluator

evaluator = MultiAgentEvaluator(pool)  # or list of agents
comparison = evaluator.compare_agents(test_cases)

# Get rankings
best_agent_id = comparison["best_overall"]
rankings = comparison["rankings"]["reward"]
```

**Training Multiple Agents**:
```python
from rl_chatbot.rl.trainer import MultiAgentRLTrainer

trainer = MultiAgentRLTrainer(pool)  # or list of agents
trainer.train_all_agents(test_cases, num_episodes=10)

# Get best agent
best_id, best_agent = trainer.get_best_agent(test_cases)
```

### Adding a New Agent Framework

See `docs/ADDING_NEW_AGENT_FRAMEWORK.md` for complete guide. Quick overview:

1. Create new directory: `src/rl_chatbot/agents/your_framework/`
2. Implement agent class inheriting from `BaseAgent`:
   ```python
   class YourFrameworkAgent(BaseAgent, AgentCapabilities):
       def chat(self, user_message: str, **kwargs) -> str:
           # Implement using your framework
       def reset(self, clear_conversation_id: bool = False):
           # Reset state
       # ... implement other BaseAgent methods
   ```
3. Register agent type in `factory.py`:
   ```python
   class AgentType(Enum):
       YOUR_FRAMEWORK = "your_framework"

   _AGENT_CLASSES = {
       AgentType.YOUR_FRAMEWORK: YourFrameworkAgent,
   }
   ```
4. Your agent automatically works with:
   - Evaluator and MultiAgentEvaluator
   - RLTrainer and MultiAgentRLTrainer
   - AgentFactory and AgentPool
   - All existing tools through shared ToolRegistry

**Example: Compare OpenAI vs Your Framework**
```python
from rl_chatbot import AgentFactory, AgentType, MultiAgentEvaluator

factory = AgentFactory()
agents = [
    factory.create_agent(agent_type=AgentType.OPENAI),
    factory.create_agent(agent_type=AgentType.YOUR_FRAMEWORK),
]

evaluator = MultiAgentEvaluator(agents)
comparison = evaluator.compare_agents(test_cases)
print(f"Best agent: {comparison['best_overall']}")
```

### Implementing Full RL
1. Create Gymnasium environment wrapper around BaseAgent (works with any framework)
2. Define observation space (conversation state) and action space (tool selection)
3. Integrate stable-baselines3 algorithm (PPO recommended)
4. Modify trainer to use RL algorithm instead of simple episode collection
5. For multi-agent: use MultiAgentRLTrainer to compare different RL strategies or frameworks
