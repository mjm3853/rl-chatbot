"""Chatbot agent using the OpenAI Responses API with proper function_call_output loop."""

import os
import json
from typing import Optional, List, Dict, Any
from openai import OpenAI
from dotenv import load_dotenv

from .tools import ToolRegistry

load_dotenv()


class ChatbotAgent:
    """A chatbot that can call tools using the OpenAI Responses API."""

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
            else float(temp_env) if temp_env and temp_env.replace(".", "", 1).isdigit() else 0.7
        )
        self.conversation_id = conversation_id
        self.tool_registry = tool_registry or self._create_default_registry()

    def _create_default_registry(self) -> ToolRegistry:
        from .tools import create_default_tool_registry
        return create_default_tool_registry()

    def chat(self, user_message: str, max_iterations: int = 6) -> str:
        """Run a turn with Responses API and local tool execution."""
        tools = self._prepare_tools()
        messages: List[Dict[str, Any]] = [{"role": "user", "content": user_message}]
        last_text = ""

        for iteration in range(max_iterations):
            response = self.client.responses.create(
                model=self.model,
                input=messages,
                tools=tools if iteration == 0 else None,  # send tools only first call
            )

            # Direct text if provided
            ot = getattr(response, "output_text", None)
            if isinstance(ot, str) and ot.strip():
                return ot.strip()

            output_items = self._get_output_items(response)

            text = self._extract_message_text(output_items)
            if text:
                last_text = text

            tool_calls = self._extract_function_calls(output_items)
            if not tool_calls:
                return last_text or "No response from model."

            call_outputs: List[Dict[str, Any]] = []
            for call in tool_calls:
                name = call.get("name", "")
                call_id = call.get("call_id") or call.get("tool_call_id") or call.get("id")
                args_raw = call.get("arguments", "{}")
                try:
                    args = json.loads(args_raw) if isinstance(args_raw, str) else args_raw
                except Exception:
                    args = {}
                result = self._run_tool(name, args)
                call_outputs.append(
                    {
                        "type": "function_call_output",
                        "call_id": call_id,
                        "output": result,
                    }
                )

            messages.extend(output_items)
            messages.extend(call_outputs)
            tools = None  # only send tools on first iteration

        return last_text or "No response from model."

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for schema in self.tool_registry.get_tool_schemas():
            func_def = schema.get("function", {})
            tools.append(
                {
                    "type": "function",
                    "name": func_def.get("name"),
                    "description": func_def.get("description", ""),
                    "parameters": func_def.get("parameters", {}),
                }
            )
        return tools

    def _get_output_items(self, response) -> List[Dict[str, Any]]:
        items: List[Dict[str, Any]] = []
        if getattr(response, "output", None):
            items = [self._normalize_item(item) for item in response.output]
        elif getattr(response, "items", None):
            items = [self._normalize_item(item) for item in response.items]
        # Filter out reasoning items to avoid summary requirements when re-sending
        return [item for item in items if item.get("type") != "reasoning"]

    def _normalize_item(self, item: Any) -> Dict[str, Any]:
        if isinstance(item, dict):
            return item
        d: Dict[str, Any] = {}
        for attr in ["type", "role", "content", "name", "arguments", "call_id", "id", "tool_call_id"]:
            if hasattr(item, attr):
                d[attr] = getattr(item, attr)
        return d

    def _extract_message_text(self, items: List[Dict[str, Any]]) -> str:
        for item in items:
            if item.get("type") == "message" or item.get("role") == "assistant":
                content = item.get("content", "")
                if isinstance(content, str) and content.strip():
                    return content.strip()
                if isinstance(content, list):
                    for c in content:
                        if isinstance(c, str) and c.strip():
                            return c.strip()
                        if isinstance(c, dict) and "text" in c and str(c["text"]).strip():
                            return str(c["text"]).strip()
        return ""

    def _extract_function_calls(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        calls = []
        for item in items:
            if item.get("type") in {"function_call", "tool_call", "function"}:
                calls.append(item)
        return calls

    def _run_tool(self, name: str, args: Dict[str, Any]) -> str:
        tool = self.tool_registry.get(name)
        if not tool:
            return f"Error: Tool '{name}' not found"
        try:
            result = tool.execute(**args)
            return str(result)
        except Exception as e:
            return f"Error executing tool '{name}': {str(e)}"


def main():
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
