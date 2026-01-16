"""Tool registry - exports all available tools."""

from __future__ import annotations

from pydantic import BaseModel

from .base import BaseTool
from .base import EmptyArgs
from .current_time import CurrentTimeArgs
from .current_time import CurrentTimeTool
from .errors import ToolError
from .random_date import RandomDateArgs
from .random_date import RandomDateTool
from .read_file import ReadFileArgs
from .read_file import ReadFileTool

# Type alias for any tool (used in registry)
AnyTool = BaseTool[BaseModel]

# Registry of all available tools
# Note: Generic variance means we need type: ignore here.
# At runtime this is fine - all tools implement the same interface.
TOOLS: list[AnyTool] = [
    CurrentTimeTool(),  # type: ignore[list-item]
    RandomDateTool(),  # type: ignore[list-item]
    ReadFileTool(),  # type: ignore[list-item]
]


def get_tool_schemas() -> list[dict[str, object]]:
    """Get all tool schemas for the API."""
    return [tool.schema for tool in TOOLS]


def get_tool_registry() -> dict[str, AnyTool]:
    """Get tool name -> tool instance mapping."""
    return {tool.name: tool for tool in TOOLS}


__all__ = [
    "TOOLS",
    "AnyTool",
    "BaseTool",
    "CurrentTimeArgs",
    "CurrentTimeTool",
    "EmptyArgs",
    "RandomDateArgs",
    "RandomDateTool",
    "ReadFileArgs",
    "ReadFileTool",
    "ToolError",
    "get_tool_registry",
    "get_tool_schemas",
]
