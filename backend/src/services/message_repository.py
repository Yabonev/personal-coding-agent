"""Repository for managing chat messages."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..models.message import Message
from ..models.message import MessageRole

if TYPE_CHECKING:
    from ..models.tool import ToolCall
    from ..models.tool import ToolResult


class MessageRepository:
    """Repository for managing chat messages."""

    def __init__(self, system_prompt: str) -> None:
        """Initialize message repository with system prompt."""
        self._messages: list[Message] = [
            Message(role=MessageRole.SYSTEM, content=system_prompt)
        ]

    def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation."""
        self._messages.append(Message(role=MessageRole.USER, content=content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the conversation."""
        self._messages.append(Message(role=MessageRole.ASSISTANT, content=content))

    def add_assistant_tool_calls(self, tool_calls: list[ToolCall]) -> None:
        """Add an assistant message with tool calls."""
        self._messages.append(
            Message(role=MessageRole.ASSISTANT, content="", tool_calls=tool_calls)
        )

    def add_tool_result(self, result: ToolResult) -> None:
        """Add a tool result message."""
        self._messages.append(
            Message(
                role=MessageRole.TOOL,
                content=result.content,
                tool_call_id=result.tool_call_id,
                name=result.name,
            )
        )

    def get_messages_for_api(self) -> list[dict[str, object]]:
        """Get all messages in API format."""
        return [msg.to_dict() for msg in self._messages]

    def get_all_messages(self) -> list[Message]:
        """Get all messages."""
        return self._messages.copy()

    def clear(self) -> None:
        """Clear all messages except system message."""
        if self._messages:
            system_msg = self._messages[0]
            self._messages = [system_msg]
