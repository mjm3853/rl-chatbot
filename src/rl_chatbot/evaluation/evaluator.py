"""Evaluator for chatbot performance"""

from typing import List, Dict, Any, Optional
from tqdm import tqdm
import json
import numpy as np

from ..chatbot.agent import ChatbotAgent
from .metrics import Metrics, MetricCalculator


class Evaluator:
    """Evaluates chatbot performance on test cases"""
    
    def __init__(self, agent: ChatbotAgent):
        """
        Initialize evaluator
        
        Args:
            agent: The chatbot agent to evaluate
        """
        self.agent = agent
        self.calculator = MetricCalculator()
    
    def evaluate_single(
        self,
        user_input: str,
        expected_output: Optional[str] = None,
        expected_tools: Optional[List[str]] = None,
        task_type: str = "exact_match"
    ) -> Metrics:
        """
        Evaluate chatbot on a single test case
        
        Args:
            user_input: User's input message
            expected_output: Expected output (optional)
            expected_tools: Tools that should be called (optional)
            task_type: Type of task matching
        
        Returns:
            Metrics object with evaluation results
        """
        # Reset agent for clean evaluation
        self.agent.reset(clear_conversation_id=True)
        
        # Get response
        response = self.agent.chat(user_input)

        # Get tool calls from the agent
        tool_calls = self.agent.get_last_tool_calls()
        
        # Calculate metrics
        task_success = 0.0
        if expected_output:
            task_success = self.calculator.calculate_task_success(
                expected_output, response, task_type
            )
        
        tool_usage_efficiency = 1.0
        if expected_tools:
            tool_usage_efficiency = self.calculator.calculate_tool_usage_efficiency(
                tool_calls, expected_tools
            )
        elif tool_calls:
            # If tools were used but none expected, penalize
            tool_usage_efficiency = max(0.0, 1.0 - len(tool_calls) * 0.1)
        
        response_quality = self.calculator.calculate_response_quality(response)
        
        reward = self.calculator.calculate_reward(
            task_success, tool_usage_efficiency, response_quality
        )
        
        return Metrics(
            task_success=task_success,
            tool_usage_efficiency=tool_usage_efficiency,
            response_quality=response_quality,
            reward=reward
        )
    
    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]],
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate chatbot on a batch of test cases
        
        Args:
            test_cases: List of test case dictionaries with keys:
                - "user_input": User message
                - "expected_output": Expected response (optional)
                - "expected_tools": Expected tools to call (optional)
                - "task_type": Type of matching (optional)
            verbose: Whether to show progress
        
        Returns:
            Dictionary with aggregate metrics and per-case results
        """
        results = []
        metrics_list = []
        
        iterator = tqdm(test_cases) if verbose else test_cases
        
        for test_case in iterator:
            metrics = self.evaluate_single(
                user_input=test_case["user_input"],
                expected_output=test_case.get("expected_output"),
                expected_tools=test_case.get("expected_tools"),
                task_type=test_case.get("task_type", "exact_match")
            )
            
            results.append({
                "test_case": test_case,
                "metrics": metrics.to_dict()
            })
            metrics_list.append(metrics)
        
        # Calculate aggregate metrics
        avg_metrics = Metrics(
            task_success=np.mean([m.task_success for m in metrics_list]),
            tool_usage_efficiency=np.mean([m.tool_usage_efficiency for m in metrics_list]),
            response_quality=np.mean([m.response_quality for m in metrics_list]),
            reward=np.mean([m.reward for m in metrics_list])
        )
        
        return {
            "aggregate_metrics": avg_metrics.to_dict(),
            "individual_results": results,
            "num_test_cases": len(test_cases)
        }
    
    def evaluate_from_file(
        self,
        filepath: str,
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate chatbot using test cases from a JSON file
        
        Args:
            filepath: Path to JSON file with test cases
            verbose: Whether to show progress
        
        Returns:
            Dictionary with evaluation results
        """
        with open(filepath, 'r') as f:
            test_cases = json.load(f)
        
        return self.evaluate_batch(test_cases, verbose=verbose)


def create_sample_test_cases() -> List[Dict[str, Any]]:
    """Create sample test cases for evaluation"""
    return [
        {
            "user_input": "What is 15 * 23?",
            "expected_output": "345",
            "expected_tools": ["calculate"],
            "task_type": "exact_match"
        },
        {
            "user_input": "Calculate 100 divided by 4",
            "expected_output": "25",
            "expected_tools": ["calculate"],
            "task_type": "exact_match"
        },
        {
            "user_input": "What's the weather in New York?",
            "expected_tools": ["get_weather"],
            "task_type": "contains"
        },
        {
            "user_input": "Hello, how are you?",
            "expected_tools": [],  # No tools needed for greeting
            "task_type": "contains"
        }
    ]


def main():
    """Example evaluation"""
    from ..chatbot.agent import ChatbotAgent
    
    # Create agent
    agent = ChatbotAgent()
    
    # Create evaluator
    evaluator = Evaluator(agent)
    
    # Create test cases
    test_cases = create_sample_test_cases()
    
    # Run evaluation
    print("Running evaluation...")
    results = evaluator.evaluate_batch(test_cases)
    
    # Print results
    print("\n" + "="*50)
    print("Evaluation Results")
    print("="*50)
    print(f"Number of test cases: {results['num_test_cases']}")
    print("\nAggregate Metrics:")
    for metric, value in results['aggregate_metrics'].items():
        print(f"  {metric}: {value:.3f}")
    
    # Save results
    output_file = "data/evaluation_results.json"
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    print(f"\nResults saved to {output_file}")


if __name__ == "__main__":
    main()

