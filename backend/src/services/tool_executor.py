"""Service for executing tool calls."""

from __future__ import annotations

import json

from pydantic import ValidationError

from ..models.tool import ToolCall
from ..models.tool import ToolResult
from ..tools import get_tool_registry
from ..tools.errors import ToolError
from ..tracing import SpanKind
from ..tracing import TracingConfig
from ..tracing import span


class ToolExecutor:
    """Executes tool calls and returns results."""

    def __init__(self, tracing_config: TracingConfig | None = None) -> None:
        """Initialize tool executor with available tools."""
        self._tools = get_tool_registry()
        self._tracing_config = tracing_config or TracingConfig()

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call and return the result.

        Args:
            tool_call: The tool call to execute

        Returns:
            ToolResult with the execution result or error
        """
        with span("tool", kind=SpanKind.TOOL) as s:
            s.set(tool_name=tool_call.name, tool_call_id=tool_call.id)
            if self._tracing_config.include_sensitive_data:
                s.set(arguments=tool_call.arguments)

            if tool_call.name not in self._tools:
                available = ", ".join(self._tools.keys())
                result = self._error_result(
                    tool_call,
                    f"Unknown tool '{tool_call.name}'. Available: {available}.",
                )
                s.set(is_error=True, error_type="unknown_tool")
                return result

            tool = self._tools[tool_call.name]

            try:
                raw_arguments = (
                    json.loads(tool_call.arguments) if tool_call.arguments else {}
                )
                parsed_args = tool.parse_arguments(raw_arguments)
                tool_output = tool.execute(parsed_args)

                s.set(is_error=False, result_len=len(tool_output))
                if self._tracing_config.include_sensitive_data:
                    s.set(result=tool_output)
                return ToolResult(
                    tool_call_id=tool_call.id,
                    name=tool_call.name,
                    content=tool_output,
                )

            except json.JSONDecodeError as e:
                s.set(is_error=True, error_type="json_decode")
                return self._error_result(
                    tool_call,
                    f"Invalid JSON in arguments. {e.msg}.",
                )

            except ValidationError as e:
                s.set(is_error=True, error_type="validation")
                return self._error_result(
                    tool_call,
                    self._format_validation_error(e),
                )

            except ToolError as e:
                s.set(is_error=True, error_type="tool_error")
                return self._error_result(tool_call, e.message)

            except Exception as e:
                s.set(is_error=True, error_type=type(e).__name__)
                return self._error_result(
                    tool_call,
                    f"Unexpected error: {type(e).__name__}: {e}",
                )

    def _error_result(self, tool_call: ToolCall, message: str) -> ToolResult:
        """Create an error ToolResult."""
        return ToolResult(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            content=message,
            is_error=True,
        )

    def _format_validation_error(self, e: ValidationError) -> str:
        """Format Pydantic ValidationError as actionable message."""
        errors = e.errors()
        if len(errors) == 1:
            err = errors[0]
            field = ".".join(str(loc) for loc in err["loc"])
            msg_type = err["type"]

            if msg_type == "missing":
                return f"Missing required argument '{field}'."
            if msg_type == "string_type":
                return f"Argument '{field}' must be a string."
            if msg_type == "int_type":
                return f"Argument '{field}' must be an integer."

            return f"Invalid argument '{field}': {err['msg']}."

        fields = [".".join(str(loc) for loc in err["loc"]) for err in errors]
        joined = ", ".join(fields)
        return f"Invalid arguments: {joined}. Check types and required fields."
