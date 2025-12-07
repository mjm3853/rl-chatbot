"""Chatbot agent using the OpenAI Responses API with local tool execution."""

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

    def chat(self, user_message: str, max_iterations: int = 5) -> str:
        """
        Process a user message using the Responses API.
        Executes tools locally and makes a follow-up call with tool results when needed.
        """
        params: Dict[str, Any] = {"model": self.model, "input": user_message}
        tools = self._prepare_tools()
        if tools:
            params["tools"] = tools
        if self.conversation_id:
            params["conversation_id"] = self.conversation_id

        last_text = ""
        for _ in range(max_iterations):
            response = self.client.responses.create(**params)

            conv_id = getattr(response, "conversation_id", None)
            if conv_id:
                self.conversation_id = conv_id
                params["conversation_id"] = conv_id

            output_text = self._extract_output_text(response)
            if output_text:
                last_text = output_text

            tool_calls = self._extract_tool_calls(response)
            if not tool_calls:
                return output_text or last_text or "No response from model."

            tool_results = self._execute_tools(tool_calls)

            if tool_results:
                # Follow-up call with tool results; remove tools to avoid re-selection
                params.pop("tools", None)
                params["input"] = "Tool results:\n" + "\n".join(f"- {res}" for res in tool_results)
                continue

            return "Tools were requested but no results were produced."

        return last_text or "No response from model."

    def _prepare_tools(self) -> List[Dict[str, Any]]:
        tools = []
        for schema in self.tool_registry.get_tool_schemas():
            func_def = schema.get("function", {})
            tools.append({
                "type": "function",
                "name": func_def.get("name"),
                "description": func_def.get("description", ""),
                "parameters": func_def.get("parameters", {}),
            })
        return tools

    def _extract_output_text(self, response) -> str:
        """Extract text from Responses API response."""
        items = getattr(response, "items", None)
        if items:
            for item in items:
                item_type = getattr(item, "type", None) or (item.get("type") if isinstance(item, dict) else None)
                if item_type == "message":
                    content = getattr(item, "content", None)
                    if content:
                        if isinstance(content, str):
                            return content.strip()
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, str):
                                    return c.strip()
                                if isinstance(c, dict) and "text" in c:
                                    return str(c["text"]).strip()
                    if isinstance(item, dict):
                        content = item.get("content", "")
                        if isinstance(content, str):
                            return content.strip()
                        if isinstance(content, list):
                            for c in content:
                                if isinstance(c, str):
                                    return c.strip()

        output = getattr(response, "output", None)
        if output:
            if isinstance(output, str):
                return output.strip()
            if isinstance(output, list):
                for item in output:
                    if isinstance(item, dict):
                        if item.get("type") == "message":
                            content = item.get("content", "")
                            if isinstance(content, str) and content:
                                return content.strip()
                            if isinstance(content, list):
                                for c in content:
                                    if isinstance(c, str):
                                        return c.strip()
                        if "text" in item:
                            return str(item["text"]).strip()
                        if "content" in item and isinstance(item["content"], str):
                            return item["content"].strip()
                    elif isinstance(item, str):
                        return item.strip()

        output_text = getattr(response, "output_text", None)
        if isinstance(output_text, str):
            return output_text.strip()

        text_attr = getattr(response, "text", None)
        if isinstance(text_attr, str):
            return text_attr.strip()

        return ""

    def _extract_tool_calls(self, response) -> List[Any]:
        tool_calls: List[Any] = []
        tc = getattr(response, "tool_calls", None)
        if tc:
            tool_calls.extend(tc if isinstance(tc, list) else [tc])
        tu = getattr(response, "tool_use", None)
        if tu:
            tool_calls.extend(tu if isinstance(tu, list) else [tu])

        output = getattr(response, "output", None)
        if not tool_calls and isinstance(output, list):
            for item in output:
                if isinstance(item, dict) and item.get("type") in {"function_call", "tool_call", "function"}:
                    tool_calls.append(item)

        return tool_calls

    def _execute_tools(self, tool_calls: List[Any]) -> List[str]:
        results: List[str] = []
        for call in tool_calls:
            if isinstance(call, dict):
                tool_name = call.get("name") or call.get("function", {}).get("name", "")
                tool_args = call.get("arguments") or call.get("function", {}).get("arguments", {})
            else:
                tool_name = getattr(call, "name", "")
                tool_args = getattr(call, "arguments", {})
                if not tool_name:
                    func = getattr(call, "function", None)
                    if func:
                        tool_name = getattr(func, "name", "")
                        tool_args = getattr(func, "arguments", {})
            if not tool_name:
                continue

            if isinstance(tool_args, str):
                try:
                    tool_args = json.loads(tool_args)
                except json.JSONDecodeError:
                    tool_args = {}

            tool = self.tool_registry.get(tool_name)
            if not tool:
                results.append(f"Error: Tool '{tool_name}' not found")
                continue
            try:
                result = tool.execute(**tool_args)
                results.append(str(result))
            except Exception as e:
                results.append(f"Error executing tool '{tool_name}': {str(e)}")
        return results


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
