# Tools Directory

This directory contains the modular tool system for the RL Chatbot project. Each tool is a self-contained module that can be easily added, modified, or removed.

## Structure

```
tools/
├── base.py           # Base classes (Tool, ToolRegistry)
├── calculate.py      # Mathematical calculation tool
├── search.py         # Web search tool (mock)
├── weather.py        # Weather information tool (mock)
├── __init__.py       # Exports and default registry creation
└── README.md         # This file
```

## How to Add a New Tool

Adding a new tool is simple and requires just 3 steps:

### Step 1: Create a New Tool File

Create a new Python file in this directory (e.g., `my_tool.py`):

```python
"""Description of your tool"""

from .base import Tool


def my_function(param1: str, param2: int) -> str:
    """
    Your tool's function implementation.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        The result as a string
    """
    # Your implementation here
    result = f"Processed {param1} with value {param2}"
    return result


def create_my_tool() -> Tool:
    """Create the my_tool tool"""
    return Tool(
        name="my_tool",
        description="Clear description of what your tool does",
        parameters={
            "type": "object",
            "properties": {
                "param1": {
                    "type": "string",
                    "description": "Description of param1"
                },
                "param2": {
                    "type": "integer",
                    "description": "Description of param2"
                }
            },
            "required": ["param1", "param2"]
        },
        function=my_function
    )
```

### Step 2: Register in `__init__.py`

Update `__init__.py` to import and register your new tool:

```python
from .my_tool import create_my_tool  # Add this import

def create_default_tool_registry() -> ToolRegistry:
    """Create a registry with default tools"""
    registry = ToolRegistry()

    # Register all default tools
    registry.register(create_calculate_tool())
    registry.register(create_search_tool())
    registry.register(create_weather_tool())
    registry.register(create_my_tool())  # Add this line

    return registry
```

Also add to the `__all__` export list if you want to expose the tool creator function:

```python
__all__ = [
    "Tool",
    "ToolRegistry",
    "create_default_tool_registry",
    "create_calculate_tool",
    "create_search_tool",
    "create_weather_tool",
    "create_my_tool",  # Add this line
]
```

### Step 3: That's It!

Your tool is now automatically available to:
- All agent implementations (OpenAI, Pydantic AI, LangGraph, etc.)
- The evaluation framework
- The RL training system

No other code changes needed!

## Testing Your Tool

Create a test in `tests/test_tools.py`:

```python
def test_my_tool():
    """Test my_tool"""
    registry = create_default_tool_registry()
    my_tool = registry.get("my_tool")

    result = my_tool.execute(param1="test", param2=42)
    assert "Processed test with value 42" in result
```

Run tests:

```bash
uv run pytest tests/test_tools.py -v
```

## Tool Parameter Schema

Tools use JSON Schema to define parameters. Here are common patterns:

### String Parameter

```python
"param_name": {
    "type": "string",
    "description": "Description of the parameter"
}
```

### Integer/Number Parameter

```python
"param_name": {
    "type": "integer",  # or "number" for floats
    "description": "Description of the parameter"
}
```

### Boolean Parameter

```python
"param_name": {
    "type": "boolean",
    "description": "Description of the parameter"
}
```

### Array Parameter

```python
"param_name": {
    "type": "array",
    "items": {"type": "string"},
    "description": "Description of the parameter"
}
```

### Optional Parameters

Omit the parameter from the `required` list:

```python
parameters={
    "type": "object",
    "properties": {
        "required_param": {"type": "string"},
        "optional_param": {"type": "string"}
    },
    "required": ["required_param"]  # only required_param is mandatory
}
```

## Best Practices

1. **One Tool Per File**: Keep each tool in its own file for clarity
2. **Clear Descriptions**: Write clear descriptions for the tool and all parameters
3. **Error Handling**: Always handle errors gracefully and return string error messages
4. **Return Strings**: Tools should return strings (the LLM processes text)
5. **Mock vs Real**: Mark mock implementations clearly and note where to add real APIs
6. **Test Your Tool**: Always add tests for new tools

## Example: Real API Integration

Here's an example of integrating a real API:

```python
"""Real weather tool using OpenWeatherMap API"""

import os
import requests
from .base import Tool


def get_weather(location: str) -> str:
    """Get weather information using OpenWeatherMap API"""
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key:
        return "Error: OPENWEATHER_API_KEY not set in environment"

    try:
        url = f"https://api.openweathermap.org/data/2.5/weather"
        params = {"q": location, "appid": api_key, "units": "imperial"}
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()
        temp = data["main"]["temp"]
        description = data["weather"][0]["description"]

        return f"Weather in {location}: {description}, {temp}°F"
    except requests.RequestException as e:
        return f"Error fetching weather: {str(e)}"
    except (KeyError, IndexError) as e:
        return f"Error parsing weather data: {str(e)}"


def create_weather_tool() -> Tool:
    """Create the weather tool"""
    return Tool(
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
    )
```

## Questions?

See the existing tool implementations (`calculate.py`, `search.py`, `weather.py`) for examples, or check the main project documentation.
