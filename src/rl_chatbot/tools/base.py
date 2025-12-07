"""Base classes for tool definitions"""

from typing import Any, Dict, List, Callable
from pydantic import BaseModel, Field


class Tool(BaseModel):
    """Represents a tool that the chatbot can call"""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of what the tool does")
    parameters: Dict[str, Any] = Field(
        default_factory=dict,
        description="JSON schema for tool parameters"
    )
    function: Callable = Field(..., description="The actual function to call")

    def execute(self, **kwargs) -> Any:
        """Execute the tool with given parameters"""
        return self.function(**kwargs)


class ToolRegistry:
    """Registry for managing available tools"""

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool):
        """Register a tool"""
        self._tools[tool.name] = tool

    def get(self, name: str) -> Tool:
        """Get a tool by name"""
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """List all registered tools"""
        return list(self._tools.values())

    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get JSON schemas for all tools (for LLM function calling)"""
        schemas = []
        for tool in self._tools.values():
            schemas.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters
                }
            })
        return schemas
