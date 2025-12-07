"""Chatbot agent with tool calling capabilities"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from .tools import ToolRegistry

load_dotenv()


class ChatbotAgent:
    """A chatbot that can call tools to accomplish tasks"""
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
    ):
        """
        Initialize the chatbot agent
        
        Args:
            tool_registry: Registry of available tools. If None, creates default registry.
            model: LLM model to use
            temperature: Temperature for LLM generation
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.tool_registry = tool_registry or self._create_default_registry()
        self.conversation_history: List[Dict[str, Any]] = []
    
    def _create_default_registry(self) -> ToolRegistry:
        """Create default tool registry"""
        from .tools import create_default_tool_registry
        return create_default_tool_registry()
    
    def chat(self, user_message: str, max_tool_calls: int = 5) -> str:
        """
        Process a user message and return a response
        
        Args:
            user_message: The user's message
            max_tool_calls: Maximum number of tool calls in one turn
            
        Returns:
            The chatbot's response
        """
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Process with potential tool calls
        tool_calls_made = 0
        while tool_calls_made < max_tool_calls:
            # Prepare messages for API call
            messages = self.conversation_history.copy()
            
            # Get tool schemas for function calling
            tools = self.tool_registry.get_tool_schemas()
            
            # Call LLM
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=tools if tools else None,
                temperature=self.temperature,
            )
            
            message = response.choices[0].message
            
            # Add assistant message to history
            self.conversation_history.append({
                "role": "assistant",
                "content": message.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in (message.tool_calls or [])
                ]
            })
            
            # If no tool calls, we're done
            if not message.tool_calls:
                return message.content or ""
            
            # Execute tool calls
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)  # Parse JSON string safely
                
                # Get and execute tool
                tool = self.tool_registry.get(tool_name)
                if tool:
                    try:
                        tool_result = tool.execute(**tool_args)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found"
                
                # Add tool result to history
                self.conversation_history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": str(tool_result)
                })
                
                tool_calls_made += 1
        
        # If we hit max tool calls, get final response
        messages = self.conversation_history.copy()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
        )
        
        final_message = response.choices[0].message.content or ""
        self.conversation_history.append({
            "role": "assistant",
            "content": final_message
        })
        
        return final_message
    
    def reset(self):
        """Reset conversation history"""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history.copy()


def main():
    """Example usage of the chatbot"""
    agent = ChatbotAgent()
    
    print("Chatbot ready! Type 'quit' to exit.\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        response = agent.chat(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()

