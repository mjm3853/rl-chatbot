"""Metrics for evaluating chatbot performance"""

from typing import Dict, Any, List
from dataclasses import dataclass
import numpy as np


@dataclass
class Metrics:
    """Container for evaluation metrics"""
    
    task_success: float = 0.0  # 0.0 to 1.0
    tool_usage_efficiency: float = 0.0  # 0.0 to 1.0
    response_quality: float = 0.0  # 0.0 to 1.0
    reward: float = 0.0  # Composite reward for RL
    
    def to_dict(self) -> Dict[str, float]:
        """Convert metrics to dictionary"""
        return {
            "task_success": self.task_success,
            "tool_usage_efficiency": self.tool_usage_efficiency,
            "response_quality": self.response_quality,
            "reward": self.reward,
        }


class MetricCalculator:
    """Calculates various metrics for chatbot evaluation"""
    
    @staticmethod
    def calculate_task_success(
        expected_output: Any,
        actual_output: Any,
        task_type: str = "exact_match"
    ) -> float:
        """
        Calculate task success rate
        
        Args:
            expected_output: Expected result
            actual_output: Actual result from chatbot
            task_type: Type of task matching ("exact_match", "contains", "semantic")
        
        Returns:
            Success score between 0.0 and 1.0
        """
        if task_type == "exact_match":
            return 1.0 if str(expected_output).strip().lower() == str(actual_output).strip().lower() else 0.0
        elif task_type == "contains":
            expected_str = str(expected_output).lower()
            actual_str = str(actual_output).lower()
            return 1.0 if expected_str in actual_str else 0.0
        else:
            # Placeholder for semantic similarity (would use embeddings)
            return 0.5
    
    @staticmethod
    def calculate_tool_usage_efficiency(
        tool_calls: List[Dict[str, Any]],
        expected_tools: List[str],
        unnecessary_calls: int = 0
    ) -> float:
        """
        Calculate how efficiently tools were used
        
        Args:
            tool_calls: List of tool calls made
            expected_tools: Tools that should have been called
            unnecessary_calls: Number of unnecessary tool calls
        
        Returns:
            Efficiency score between 0.0 and 1.0
        """
        if not expected_tools:
            # If no tools expected, efficiency is based on not using unnecessary tools
            return max(0.0, 1.0 - (unnecessary_calls * 0.2))
        
        called_tools = [tc.get("name") for tc in tool_calls]
        correct_calls = sum(1 for tool in expected_tools if tool in called_tools)
        precision = correct_calls / len(called_tools) if called_tools else 0.0
        recall = correct_calls / len(expected_tools) if expected_tools else 1.0
        
        # F1 score as efficiency metric
        if precision + recall == 0:
            return 0.0
        return 2 * (precision * recall) / (precision + recall)
    
    @staticmethod
    def calculate_response_quality(
        response: str,
        min_length: int = 10,
        max_length: int = 500
    ) -> float:
        """
        Calculate response quality based on various factors
        
        Args:
            response: The chatbot's response
            min_length: Minimum expected response length
            max_length: Maximum expected response length
        
        Returns:
            Quality score between 0.0 and 1.0
        """
        if not response:
            return 0.0
        
        length = len(response)
        
        # Length score (optimal range)
        if min_length <= length <= max_length:
            length_score = 1.0
        elif length < min_length:
            length_score = length / min_length
        else:
            length_score = max(0.0, 1.0 - (length - max_length) / max_length)
        
        # Basic quality indicators (can be enhanced)
        has_content = len(response.strip()) > 0
        not_error = "error" not in response.lower()[:50]
        
        quality_score = (length_score * 0.6 + (1.0 if has_content else 0.0) * 0.2 + 
                        (1.0 if not_error else 0.0) * 0.2)
        
        return min(1.0, max(0.0, quality_score))
    
    @staticmethod
    def calculate_reward(
        task_success: float,
        tool_usage_efficiency: float,
        response_quality: float,
        weights: Dict[str, float] = None
    ) -> float:
        """
        Calculate composite reward for RL training
        
        Args:
            task_success: Task success score
            tool_usage_efficiency: Tool usage efficiency score
            response_quality: Response quality score
            weights: Weights for each component (default: equal weights)
        
        Returns:
            Composite reward score
        """
        if weights is None:
            weights = {
                "task_success": 0.5,
                "tool_usage_efficiency": 0.3,
                "response_quality": 0.2
            }
        
        reward = (
            task_success * weights["task_success"] +
            tool_usage_efficiency * weights["tool_usage_efficiency"] +
            response_quality * weights["response_quality"]
        )
        
        return reward

