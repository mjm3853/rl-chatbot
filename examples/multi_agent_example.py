"""
Example demonstrating multi-agent capabilities with shared tools.

This example shows how to:
1. Create multiple agents with shared tool registries
2. Evaluate and compare multiple agents
3. Train multiple agents and find the best performer
"""

from src.rl_chatbot.factory import AgentFactory, AgentPool
from src.rl_chatbot.evaluation.evaluator import MultiAgentEvaluator, create_sample_test_cases
from src.rl_chatbot.rl.trainer import MultiAgentRLTrainer


def example_agent_pool():
    """Example: Creating and using an agent pool with shared tools."""
    print("="*60)
    print("Example 1: Agent Pool with Shared Tools")
    print("="*60)

    # Create agent pool with 3 agents sharing the same tools
    pool = AgentPool(initial_size=3, model="gpt-4o")

    print(f"\nCreated pool with {pool.size()} agents")
    print(f"Agent IDs: {pool.list_agents()}")

    # Get shared tool registry
    tool_registry = pool.get_tool_registry()
    print(f"\nShared tools: {[tool.name for tool in tool_registry.list_tools()]}")

    # Use different agents
    agent_ids = pool.list_agents()

    print("\n" + "-"*60)
    print("Testing agents with same input:")
    print("-"*60)

    test_message = "What is 25 * 4?"
    for agent_id in agent_ids[:2]:  # Test first 2 agents
        agent = pool.get_agent(agent_id)
        response = agent.chat(test_message)
        print(f"\nAgent {agent_id[:8]}...")
        print(f"Response: {response}")
        print(f"Tools used: {[tc['name'] for tc in agent.get_last_tool_calls()]}")

    # Reset all agents
    pool.reset_all()
    print("\n✓ All agents reset")


def example_agent_factory():
    """Example: Using AgentFactory to create agents with custom configurations."""
    print("\n" + "="*60)
    print("Example 2: Agent Factory with Custom Configurations")
    print("="*60)

    # Create factory with shared tools
    factory = AgentFactory()

    # Create agents with different configurations
    agents = {
        "default": factory.create_agent(),
        "high_temp": factory.create_agent(temperature=1.5),
        "low_temp": factory.create_agent(temperature=0.5),
    }

    print(f"\nCreated {len(agents)} agents with different configurations")
    print("Configurations:")
    for name, agent in agents.items():
        print(f"  - {name}: temp={agent.temperature}, model={agent.model}")

    # All agents share the same tool registry
    print("\n✓ All agents share the same tool registry")


def example_multi_agent_evaluation():
    """Example: Evaluating and comparing multiple agents."""
    print("\n" + "="*60)
    print("Example 3: Multi-Agent Evaluation and Comparison")
    print("="*60)

    # Create agent pool
    pool = AgentPool(initial_size=2, model="gpt-4o")

    # Create evaluator
    evaluator = MultiAgentEvaluator(pool)

    # Get test cases
    test_cases = create_sample_test_cases()

    print(f"\nEvaluating {pool.size()} agents on {len(test_cases)} test cases...")

    # Compare agents
    comparison = evaluator.compare_agents(test_cases, verbose=True)

    # Print comparison results
    print("\n" + "-"*60)
    print("Comparison Results:")
    print("-"*60)

    print("\nAgent Metrics:")
    for agent_id, metrics in comparison["agent_metrics"].items():
        print(f"\nAgent {agent_id[:8]}...")
        for metric, value in metrics.items():
            print(f"  {metric}: {value:.3f}")

    print("\n" + "-"*60)
    print("Rankings by Metric:")
    print("-"*60)
    for metric, ranking in comparison["rankings"].items():
        print(f"\n{metric}:")
        for i, agent_id in enumerate(ranking, 1):
            score = comparison["agent_metrics"][agent_id][metric]
            print(f"  {i}. Agent {agent_id[:8]}... (score: {score:.3f})")

    print(f"\n✓ Best overall agent: {comparison['best_overall'][:8]}...")


def example_multi_agent_training():
    """Example: Training multiple agents and selecting the best."""
    print("\n" + "="*60)
    print("Example 4: Multi-Agent Training")
    print("="*60)

    # Create agent pool with different configurations
    factory = AgentFactory()
    agents = [
        factory.create_agent(model="gpt-4o", temperature=1.0),
        factory.create_agent(model="gpt-4o", temperature=1.0),
    ]

    # Create multi-agent trainer
    trainer = MultiAgentRLTrainer(agents)

    # Get test cases
    test_cases = create_sample_test_cases()

    print(f"\nTraining {len(agents)} agents for 3 episodes...")

    # Train all agents
    trainer.train_all_agents(test_cases, num_episodes=3, verbose=True)

    # Compare trained agents
    print("\n" + "-"*60)
    print("Comparing trained agents...")
    print("-"*60)

    comparison = trainer.compare_agents(test_cases, verbose=False)

    print("\nFinal Rankings (by reward):")
    for i, agent_id in enumerate(comparison["rankings"]["reward"], 1):
        score = comparison["agent_metrics"][agent_id]["reward"]
        print(f"  {i}. Agent {agent_id[:8]}... (reward: {score:.3f})")

    # Get best agent
    best_id, best_agent = trainer.get_best_agent(test_cases, metric="reward")
    print(f"\n✓ Best agent: {best_id[:8]}... (reward: {comparison['agent_metrics'][best_id]['reward']:.3f})")

    # Save checkpoints
    print("\nSaving checkpoints...")
    trainer.save_all_checkpoints(episode=3)


def main():
    """Run all examples."""
    print("\n" + "="*60)
    print("Multi-Agent System Examples")
    print("="*60)

    try:
        # Example 1: Agent Pool
        example_agent_pool()

        # Example 2: Agent Factory
        example_agent_factory()

        # Example 3: Multi-Agent Evaluation
        example_multi_agent_evaluation()

        # Example 4: Multi-Agent Training (commented out as it takes longer)
        # example_multi_agent_training()

        print("\n" + "="*60)
        print("✓ All examples completed successfully!")
        print("="*60)

    except Exception as e:
        print(f"\n✗ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
