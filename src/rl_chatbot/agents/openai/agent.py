"""OpenAI-based chatbot agent implementation using Responses API."""

import os
import json
import uuid
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from ..base import BaseAgent, AgentCapabilities
from ...tools import ToolRegistry

load_dotenv()


class OpenAIAgent(BaseAgent, AgentCapabilities):
    """A chatbot agent using the OpenAI Responses API with function calling."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        conversation_id: Optional[str] = None,
    ):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self._model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        temp_env = os.getenv("OPENAI_TEMPERATURE")
        self._temperature = (
            temperature
            if temperature is not None
            else float(temp_env) if temp_env and temp_env.replace(".", "", 1).isdigit() else 1.0
        )
        self._conversation_id = conversation_id or str(uuid.uuid4())
        self._tool_registry = tool_registry or self._create_default_registry()

        # Context for multi-turn conversations
        self._context: List[Dict[str, Any]] = []

        # Track tool calls for evaluation
        self._last_tool_calls: List[Dict[str, Any]] = []

        # Store last response ID for chaining
        self._last_response_id: Optional[str] = None

    def _create_default_registry(self) -> ToolRegistry:
        from ...tools import create_default_tool_registry
        return create_default_tool_registry()

    @property
    def model(self) -> str:
        """Get the model name."""
        return self._model

    @property
    def temperature(self) -> float:
        """Get the temperature parameter."""
        return self._temperature

    @property
    def tool_registry(self) -> ToolRegistry:
        """Get the tool registry (for backward compatibility)."""
        return self._tool_registry

    def reset(self, clear_conversation_id: bool = False):
        """Reset the agent's conversation state."""
        self._context = []
        self._last_tool_calls = []
        self._last_response_id = None
        if clear_conversation_id:
            self._conversation_id = str(uuid.uuid4())

    def get_conversation_id(self) -> str:
        """Get the current conversation ID."""
        return self._conversation_id

    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """Get tool calls from the last interaction."""
        return self._last_tool_calls

    def supports_function_calling(self) -> bool:
        """OpenAI supports function calling."""
        return True

    def get_supported_tools(self) -> List[str]:
        """Get list of available tool names."""
        return [tool.name for tool in self._tool_registry.list_tools()]

    def chat(self, user_message: str, max_iterations: int = 6, **kwargs) -> str:
        """
        Run a chat turn with tool calling support using Responses API.

        Args:
            user_message: The user's input message
            max_iterations: Maximum number of API calls (for multi-turn tool calling)
            **kwargs: Additional OpenAI-specific parameters (ignored for now)

        Returns:
            The agent's response text
        """
        # Reset tool call tracking
        self._last_tool_calls = []

        # Prepare tools for function calling
        tools = self._prepare_tools()

        # Build input - either append to context or start fresh
        if self._context:
            # Multi-turn conversation: append new user message
            self._context.append({"role": "user", "content": user_message})
            input_data = self._context
        else:
            # First turn: just the user message
            input_data = user_message

        # Build request parameters
        request_params = {
            "model": self._model,
            "input": input_data,
            "tools": tools,
            "store": True,  # Enable storage for multi-turn
        }

        # Add temperature if not default
        if self._temperature != 1.0:
            request_params["temperature"] = self._temperature

        # Make the Responses API call
        response = self.client.responses.create(**request_params)

        # Store response ID for potential chaining
        self._last_response_id = response.id

        # Extract output text directly if available
        if hasattr(response, 'output_text') and response.output_text:
            # Update context with response output
            self._context.extend(response.output)
            return response.output_text

        # Otherwise, process output items
        output_items = response.output if hasattr(response, 'output') else []

        # Track tool calls from output
        for item in output_items:
            item_dict = item if isinstance(item, dict) else self._item_to_dict(item)
            if item_dict.get('type') == 'function_call':
                self._last_tool_calls.append({
                    'id': item_dict.get('call_id') or item_dict.get('id'),
                    'name': item_dict.get('name'),
                    'arguments': item_dict.get('arguments'),
                })

        # If there are tool calls, execute them and make follow-up requests
        if self._last_tool_calls:
            # Append response output to context
            self._context.extend(output_items)

            # Execute all tool calls
            for tool_call in self._last_tool_calls:
                call_id = tool_call['id']
                function_name = tool_call['name']

                # Parse arguments
                try:
                    args_str = tool_call['arguments']
                    function_args = json.loads(args_str) if isinstance(args_str, str) else args_str
                except (json.JSONDecodeError, TypeError):
                    function_args = {}

                # Execute the tool
                function_response = self._run_tool(function_name, function_args)

                # Append function output to context
                self._context.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": function_response,
                })

            # Make follow-up request with tool outputs
            follow_up_params = {
                "model": self._model,
                "input": self._context,
                "store": True,
            }
            if self._temperature != 1.0:
                follow_up_params["temperature"] = self._temperature

            follow_up_response = self.client.responses.create(**follow_up_params)

            # Update context with follow-up output
            self._context.extend(follow_up_response.output)

            # Return the final text
            if hasattr(follow_up_response, 'output_text') and follow_up_response.output_text:
                return follow_up_response.output_text

            # Extract text from follow-up output
            return self._extract_text_from_output(follow_up_response.output)

        # No tool calls - extract and return text from output
        text = self._extract_text_from_output(output_items)

        # Update context with response
        self._context.extend(output_items)

        return text or "No response from model."

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """Prepare tools in the format expected by Responses API."""
        tools = []
        for schema in self._tool_registry.get_tool_schemas():
            # Responses API uses internally-tagged format
            func_def = schema.get("function", {})
            tools.append({
                "type": "function",
                "name": func_def.get("name"),
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {}),
            })
        return tools

    def _item_to_dict(self, item: Any) -> Dict[str, Any]:
        """Convert an item object to dictionary."""
        if isinstance(item, dict):
            return item

        item_dict = {}
        for attr in ['type', 'role', 'content', 'name', 'arguments', 'call_id', 'id', 'status']:
            if hasattr(item, attr):
                item_dict[attr] = getattr(item, attr)
        return item_dict

    def _extract_text_from_output(self, output_items: List) -> str:
        """Extract text content from output items."""
        for item in output_items:
            item_dict = item if isinstance(item, dict) else self._item_to_dict(item)

            # Skip reasoning items
            if item_dict.get('type') == 'reasoning':
                continue

            # Look for message items
            if item_dict.get('type') == 'message':
                content = item_dict.get('content', [])

                # Content can be a list of content items
                if isinstance(content, list):
                    for content_item in content:
                        if isinstance(content_item, dict):
                            # Look for text or output_text
                            text = content_item.get('text') or content_item.get('output_text')
                            if text and isinstance(text, str) and text.strip():
                                return text.strip()
                        elif isinstance(content_item, str) and content_item.strip():
                            return content_item.strip()

                # Content might be a string directly
                elif isinstance(content, str) and content.strip():
                    return content.strip()

        return ""

    def _run_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return its result."""
        tool = self._tool_registry.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            result = tool.execute(**args)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"


def main():
    """Interactive chatbot session."""
    agent = OpenAIAgent()
    print("OpenAI Chatbot (Responses API) ready! Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        response = agent.chat(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
