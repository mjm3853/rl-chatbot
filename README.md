# RL Chatbot: Reinforcement Learning for Tool-Calling Chatbots

A learning project for practicing reinforcement learning (RL) with a focus on evaluating and improving tool-calling chatbots across multiple agent frameworks.

## 🎯 Project Goals

This project provides a complete scaffold for:
1. **Building tool-calling agents** - Agents that can use tools/functions to accomplish tasks
   - Supports multiple frameworks: OpenAI (Responses API), Pydantic AI, LangGraph (extensible)
   - Shared tool registry across all agents
   - Automatic tool execution and result handling
   - Built-in multi-turn conversation support
2. **Evaluating agent performance** - Metrics and frameworks to measure how well agents perform
   - Compare different frameworks side-by-side
   - Multi-agent evaluation and ranking
3. **Training with Reinforcement Learning** - Using RL to improve agent decision-making over time
   - Framework-agnostic RL training
   - Compare different agents and strategies

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- An OpenAI API key

### Installation

1. **Install dependencies**:
```bash
# Using uv (recommended - faster)
uv sync

# Or using pip
pip install -e .
```

2. **Set up environment variables**:
```bash
# Copy the sample environment file
cp .env.sample .env

# Edit .env and add your API key
# OPENAI_API_KEY=your_key_here
```

Or export directly:
```bash
export OPENAI_API_KEY=your_key_here
```

The `.env` file is gitignored for security. See `.env.sample` for available configuration options.

### Try It Out

#### 1. Test the Chatbot

Run the chatbot interactively:
```bash
uv run chatbot
```

Try asking:
- "What is 15 * 23?"
- "What's the weather in New York?"
- "Calculate 100 divided by 4"

#### 2. Run Evaluation

Evaluate the chatbot on test cases:
```bash
uv run evaluate
```

This will:
- Run the agent on sample test cases
- Calculate metrics (task success, tool efficiency, response quality)
- Save results to `data/evaluation_results.json`

#### 3. Start RL Training

Begin training with reinforcement learning:
```bash
uv run train
```

This will:
- Collect episodes of interactions
- Compute rewards based on performance
- Save training checkpoints to `checkpoints/`

#### Alternative: Use Full Module Paths

```bash
uv run python -m rl_chatbot.agents.openai.agent
uv run python -m rl_chatbot.evaluation.evaluator
uv run python -m rl_chatbot.rl.trainer
```

## 🌐 API Server

The project includes a FastAPI server that provides REST API and WebSocket endpoints for building UIs and integrations.

### Start the Server

```bash
uv run server
```

The server starts at `http://localhost:8000`. View interactive API docs at `http://localhost:8000/docs`.

### Configuration

Configure via environment variables in `.env`:

```bash
# Database location (default: ./data/rl_chatbot.db)
DATABASE_URL=sqlite+aiosqlite:///./data/rl_chatbot.db

# Server settings
HOST=0.0.0.0
PORT=8000
DEBUG=false
```

### API Endpoints

| Category | Endpoint | Description |
|----------|----------|-------------|
| **Health** | `GET /api/v1/health` | Health check |
| **Agents** | `GET /api/v1/agents` | List agents |
| | `POST /api/v1/agents` | Create agent |
| | `GET /api/v1/agents/{id}` | Get agent |
| | `PATCH /api/v1/agents/{id}` | Update agent |
| | `DELETE /api/v1/agents/{id}` | Delete agent |
| **Chat** | `POST /api/v1/chat` | Send message, get response |
| | `WS /api/v1/chat/ws/{agent_id}` | Real-time chat WebSocket |
| **Conversations** | `GET /api/v1/conversations` | List conversations |
| | `GET /api/v1/conversations/{id}` | Get conversation with messages |
| | `DELETE /api/v1/conversations/{id}` | Delete conversation |
| **Test Cases** | `GET /api/v1/test-cases` | List test cases |
| | `POST /api/v1/test-cases` | Create test case |
| | `POST /api/v1/test-cases/bulk` | Bulk import |
| **Evaluations** | `GET /api/v1/evaluations` | List evaluation runs |
| | `POST /api/v1/evaluations` | Start evaluation (background) |
| | `GET /api/v1/evaluations/{id}` | Get run with results |
| | `WS /api/v1/evaluations/ws/{id}` | Progress WebSocket |
| **Training** | `GET /api/v1/training` | List training runs |
| | `POST /api/v1/training` | Start training (background) |
| | `GET /api/v1/training/{id}` | Get run with episodes |
| | `POST /api/v1/training/{id}/stop` | Stop training |
| | `WS /api/v1/training/ws/{id}` | Progress WebSocket |
| **Tools** | `GET /api/v1/tools` | List available tools |

### Example: Chat via API

```bash
# Create an agent
curl -X POST http://localhost:8000/api/v1/agents/ \
  -H "Content-Type: application/json" \
  -d '{"name": "My Agent", "model": "gpt-4o", "temperature": 0.7}'

# Chat with the agent (use the agent_id from above)
curl -X POST http://localhost:8000/api/v1/chat/ \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "AGENT_UUID", "message": "What is 15 * 23?"}'
```

### WebSocket Support

Connect to WebSocket endpoints for real-time updates:

- **Chat**: `ws://localhost:8000/api/v1/chat/ws/{agent_id}` - Send/receive messages in real-time
- **Evaluation Progress**: `ws://localhost:8000/api/v1/evaluations/ws/{run_id}` - Monitor evaluation progress
- **Training Progress**: `ws://localhost:8000/api/v1/training/ws/{run_id}` - Monitor training progress

### Database

The server uses SQLite for persistence with the following tables:
- `agents` - Agent configurations
- `conversations` / `messages` / `tool_calls` - Chat history
- `test_cases` - Evaluation test cases
- `evaluation_runs` / `evaluation_results` - Evaluation data
- `training_runs` / `training_episodes` - Training data

Database migrations are managed with Alembic:

```bash
# Run migrations (auto-runs on server start)
uv run alembic upgrade head

# Create new migration after model changes
uv run alembic revision --autogenerate -m "description"
```

## 🏗️ Project Structure

```
rl-chatbot/
├── src/rl_chatbot/
│   ├── agents/            # Agent implementations for different frameworks
│   │   ├── base.py       # BaseAgent interface - all agents must implement
│   │   ├── openai/       # OpenAI Responses API implementation
│   │   ├── pydantic_ai/  # Pydantic AI (placeholder)
│   │   └── langgraph/    # LangGraph (placeholder)
│   ├── tools/            # Modular tool system (shared across all agents)
│   │   ├── base.py       # Tool and ToolRegistry classes
│   │   ├── calculate.py  # Math calculation tool
│   │   ├── search.py     # Web search tool (mock)
│   │   ├── weather.py    # Weather tool (mock)
│   │   └── README.md     # Guide for adding new tools
│   ├── factory.py        # AgentFactory and AgentPool
│   ├── evaluation/       # Evaluation framework
│   │   ├── evaluator.py  # Single & multi-agent evaluators
│   │   └── metrics.py    # Performance metrics
│   ├── rl/               # Reinforcement learning components
│   │   ├── trainer.py    # Single & multi-agent RL trainers
│   │   └── reward.py     # Reward function design
│   └── server/           # FastAPI server for UI/integrations
│       ├── main.py       # FastAPI app entry point
│       ├── config.py     # Server configuration
│       ├── database.py   # Async SQLite database
│       ├── models/       # SQLModel database models
│       ├── schemas/      # Pydantic request/response schemas
│       ├── routers/      # API route handlers
│       ├── services/     # Business logic layer
│       └── websocket/    # WebSocket handlers
├── migrations/           # Alembic database migrations
├── examples/             # Example scripts
├── docs/                 # Documentation
├── tests/                # Unit tests
├── data/                 # Database and evaluation data
└── checkpoints/          # Model checkpoints
```

## 📚 Learning Path

### Phase 1: Understanding the Components
- **Agents** (`src/rl_chatbot/agents/`): Study how different frameworks make decisions and call tools
- **Tools** (`src/rl_chatbot/tools/`): Understand the modular tool system (see `tools/README.md`)
- **Evaluation** (`src/rl_chatbot/evaluation/`): Learn how to measure agent performance
- **RL Training** (`src/rl_chatbot/rl/`): Understand the reinforcement learning loop

### Phase 2: Experimentation
- Add new tools/functions (automatically available to all agents)
- Create custom evaluation metrics
- Compare different agent frameworks
- Experiment with different RL algorithms (PPO, DQN, etc.)

### Phase 3: Improvement
- Analyze evaluation results across frameworks
- Tune hyperparameters
- Iterate on the RL training process
- Select best-performing agent framework for your use case

## 🔧 Key Concepts

### Multi-Framework Architecture

The project uses an abstract `BaseAgent` interface that allows different agent frameworks to work seamlessly:

```python
from rl_chatbot import AgentFactory, AgentType

factory = AgentFactory()

# Create agents from different frameworks
openai_agent = factory.create_agent(agent_type=AgentType.OPENAI)
# pydantic_agent = factory.create_agent(agent_type=AgentType.PYDANTIC_AI)
# langgraph_agent = factory.create_agent(agent_type=AgentType.LANGGRAPH)

# All agents share the same tools and can be evaluated identically
```

### Tool Calling

Agents can call tools (functions) to accomplish tasks. Default tools:
- `calculate`: Perform mathematical calculations
- `search`: Search for information (mock)
- `get_weather`: Get weather information (mock)

All agents access the same `ToolRegistry`, ensuring consistent tool availability.

### Evaluation Metrics

- **Task Success Rate**: Percentage of tasks completed successfully
- **Tool Usage Efficiency**: How effectively tools are used
- **Response Quality**: Quality of agent responses
- **Reward**: Composite score used for RL training

### Multi-Agent Comparison

```python
from rl_chatbot import AgentPool, MultiAgentEvaluator

# Create pool with multiple agents
pool = AgentPool(initial_size=3)

# Evaluate and compare
evaluator = MultiAgentEvaluator(pool)
comparison = evaluator.compare_agents(test_cases)

print(f"Best agent: {comparison['best_overall']}")
```

### Reinforcement Learning

- **State**: Current conversation context and available tools
- **Action**: Which tool to call (or respond directly)
- **Reward**: Score based on task completion and quality
- **Policy**: The agent's decision-making strategy (updated via RL)

## 🧪 Experiments to Try

1. **Add new tools**: Extend agent capabilities (see `src/rl_chatbot/tools/README.md` for guide)
2. **Add new agent framework**: Follow guide in `docs/ADDING_NEW_AGENT_FRAMEWORK.md`
3. **Modify reward function**: Change what the RL algorithm optimizes for
4. **Compare frameworks**: Evaluate OpenAI vs Pydantic AI vs LangGraph
5. **Human feedback**: Incorporate human preferences into training
6. **Multi-turn conversations**: Handle complex, multi-step tasks

## 📝 Development

### Run Tests
```bash
pytest tests/
```

### Format Code
```bash
black src/ tests/
ruff check src/ tests/
```

### Adding a New Agent Framework

See `docs/ADDING_NEW_AGENT_FRAMEWORK.md` for a complete guide. Quick overview:

1. Create implementation in `src/rl_chatbot/agents/your_framework/`
2. Inherit from `BaseAgent` and implement required methods
3. Register in `AgentFactory`
4. Your agent automatically works with evaluation and RL training!

## 🐛 Troubleshooting

**Issue**: `ModuleNotFoundError`
- **Solution**: Install the package: `pip install -e .` or `uv sync`

**Issue**: `OpenAI API key not found`
- **Solution**: Set the `OPENAI_API_KEY` environment variable or create a `.env` file

**Issue**: Import errors
- **Solution**: Make sure you're running from the project root and the package is installed in editable mode

**Issue**: Temperature not supported error
- **Solution**: Some models only support default temperature (1.0). The code handles this automatically for OpenAI agents.

## 📖 Learning Resources

- [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/) - Comprehensive RL textbook
- [RLHF (Reinforcement Learning from Human Feedback)](https://huggingface.co/blog/rlhf) - Modern RL techniques
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling) - Tool calling with OpenAI
- [Pydantic AI](https://ai.pydantic.dev/) - Agent framework with Pydantic models
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Build stateful agent workflows

## 🤝 Contributing

This is a research/learning project. Feel free to experiment and modify! Contributions welcome:

- Add new agent framework implementations
- Improve evaluation metrics
- Implement full RL algorithms (currently scaffolded)
- Add more tools
- Create example notebooks

## 📄 License

MIT

---

**Happy learning! 🚀**

For detailed implementation notes and architecture details, see `CLAUDE.md`.
