"""Web search tool"""

from .base import Tool


def search(query: str) -> str:
    """Search for information (mock implementation)"""
    # In a real implementation, this would call a search API
    return f"Search results for: {query} (mock - implement with real search API)"


def create_search_tool() -> Tool:
    """Create the search tool"""
    return Tool(
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
    )
