"""Chatbot agent using the OpenAI Chat Completions API with function calling."""

import os
import json
import uuid
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from .tools import ToolRegistry

load_dotenv()


class ChatbotAgent:
    """A chatbot that can call tools using the OpenAI Chat Completions API."""

    def __init__(
        self,
        tool_registry: Optional[ToolRegistry] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        conversation_id: Optional[str] = None,
    ):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o")
        temp_env = os.getenv("OPENAI_TEMPERATURE")
        self.temperature = (
            temperature
            if temperature is not None
            else float(temp_env) if temp_env and temp_env.replace(".", "", 1).isdigit() else 1.0
        )
        self.conversation_id = conversation_id or str(uuid.uuid4())
        self.tool_registry = tool_registry or self._create_default_registry()

        # Conversation history
        self.messages: List[Dict[str, Any]] = []

        # Track tool calls for evaluation
        self.last_tool_calls: List[Dict[str, Any]] = []

    def _create_default_registry(self) -> ToolRegistry:
        from .tools import create_default_tool_registry
        return create_default_tool_registry()

    def reset(self, clear_conversation_id: bool = False):
        """Reset the agent's conversation state."""
        self.messages = []
        self.last_tool_calls = []
        if clear_conversation_id:
            self.conversation_id = str(uuid.uuid4())

    def get_conversation_id(self) -> str:
        """Get the current conversation ID."""
        return self.conversation_id

    def get_last_tool_calls(self) -> List[Dict[str, Any]]:
        """Get tool calls from the last interaction."""
        return self.last_tool_calls

    def chat(self, user_message: str, max_iterations: int = 6) -> str:
        """
        Run a chat turn with tool calling support.

        Args:
            user_message: The user's input message
            max_iterations: Maximum number of API calls to make (to handle tool calling loops)

        Returns:
            The chatbot's response text
        """
        # Add user message to conversation
        self.messages.append({"role": "user", "content": user_message})

        # Reset tool call tracking
        self.last_tool_calls = []

        # Prepare tools for function calling
        tools = self._prepare_tools()

        # Iterative loop to handle function calling
        for iteration in range(max_iterations):
            # Make API call
            # Note: Some models don't support custom temperature, so only pass if it's 1.0
            call_params = {
                "model": self.model,
                "messages": self.messages,
                "tools": tools,
            }
            # Only add temperature if it's not the default value
            if self.temperature != 1.0:
                call_params["temperature"] = self.temperature

            response = self.client.chat.completions.create(**call_params)

            message = response.choices[0].message

            # Add assistant's response to conversation
            self.messages.append(message.model_dump())

            # Check if there are tool calls
            if message.tool_calls:
                # Track tool calls for evaluation
                for tool_call in message.tool_calls:
                    self.last_tool_calls.append({
                        "id": tool_call.id,
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    })

                # Execute each tool call
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name

                    # Parse arguments
                    try:
                        function_args = json.loads(tool_call.function.arguments)
                    except json.JSONDecodeError:
                        function_args = {}

                    # Execute the tool
                    function_response = self._run_tool(function_name, function_args)

                    # Add tool response to conversation
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        "content": function_response,
                    })

                # Continue loop to get final response
                continue

            # No tool calls - return the assistant's message
            if message.content:
                return message.content
            else:
                return "No response from model."

        # Max iterations reached
        return self.messages[-1].get("content", "Maximum iterations reached without response.")

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        """Prepare tools in the format expected by OpenAI API."""
        tools = []
        for schema in self.tool_registry.get_tool_schemas():
            tools.append(schema)
        return tools

    def _run_tool(self, name: str, args: Dict[str, Any]) -> str:
        """Execute a tool and return its result."""
        tool = self.tool_registry.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            result = tool.execute(**args)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"


def main():
    """Interactive chatbot session."""
    agent = ChatbotAgent()
    print("Chatbot ready! Type 'quit' to exit.\n")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["quit", "exit", "q"]:
            break
        response = agent.chat(user_input)
        print(f"Bot: {response}\n")


if __name__ == "__main__":
    main()
