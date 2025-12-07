# RL Chatbot: Reinforcement Learning for Tool-Calling Chatbots

A learning project for practicing reinforcement learning (RL) with a focus on evaluating and improving tool-calling chatbots.

## 🎯 Project Goals

This project provides a complete scaffold for:
1. **Building a tool-calling chatbot** - A chatbot that can use tools/functions to accomplish tasks
2. **Evaluating chatbot performance** - Metrics and frameworks to measure how well the chatbot performs
3. **Training with Reinforcement Learning** - Using RL to improve the chatbot's decision-making over time

## 📚 Learning Path

### Phase 1: Understanding the Components
- **Chatbot (`src/rl_chatbot/chatbot/`)**: Study how the chatbot makes decisions and calls tools
- **Evaluation (`src/rl_chatbot/evaluation/`)**: Learn how to measure chatbot performance
- **RL Training (`src/rl_chatbot/rl/`)**: Understand the reinforcement learning loop

### Phase 2: Experimentation
- Modify the chatbot's behavior
- Add new tools/functions
- Create custom evaluation metrics
- Experiment with different RL algorithms (PPO, DQN, etc.)

### Phase 3: Improvement
- Analyze evaluation results
- Tune hyperparameters
- Iterate on the RL training process

## 🏗️ Project Structure

```
rl-chatbot/
├── src/rl_chatbot/
│   ├── chatbot/          # Chatbot implementation with tool calling
│   │   ├── __init__.py
│   │   ├── agent.py      # Main chatbot agent
│   │   └── tools.py      # Available tools/functions
│   ├── evaluation/       # Evaluation framework
│   │   ├── __init__.py
│   │   ├── metrics.py    # Performance metrics
│   │   └── evaluator.py  # Evaluation runner
│   └── rl/               # Reinforcement learning components
│       ├── __init__.py
│       ├── trainer.py    # RL training loop
│       └── reward.py     # Reward function design
├── tests/                # Unit tests
├── data/                 # Training and evaluation data
├── checkpoints/          # Model checkpoints
├── pyproject.toml        # Dependencies
└── README.md
```

## 🚀 Getting Started

### Installation

1. Install dependencies:
```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

2. Set up environment variables:
```bash
export OPENAI_API_KEY=your_key_here  # If using OpenAI
# Or configure other LLM providers
```

### Basic Usage

1. **Run the chatbot**:
```bash
python -m rl_chatbot.chatbot.agent
```

2. **Evaluate the chatbot**:
```bash
python -m rl_chatbot.evaluation.evaluator
```

3. **Train with RL**:
```bash
python -m rl_chatbot.rl.trainer
```

## 🔧 Key Concepts

### Tool Calling
The chatbot can call tools (functions) to accomplish tasks. Examples:
- `calculate`: Perform mathematical calculations
- `search`: Search for information
- `get_weather`: Get weather information

### Evaluation Metrics
- **Task Success Rate**: Percentage of tasks completed successfully
- **Tool Usage Efficiency**: How effectively tools are used
- **Response Quality**: Quality of chatbot responses
- **Reward**: Composite score used for RL training

### Reinforcement Learning
- **State**: Current conversation context and available tools
- **Action**: Which tool to call (or respond directly)
- **Reward**: Score based on task completion and quality
- **Policy**: The chatbot's decision-making strategy (updated via RL)

## 📖 Learning Resources

- [Reinforcement Learning: An Introduction](http://incompleteideas.net/book/)
- [RLHF (Reinforcement Learning from Human Feedback)](https://huggingface.co/blog/rlhf)
- [OpenAI Function Calling](https://platform.openai.com/docs/guides/function-calling)

## 🧪 Experiments to Try

1. **Add new tools**: Extend the chatbot's capabilities
2. **Modify reward function**: Change what the RL agent optimizes for
3. **Compare RL algorithms**: Try PPO, DQN, A2C, etc.
4. **Human feedback**: Incorporate human preferences into training
5. **Multi-turn conversations**: Handle complex, multi-step tasks

## 📝 Development

Run tests:
```bash
pytest tests/
```

Format code:
```bash
black src/ tests/
ruff check src/ tests/
```

## 🤝 Contributing

This is a learning project. Feel free to experiment and modify!

## 📄 License

MIT

