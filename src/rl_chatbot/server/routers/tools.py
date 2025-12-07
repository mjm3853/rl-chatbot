"""Tools endpoint."""

from typing import List, Any

from fastapi import APIRouter
from pydantic import BaseModel

from rl_chatbot.tools import create_default_tool_registry

router = APIRouter()


class ToolSchema(BaseModel):
    """Schema for a tool."""

    name: str
    description: str
    parameters: dict[str, Any]


@router.get("", response_model=List[ToolSchema])
async def list_tools():
    """List all available tools."""
    registry = create_default_tool_registry()
    tools = registry.list_tools()
    return [
        ToolSchema(
            name=tool.name,
            description=tool.description,
            parameters=tool.parameters,
        )
        for tool in tools
    ]
