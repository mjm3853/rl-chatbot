"""Tool definitions for the chatbot"""

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


# Example tool implementations

def calculate(expression: str) -> str:
    """Calculate a mathematical expression safely"""
    try:
        # Only allow basic math operations for safety
        allowed_chars = set("0123456789+-*/.() ")
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression"
        result = eval(expression)
        return str(result)
    except Exception as e:
        return f"Error: {str(e)}"


def search(query: str) -> str:
    """Search for information (mock implementation)"""
    # In a real implementation, this would call a search API
    return f"Search results for: {query} (mock - implement with real search API)"


def get_weather(location: str) -> str:
    """Get weather information for a location (mock implementation)"""
    # In a real implementation, this would call a weather API
    return f"Weather in {location}: Sunny, 72°F (mock - implement with real weather API)"


def create_default_tool_registry() -> ToolRegistry:
    """Create a registry with default tools"""
    registry = ToolRegistry()
    
    registry.register(Tool(
        name="calculate",
        description="Perform mathematical calculations. Input should be a valid mathematical expression.",
        parameters={
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2', '10 * 5')"
                }
            },
            "required": ["expression"]
        },
        function=calculate
    ))
    
    registry.register(Tool(
        name="search",
        description="Search for information on the web",
        parameters={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query"
                }
            },
            "required": ["query"]
        },
        function=search
    ))
    
    registry.register(Tool(
        name="get_weather",
        description="Get current weather information for a location",
        parameters={
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or location"
                }
            },
            "required": ["location"]
        },
        function=get_weather
    ))
    
    return registry

