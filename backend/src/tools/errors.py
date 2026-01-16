"""Tool error types."""

from __future__ import annotations


class ToolError(Exception):
    """Tool error with actionable message.

    Use for all tool failures. Message should be clear and directive.
    """

    def __init__(self, message: str, *, retryable: bool = False) -> None:
        """Create a tool error.

        Args:
            message: Actionable error message for the model
            retryable: Whether the operation might succeed if retried
        """
        super().__init__(message)
        self.message = message
        self.retryable = retryable
