# Quick Start Guide

Get up and running with the RL Chatbot project in minutes!

## Prerequisites

- Python 3.10 or higher
- An OpenAI API key (or configure another LLM provider)

## Setup

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

# Edit .env and add your API keys
# The .env file is gitignored for security
```

Or export directly:
```bash
export OPENAI_API_KEY=your_key_here
```

## Try It Out

### 1. Test the Chatbot

Run the chatbot interactively:
```bash
uv run rl_chatbot.chatbot.agent
```

Try asking:
- "What is 15 * 23?"
- "What's the weather in New York?"
- "Calculate 100 divided by 4"

### 2. Run Evaluation

Evaluate the chatbot on test cases:
```bash
uv run rl_chatbot.evaluation.evaluator
```

This will:
- Run the chatbot on sample test cases
- Calculate metrics (task success, tool efficiency, response quality)
- Save results to `data/evaluation_results.json`

### 3. Start RL Training

Begin training the chatbot with reinforcement learning:
```bash
uv run rl_chatbot.rl.trainer
```

This will:
- Collect episodes of interactions
- Compute rewards based on performance
- Save training checkpoints

## Next Steps

1. **Add your own tools**: Edit `src/rl_chatbot/chatbot/tools.py` to add new capabilities
2. **Create test cases**: Add your own test cases to `data/sample_test_cases.json`
3. **Modify rewards**: Adjust the reward function in `src/rl_chatbot/rl/reward.py`
4. **Implement full RL**: Extend `src/rl_chatbot/rl/trainer.py` with a proper RL algorithm (PPO, DQN, etc.)

## Project Structure

- `src/rl_chatbot/chatbot/` - Chatbot with tool calling
- `src/rl_chatbot/evaluation/` - Evaluation framework
- `src/rl_chatbot/rl/` - Reinforcement learning components
- `data/` - Test cases and evaluation data
- `checkpoints/` - Saved model checkpoints

## Troubleshooting

**Issue**: `ModuleNotFoundError`
- **Solution**: Make sure you've installed the package: `pip install -e .`

**Issue**: `OpenAI API key not found`
- **Solution**: Set the `OPENAI_API_KEY` environment variable or create a `.env` file

**Issue**: Import errors
- **Solution**: Make sure you're running from the project root and the package is installed in editable mode

## Learning Resources

Check the main `README.md` for:
- Detailed project structure
- Learning path and concepts
- Experiment ideas
- Additional resources

Happy learning! 🚀

