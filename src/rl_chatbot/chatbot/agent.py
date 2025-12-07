"""Chatbot agent with tool calling capabilities"""

import os
import json
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv

from .tools import ToolRegistry

load_dotenv()


class ChatbotAgent:
    """A chatbot that can call tools to accomplish tasks using OpenAI Responses API"""
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        conversation_id: Optional[str] = None,
    ):
        """
        Initialize the chatbot agent
        
        Args:
            tool_registry: Registry of available tools. If None, creates default registry.
            model: LLM model to use. If None, reads from OPENAI_MODEL env var or defaults to "gpt-4o"
            temperature: Temperature for LLM generation. If None, reads from OPENAI_TEMPERATURE env var or defaults to 0.7
            conversation_id: Optional conversation ID for stateful conversations
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Get model from parameter, env var, or default
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        
        # Get temperature from parameter, env var, or default
        temp_str = os.getenv("OPENAI_TEMPERATURE")
        if temperature is not None:
            self.temperature = temperature
        elif temp_str is not None:
            try:
                self.temperature = float(temp_str)
            except ValueError:
                self.temperature = 0.7
        else:
            self.temperature = 0.7
        
        self.conversation_id = conversation_id
        self.tool_registry = tool_registry or self._create_default_registry()
    
    def _create_default_registry(self) -> ToolRegistry:
        """Create default tool registry"""
        from .tools import create_default_tool_registry
        return create_default_tool_registry()
    
    def chat(self, user_message: str, max_tool_calls: int = 5) -> str:
        """
        Process a user message and return a response using the Responses API
        
        Args:
            user_message: The user's message
            max_tool_calls: Maximum number of tool calls in one turn
            
        Returns:
            The chatbot's response
        """
        # Get tool schemas and convert to Responses API format
        tool_schemas = self.tool_registry.get_tool_schemas()
        tools = []
        for schema in tool_schemas:
            # Responses API expects tools with type, name, description, and parameters
            # Extract the function definition from the schema
            func_def = schema.get("function", {})
            tools.append({
                "type": "function",  # Required by Responses API
                "name": func_def.get("name"),
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {})
            })
        
        # Prepare request parameters
        # Note: Responses API doesn't support temperature parameter
        request_params = {
            "model": self.model,
            "input": user_message,
        }
        
        if tools:
            request_params["tools"] = tools
        
        if self.conversation_id:
            request_params["conversation_id"] = self.conversation_id
        
        # Call Responses API
        response = self.client.responses.create(**request_params)
        
        # Update conversation_id if provided in response
        if hasattr(response, 'conversation_id') and response.conversation_id:
            self.conversation_id = response.conversation_id
        
        # Get the output text
        output_text = ""
        if hasattr(response, 'output_text'):
            output_text = response.output_text or ""
        elif hasattr(response, 'output'):
            output_text = response.output or ""
        else:
            output_text = str(response) if response else ""
        
        # Handle tool calls if present
        tool_calls = None
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = response.tool_calls
        elif hasattr(response, 'tool_use') and response.tool_use:
            tool_calls = response.tool_use
        
        if tool_calls:
            # Execute tool calls
            tool_results = []
            for tool_call in tool_calls:
                # Handle different response formats
                if isinstance(tool_call, dict):
                    tool_name = tool_call.get('name', '') or tool_call.get('function', {}).get('name', '')
                    tool_args = tool_call.get('arguments', {}) or tool_call.get('function', {}).get('arguments', {})
                else:
                    # Assume it's an object with attributes
                    tool_name = getattr(tool_call, 'name', '')
                    tool_args = getattr(tool_call, 'arguments', {})
                    if not tool_name:
                        func = getattr(tool_call, 'function', None)
                        if func:
                            tool_name = getattr(func, 'name', '')
                            tool_args = getattr(func, 'arguments', {})
                        else:
                            continue
                
                if isinstance(tool_args, str):
                    try:
                        tool_args = json.loads(tool_args)
                    except json.JSONDecodeError:
                        tool_args = {}
                
                # Get and execute tool
                tool = self.tool_registry.get(tool_name)
                if tool:
                    try:
                        tool_result = tool.execute(**tool_args)
                    except Exception as e:
                        tool_result = f"Error executing tool: {str(e)}"
                else:
                    tool_result = f"Error: Tool '{tool_name}' not found"
                
                tool_results.append(tool_result)
            
            # Make a follow-up call to get the final response with tool results
            if tool_results and max_tool_calls > 0:
                # For Responses API, when tools are called, we need to make another call
                # to get the final response. The API handles tool execution via conversation_id.
                # If output_text is empty, make a follow-up call with a continuation message
                if not output_text.strip():
                    # Make a follow-up call to continue the conversation
                    # The Responses API will use the conversation_id to continue
                    # We pass a simple continuation message
                    return self.chat("Please provide the final answer based on the tool results.", max_tool_calls - 1)
                else:
                    # We have output text, return it
                    return output_text
        
        return output_text
    
    def reset(self, clear_conversation_id: bool = False):
        """Reset conversation state and optionally clear conversation ID"""
        if clear_conversation_id:
            self.conversation_id = None
    
    def get_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID"""
        return self.conversation_id


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

