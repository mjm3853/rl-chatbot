"""Weather information tool"""

from .base import Tool


def get_weather(location: str) -> str:
    """Get weather information for a location (mock implementation)"""
    # In a real implementation, this would call a weather API
    return f"Weather in {location}: Sunny, 72°F (mock - implement with real weather API)"


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
