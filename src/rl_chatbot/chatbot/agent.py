"""Chatbot agent with tool calling capabilities"""

import os
import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

from .tools import ToolRegistry

load_dotenv()


class ChatbotAgent:
    """A chatbot that can call tools to accomplish tasks using OpenAI Responses API"""
    
    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: str = "gpt-4o",
        temperature: float = 0.7,
        use_responses_api: bool = True,
        conversation_id: Optional[str] = None,
    ):
        """
        Initialize the chatbot agent
        
        Args:
            tool_registry: Registry of available tools. If None, creates default registry.
            model: LLM model to use (gpt-4o recommended for Responses API)
            temperature: Temperature for LLM generation
            use_responses_api: Whether to use the Responses API (True) or Chat Completions API (False)
            conversation_id: Optional conversation ID for stateful conversations in Responses API
        """
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.temperature = temperature
        self.use_responses_api = use_responses_api
        self.conversation_id = conversation_id
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
        if self.use_responses_api:
            return self._chat_with_responses_api(user_message, max_tool_calls)
        else:
            return self._chat_with_completions_api(user_message, max_tool_calls)
    
    def _chat_with_responses_api(self, user_message: str, max_tool_calls: int = 5) -> str:
        """Chat using the Responses API"""
        # Get tool schemas - Responses API uses the same format as Chat Completions
        tools = self.tool_registry.get_tool_schemas()
        
        # Prepare request parameters
        request_params = {
            "model": self.model,
            "input": user_message,
            "temperature": self.temperature,
        }
        
        if tools:
            request_params["tools"] = tools
        
        if self.conversation_id:
            request_params["conversation_id"] = self.conversation_id
        
        # Call Responses API
        try:
            response = self.client.responses.create(**request_params)
        except Exception as e:
            # Fallback to completions API if Responses API fails
            print(f"Warning: Responses API failed ({e}), falling back to Completions API")
            return self._chat_with_completions_api(user_message, max_tool_calls)
        
        # Update conversation_id if provided in response
        if hasattr(response, 'conversation_id') and response.conversation_id:
            self.conversation_id = response.conversation_id
        
        # Get the output text - Responses API provides output_text directly
        output_text = ""
        if hasattr(response, 'output_text'):
            output_text = response.output_text
        elif hasattr(response, 'output'):
            output_text = response.output
        else:
            # Fallback: try to extract from response object
            output_text = str(response)
        
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
                    tool_name = tool_call.get('function', {}).get('name', '')
                    tool_args = tool_call.get('function', {}).get('arguments', {})
                else:
                    # Assume it's an object with attributes
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
            
            # Make a follow-up call with tool results if needed
            if tool_results and max_tool_calls > 0:
                # For Responses API, tool results are typically handled automatically
                # But we can make a follow-up call if needed
                follow_up_message = f"{user_message}\n\nTool results: {', '.join(str(r) for r in tool_results)}"
                return self._chat_with_responses_api(follow_up_message, max_tool_calls - 1)
        
        return output_text
    
    def _chat_with_completions_api(self, user_message: str, max_tool_calls: int = 5) -> str:
        """Chat using the Chat Completions API (fallback)"""
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Process with potential tool calls
        tool_calls_made = 0
        while tool_calls_made < max_tool_calls:
            # Prepare messages for API call - filter out empty tool_calls
            messages = []
            for msg in self.conversation_history:
                msg_copy = msg.copy()
                # Remove tool_calls if it's empty or None
                if "tool_calls" in msg_copy and not msg_copy["tool_calls"]:
                    msg_copy.pop("tool_calls", None)
                messages.append(msg_copy)
            
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
            
            # Build assistant message - only include tool_calls if not empty
            assistant_msg = {
                "role": "assistant",
                "content": message.content,
            }
            if message.tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments
                        }
                    }
                    for tc in message.tool_calls
                ]
            
            # Add assistant message to history
            self.conversation_history.append(assistant_msg)
            
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
        # Filter out empty tool_calls from messages
        messages = []
        for msg in self.conversation_history:
            msg_copy = msg.copy()
            # Remove tool_calls if it's empty or None
            if "tool_calls" in msg_copy and not msg_copy["tool_calls"]:
                msg_copy.pop("tool_calls", None)
            messages.append(msg_copy)
        
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
    
    def reset(self, clear_conversation_id: bool = False):
        """Reset conversation history and optionally clear conversation ID"""
        self.conversation_history = []
        if clear_conversation_id:
            self.conversation_id = None
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history"""
        return self.conversation_history.copy()
    
    def get_conversation_id(self) -> Optional[str]:
        """Get the current conversation ID (for Responses API)"""
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

