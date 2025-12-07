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
    
    def chat(self, user_message: str, max_iterations: int = 10) -> str:
        """
        Process a user message and return a response using the Responses API
        
        The Responses API handles tool execution automatically via conversation_id.
        We iterate until we get a final text response.
        
        Args:
            user_message: The user's message
            max_iterations: Maximum number of API calls to make (prevents infinite loops)
            
        Returns:
            The chatbot's response text
        """
        # Convert tool schemas to Responses API format
        tools = self._prepare_tools()
        
        # Prepare request parameters
        request_params = {
            "model": self.model,
            "input": user_message,
        }
        
        if tools:
            request_params["tools"] = tools
        
        if self.conversation_id:
            request_params["conversation_id"] = self.conversation_id
        
        # Iterate until we get a final response
        # The Responses API may return tool calls that need execution
        output_text = ""
        for iteration in range(max_iterations):
            # Call Responses API
            response = self.client.responses.create(**request_params)
            
            # Update conversation_id for stateful conversations
            if hasattr(response, 'conversation_id') and response.conversation_id:
                self.conversation_id = response.conversation_id
                request_params["conversation_id"] = self.conversation_id
            
            # Get output text from response
            output_text = self._extract_output_text(response)
            
            # Check for tool calls that need execution
            tool_calls = self._extract_tool_calls(response)
            
            if tool_calls:
                # Execute tools locally
                tool_results = self._execute_tools(tool_calls)
                
                # If we have output text already, return it (tools might have been called but we got text too)
                if output_text.strip():
                    return output_text
                
                # If we have tool results but no output text, make a follow-up call
                # The Responses API will use conversation_id to continue the conversation
                if tool_results:
                    # For Responses API, we need to make another call to get the final response
                    # The API should handle the conversation context via conversation_id
                    # Use empty input to continue - the API should process tool results automatically
                    request_params["input"] = ""
                    # Don't include tools in follow-up calls to avoid loops
                    if "tools" in request_params:
                        del request_params["tools"]
                    continue
                else:
                    # No tool results, something went wrong
                    return "Error: Tools were called but no results were returned."
            else:
                # No tool calls, return the output text
                if output_text.strip():
                    return output_text
                # If no output and no tool calls after first iteration, we're done
                if iteration > 0:
                    return ""
        
        # If we've exhausted iterations, return whatever we have
        return output_text or ""
    
    def _prepare_tools(self) -> list:
        """Convert tool schemas to Responses API format"""
        tool_schemas = self.tool_registry.get_tool_schemas()
        tools = []
        for schema in tool_schemas:
            func_def = schema.get("function", {})
            tools.append({
                "type": "function",
                "name": func_def.get("name"),
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {})
            })
        return tools
    
    def _extract_output_text(self, response) -> str:
        """Extract output text from Responses API response"""
        # Standard Responses API response has output_text attribute
        if hasattr(response, 'output_text') and response.output_text:
            return str(response.output_text).strip()
        
        # Check output attribute
        if hasattr(response, 'output'):
            output = response.output
            if isinstance(output, str):
                return output.strip()
            elif isinstance(output, list):
                # Extract text from message items in the output list
                for item in output:
                    if isinstance(item, dict):
                        # Check for message type
                        if item.get('type') == 'message':
                            content = item.get('content', '')
                            if content:
                                return str(content).strip()
                        # Also check for text content directly
                        if 'text' in item:
                            return str(item['text']).strip()
                        if 'content' in item:
                            return str(item['content']).strip()
                    elif isinstance(item, str):
                        return item.strip()
        
        # Check for text attribute directly
        if hasattr(response, 'text') and response.text:
            return str(response.text).strip()
        
        return ""
    
    def _extract_tool_calls(self, response) -> list:
        """Extract tool calls from Responses API response"""
        tool_calls = []
        
        # Check standard attributes
        if hasattr(response, 'tool_calls') and response.tool_calls:
            tool_calls = response.tool_calls if isinstance(response.tool_calls, list) else [response.tool_calls]
        elif hasattr(response, 'tool_use') and response.tool_use:
            tool_calls = response.tool_use if isinstance(response.tool_use, list) else [response.tool_use]
        
        # Check output list for tool calls
        if not tool_calls and hasattr(response, 'output') and isinstance(response.output, list):
            for item in response.output:
                if isinstance(item, dict) and item.get('type') in ['function_call', 'tool_call', 'function']:
                    tool_calls.append(item)
        
        return tool_calls
    
    def _execute_tools(self, tool_calls: list) -> list:
        """Execute tool calls and return results"""
        tool_results = []
        
        for tool_call in tool_calls:
            # Extract tool name and arguments
            if isinstance(tool_call, dict):
                tool_name = tool_call.get('name', '') or tool_call.get('function', {}).get('name', '')
                tool_args = tool_call.get('arguments', {}) or tool_call.get('function', {}).get('arguments', {})
            else:
                # Object with attributes
                tool_name = getattr(tool_call, 'name', '')
                tool_args = getattr(tool_call, 'arguments', {})
                if not tool_name:
                    func = getattr(tool_call, 'function', None)
                    if func:
                        tool_name = getattr(func, 'name', '')
                        tool_args = getattr(func, 'arguments', {})
            
            if not tool_name:
                continue
            
            # Parse arguments if string
            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}
            
            # Execute tool
            tool = self.tool_registry.get(tool_name)
            if tool:
                try:
                    result = tool.execute(**tool_args)
                    tool_results.append(result)
                except Exception as e:
                    tool_results.append(f"Error: {str(e)}")
            else:
                tool_results.append(f"Error: Tool '{tool_name}' not found")
        
        return tool_results
    
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

