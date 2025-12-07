"""Mathematical calculation tool"""

from .base import Tool


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


def create_calculate_tool() -> Tool:
    """Create the calculate tool"""
    return Tool(
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
    )
