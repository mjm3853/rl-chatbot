"""Tests for tool functionality"""

import pytest
from rl_chatbot.chatbot.tools import Tool, ToolRegistry, create_default_tool_registry


def test_tool_creation():
    """Test creating a tool"""
    def test_func(x: int) -> int:
        return x * 2
    
    tool = Tool(
        name="test_tool",
        description="A test tool",
        parameters={"type": "object", "properties": {"x": {"type": "integer"}}},
        function=test_func
    )
    
    assert tool.name == "test_tool"
    assert tool.execute(x=5) == 10


def test_tool_registry():
    """Test tool registry"""
    registry = ToolRegistry()
    
    tool = Tool(
        name="test",
        description="Test",
        parameters={},
        function=lambda: "test"
    )
    
    registry.register(tool)
    assert registry.get("test") == tool
    assert len(registry.list_tools()) == 1


def test_default_tool_registry():
    """Test default tool registry creation"""
    registry = create_default_tool_registry()
    
    tools = registry.list_tools()
    assert len(tools) >= 3  # calculate, search, get_weather
    
    tool_names = [t.name for t in tools]
    assert "calculate" in tool_names
    assert "search" in tool_names
    assert "get_weather" in tool_names


def test_calculate_tool():
    """Test calculate tool"""
    registry = create_default_tool_registry()
    calc_tool = registry.get("calculate")
    
    result = calc_tool.execute(expression="2 + 2")
    assert result == "4"
    
    result = calc_tool.execute(expression="10 * 5")
    assert result == "50"

