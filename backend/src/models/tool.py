"""Tool call and result models."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field


@dataclass
class ToolCall:
    """Represents a tool call from the model."""

    id: str
    name: str
    arguments: str


@dataclass
class ToolResult:
    """Represents the result of a tool execution."""

    tool_call_id: str
    name: str
    content: str
    is_error: bool = False


@dataclass
class StreamResult:
    """Result of processing a stream response."""

    content: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    has_content: bool = False

    @property
    def has_tool_calls(self) -> bool:
        """Check if there are pending tool calls."""
        return len(self.tool_calls) > 0
