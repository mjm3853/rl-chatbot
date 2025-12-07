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
# Run interactive chatbot
uv run chatbot
# Or: uv run python -m rl_chatbot.chatbot.agent

# Evaluate chatbot on test cases
uv run evaluate
# Or: uv run python -m rl_chatbot.evaluation.evaluator

# Run RL training
uv run train
# Or: uv run python -m rl_chatbot.rl.trainer
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

1. **Chatbot Agent** (`src/rl_chatbot/chatbot/agent.py`)
   - Uses OpenAI Responses API for tool-calling conversations
   - Implements iterative tool-call loop (max 6 iterations)
   - Key method: `chat(user_message)` - handles full request/response cycle with tool execution
   - Filters reasoning items from response output to avoid API validation errors on follow-up calls

2. **Tool Registry** (`src/rl_chatbot/chatbot/tools.py`)
   - Pydantic-based Tool model with JSON schema definitions
   - ToolRegistry pattern for managing available tools
   - Default tools: `calculate`, `search` (mock), `get_weather` (mock)
   - Tools defined with name, description, parameters schema, and callable function

3. **Evaluation Framework** (`src/rl_chatbot/evaluation/`)
   - **Evaluator**: Runs test cases and computes metrics
   - **MetricCalculator**: Computes task success, tool efficiency, response quality
   - **Metrics dataclass**: Container for evaluation scores
   - Supports batch evaluation and saving results to JSON

4. **RL Training** (`src/rl_chatbot/rl/`)
   - **RLTrainer**: Scaffold for RL training loop (episode collection, checkpointing)
   - **RewardFunction**: Computes composite rewards for training
   - Currently a scaffold - full RL implementation (PPO, DQN) intended for future development

### Key Design Patterns

**OpenAI Responses API Flow**:
- First call: Send tools definitions and initial message
- Response: May contain text, function_calls, or both
- Loop: Execute tools locally, send results back as `function_call_output` items
- Continue until model returns text without tool calls or max iterations reached
- Important: Reasoning items filtered out to prevent validation errors

**Tool Execution Pattern**:
1. Extract function calls from response output items
2. Parse arguments (JSON or dict)
3. Execute tool via ToolRegistry
4. Wrap results in `function_call_output` format with `call_id`
5. Append to messages list and send follow-up request

**Evaluation Pattern**:
- Test cases include: user_input, expected_output, expected_tools, task_type
- Metrics weighted: task_success (0.5), tool_efficiency (0.3), response_quality (0.2)
- Task types: exact_match, contains, semantic (placeholder)

## Environment Configuration

Required in `.env`:
- `OPENAI_API_KEY` - Required for API calls
- `OPENAI_MODEL` - Default: gpt-4o
- `OPENAI_TEMPERATURE` - Default: 0.7
- `WANDB_API_KEY` - Optional for experiment tracking

## Important Implementation Notes

### Agent Limitations
- Responses API tool calls handled internally - tool call history not easily extractable
- For production: modify agent to track tool calls for evaluation
- `agent.reset()` method referenced in evaluator/trainer but not implemented in agent.py - needs addition
- `agent.get_conversation_id()` referenced but not implemented

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
├── chatbot/
│   ├── agent.py          # Main chatbot with Responses API
│   └── tools.py          # Tool definitions and registry
├── evaluation/
│   ├── evaluator.py      # Test case runner
│   └── metrics.py        # Metric calculations
└── rl/
    ├── trainer.py        # RL training scaffold
    └── reward.py         # Reward function
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

### Creating Test Cases
- Format: `{"user_input": str, "expected_output": str, "expected_tools": List[str], "task_type": str}`
- Save as JSON array in `data/` directory
- Use with `evaluator.evaluate_from_file(filepath)`

### Implementing Full RL
1. Create Gymnasium environment wrapper around ChatbotAgent
2. Define observation space (conversation state) and action space (tool selection)
3. Integrate stable-baselines3 algorithm (PPO recommended)
4. Modify trainer to use RL algorithm instead of simple episode collection
