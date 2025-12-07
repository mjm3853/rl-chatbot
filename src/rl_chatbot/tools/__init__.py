"""Tool registry and default tools for the chatbot"""

from .base import Tool, ToolRegistry
from .calculate import create_calculate_tool
from .search import create_search_tool
from .weather import create_weather_tool


def create_default_tool_registry() -> ToolRegistry:
    """Create a registry with default tools"""
    registry = ToolRegistry()

    # Register all default tools
    registry.register(create_calculate_tool())
    registry.register(create_search_tool())
    registry.register(create_weather_tool())

    return registry


__all__ = [
    "Tool",
    "ToolRegistry",
    "create_default_tool_registry",
    "create_calculate_tool",
    "create_search_tool",
    "create_weather_tool",
]
