"""RL trainer for chatbot improvement"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import json
from tqdm import tqdm

from ..chatbot.agent import ChatbotAgent
from ..evaluation.evaluator import Evaluator
from .reward import RewardFunction


class RLTrainer:
    """
    Trainer for improving chatbot using reinforcement learning
    
    Note: This is a scaffold. In a full implementation, you would:
    1. Define a proper RL environment (using Gymnasium)
    2. Use an RL algorithm (PPO, DQN, etc.) from stable-baselines3
    3. Train a policy network that decides when to call tools
    4. Update the policy based on rewards
    """
    
    def __init__(
        self,
        agent: ChatbotAgent,
        reward_function: Optional[RewardFunction] = None,
        checkpoint_dir: str = "checkpoints"
    ):
        """
        Initialize RL trainer
        
        Args:
            agent: The chatbot agent to train
            reward_function: Reward function for computing rewards
            checkpoint_dir: Directory to save checkpoints
        """
        self.agent = agent
        self.reward_function = reward_function or RewardFunction()
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)
        
        # Training history
        self.training_history: List[Dict[str, Any]] = []
    
    def collect_episode(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Collect one episode of interactions and rewards
        
        Args:
            test_cases: Test cases to use for this episode
        
        Returns:
            Dictionary with episode data (states, actions, rewards)
        """
        episode_data = {
            "states": [],
            "actions": [],
            "rewards": [],
            "test_cases": test_cases
        }
        
        for test_case in test_cases:
            # Reset agent
            self.agent.reset()
            
            # Get state (conversation context)
            state = {
                "user_input": test_case["user_input"],
                "conversation_id": self.agent.get_conversation_id()
            }
            
            # Agent takes action (chats)
            response = self.agent.chat(test_case["user_input"])

            # Get tool calls from the agent
            actions = self.agent.get_last_tool_calls()
            
            # Compute reward
            reward = self.reward_function.compute_reward(
                self.agent,
                test_case["user_input"],
                expected_output=test_case.get("expected_output"),
                expected_tools=test_case.get("expected_tools"),
                task_type=test_case.get("task_type", "exact_match")
            )
            
            episode_data["states"].append(state)
            episode_data["actions"].append(actions)
            episode_data["rewards"].append(reward)
        
        return episode_data
    
    def train_step(
        self,
        test_cases: List[Dict[str, Any]],
        episode_num: int
    ) -> Dict[str, Any]:
        """
        Perform one training step
        
        Args:
            test_cases: Test cases for this training step
            episode_num: Current episode number
        
        Returns:
            Training step results
        """
        # Collect episode data
        episode_data = self.collect_episode(test_cases)
        
        # Calculate metrics
        avg_reward = sum(episode_data["rewards"]) / len(episode_data["rewards"])
        
        # TODO: In a full implementation, you would:
        # 1. Update the policy network using the collected data
        # 2. Use an RL algorithm (PPO, DQN, etc.) to update parameters
        # 3. Save updated model
        
        step_results = {
            "episode": episode_num,
            "avg_reward": avg_reward,
            "total_reward": sum(episode_data["rewards"]),
            "num_test_cases": len(test_cases)
        }
        
        self.training_history.append(step_results)
        
        return step_results
    
    def train(
        self,
        test_cases: List[Dict[str, Any]],
        num_episodes: int = 10,
        verbose: bool = True
    ):
        """
        Train the chatbot using RL
        
        Args:
            test_cases: Test cases to use for training
            num_episodes: Number of training episodes
            verbose: Whether to show progress
        """
        print(f"Starting RL training for {num_episodes} episodes...")
        
        iterator = tqdm(range(num_episodes)) if verbose else range(num_episodes)
        
        for episode in iterator:
            step_results = self.train_step(test_cases, episode)
            
            if verbose:
                iterator.set_description(
                    f"Episode {episode+1}/{num_episodes} - "
                    f"Avg Reward: {step_results['avg_reward']:.3f}"
                )
        
        print("\nTraining complete!")
        print(f"Final average reward: {self.training_history[-1]['avg_reward']:.3f}")
    
    def evaluate(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Evaluate the trained agent
        
        Args:
            test_cases: Test cases for evaluation
        
        Returns:
            Evaluation results
        """
        evaluator = Evaluator(self.agent)
        return evaluator.evaluate_batch(test_cases, verbose=True)
    
    def save_checkpoint(self, episode: int):
        """Save training checkpoint"""
        checkpoint_path = self.checkpoint_dir / f"checkpoint_episode_{episode}.json"
        
        checkpoint_data = {
            "episode": episode,
            "training_history": self.training_history,
            "agent_config": {
                "model": self.agent.model,
                "temperature": self.agent.temperature
            }
        }
        
        with open(checkpoint_path, 'w') as f:
            json.dump(checkpoint_data, f, indent=2)
        
        print(f"Checkpoint saved to {checkpoint_path}")
    
    def load_checkpoint(self, checkpoint_path: str):
        """Load training checkpoint"""
        with open(checkpoint_path, 'r') as f:
            checkpoint_data = json.load(f)
        
        self.training_history = checkpoint_data.get("training_history", [])
        print(f"Checkpoint loaded from {checkpoint_path}")


def main():
    """Example RL training"""
    from ..chatbot.agent import ChatbotAgent
    from ..evaluation.evaluator import create_sample_test_cases
    
    # Create agent
    agent = ChatbotAgent()
    
    # Create trainer
    trainer = RLTrainer(agent)
    
    # Get test cases
    test_cases = create_sample_test_cases()
    
    # Train
    trainer.train(test_cases, num_episodes=5)
    
    # Evaluate
    print("\nEvaluating trained agent...")
    eval_results = trainer.evaluate(test_cases)
    
    print("\nEvaluation Results:")
    for metric, value in eval_results["aggregate_metrics"].items():
        print(f"  {metric}: {value:.3f}")
    
    # Save checkpoint
    trainer.save_checkpoint(episode=5)


if __name__ == "__main__":
    main()

