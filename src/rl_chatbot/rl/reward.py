"""Reward function for RL training"""

from typing import Dict, Any, List, Optional
from ..evaluation.metrics import MetricCalculator
from ..chatbot.agent import ChatbotAgent


class RewardFunction:
    """Computes rewards for RL training based on chatbot performance"""
    
    def __init__(
        self,
        weights: Optional[Dict[str, float]] = None,
        task_success_weight: float = 0.5,
        tool_efficiency_weight: float = 0.3,
        response_quality_weight: float = 0.2
    ):
        """
        Initialize reward function
        
        Args:
            weights: Custom weights for reward components
            task_success_weight: Weight for task success
            tool_efficiency_weight: Weight for tool usage efficiency
            response_quality_weight: Weight for response quality
        """
        if weights:
            self.weights = weights
        else:
            self.weights = {
                "task_success": task_success_weight,
                "tool_usage_efficiency": tool_efficiency_weight,
                "response_quality": response_quality_weight
            }
        
        self.calculator = MetricCalculator()
    
    def compute_reward(
        self,
        agent: ChatbotAgent,
        user_input: str,
        expected_output: Optional[str] = None,
        expected_tools: Optional[List[str]] = None,
        task_type: str = "exact_match"
    ) -> float:
        """
        Compute reward for a single interaction
        
        Args:
            agent: The chatbot agent
            user_input: User's input
            expected_output: Expected output (if available)
            expected_tools: Expected tools to call (if available)
            task_type: Type of task matching
        
        Returns:
            Reward value (typically between 0.0 and 1.0)
        """
        # Get conversation history to extract tool calls
        history = agent.get_conversation_history()
        
        # Get the final response
        final_response = ""
        tool_calls = []
        for msg in history:
            if msg.get("role") == "assistant":
                if msg.get("content"):
                    final_response = msg["content"]
                if msg.get("tool_calls"):
                    for tc in msg["tool_calls"]:
                        tool_calls.append({
                            "name": tc["function"]["name"],
                            "arguments": tc["function"]["arguments"]
                        })
        
        # Calculate individual metrics
        task_success = 0.0
        if expected_output:
            task_success = self.calculator.calculate_task_success(
                expected_output, final_response, task_type
            )
        elif not expected_output:
            # If no expected output, give partial credit for any response
            task_success = 0.5 if final_response else 0.0
        
        tool_usage_efficiency = 1.0
        if expected_tools:
            tool_usage_efficiency = self.calculator.calculate_tool_usage_efficiency(
                tool_calls, expected_tools
            )
        elif tool_calls:
            # Penalize unnecessary tool usage
            tool_usage_efficiency = max(0.0, 1.0 - len(tool_calls) * 0.1)
        
        response_quality = self.calculator.calculate_response_quality(final_response)
        
        # Compute composite reward
        reward = self.calculator.calculate_reward(
            task_success,
            tool_usage_efficiency,
            response_quality,
            weights=self.weights
        )
        
        return reward
    
    def compute_batch_rewards(
        self,
        agent: ChatbotAgent,
        test_cases: List[Dict[str, Any]]
    ) -> List[float]:
        """
        Compute rewards for a batch of test cases
        
        Args:
            agent: The chatbot agent
            test_cases: List of test case dictionaries
        
        Returns:
            List of reward values
        """
        rewards = []
        for test_case in test_cases:
            agent.reset()
            agent.chat(test_case["user_input"])
            reward = self.compute_reward(
                agent,
                test_case["user_input"],
                expected_output=test_case.get("expected_output"),
                expected_tools=test_case.get("expected_tools"),
                task_type=test_case.get("task_type", "exact_match")
            )
            rewards.append(reward)
        return rewards

