"""Processor for handling streaming API responses."""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from dataclasses import field
from typing import TYPE_CHECKING

from ..models.tool import StreamResult
from ..models.tool import ToolCall
from ..services.message_repository import MessageRepository
from ..tracing import TracingConfig
from ..ui.console_output import OutputHandler
from ..ui.loading_spinner import LoadingSpinner

if TYPE_CHECKING:
    from zai.types.chat.chat_completion_chunk import ChatCompletionChunk
    from zai.types.chat.chat_completion_chunk import ChoiceDeltaToolCall


@dataclass
class _ProcessingState:
    """Tracks state during stream processing."""

    first_content: bool = True
    first_reasoning: bool = True
    has_reasoning: bool = False
    content_started: bool = False
    full_content: str = ""
    tool_calls: dict[int, _ToolCallBuilder] = field(default_factory=dict)
    chunk_count: int = 0
    first_chunk_time: float | None = None
    start_time: float = field(default_factory=time.perf_counter)


@dataclass
class _ToolCallBuilder:
    """Accumulates tool call data from streaming chunks."""

    id: str = ""
    name: str = ""
    arguments: str = ""

    def to_tool_call(self) -> ToolCall:
        """Convert to a ToolCall model."""
        return ToolCall(id=self.id, name=self.name, arguments=self.arguments)


class StreamResponseProcessor:
    """Processes streaming responses from the API."""

    def __init__(
        self,
        message_repository: MessageRepository,
        output_handler: OutputHandler,
        spinner: LoadingSpinner,
        tracing_config: TracingConfig | None = None,
    ) -> None:
        """Initialize stream response processor.

        Args:
            message_repository: Repository for managing messages
            output_handler: Handler for console output
            spinner: Loading spinner instance
            tracing_config: Optional tracing configuration
        """
        self._message_repository = message_repository
        self._output_handler = output_handler
        self._spinner = spinner
        self._tracing_config = tracing_config

    def process(self, response: Iterable[ChatCompletionChunk]) -> StreamResult:
        """Process streaming response and update messages.

        Args:
            response: Iterator over response chunks

        Returns:
            StreamResult with content and any tool calls
        """
        state = _ProcessingState()

        try:
            for chunk in response:
                state.chunk_count += 1
                if state.first_chunk_time is None:
                    state.first_chunk_time = time.perf_counter()
                self._process_chunk(chunk, state)

            return self._finalize(state)

        except Exception as e:
            self._spinner.stop()
            self._output_handler.display_error(f"Error processing response: {e}")
            raise

    def _process_chunk(
        self,
        chunk: ChatCompletionChunk,
        state: _ProcessingState,
    ) -> None:
        """Process a single chunk from the stream."""
        if not chunk.choices:
            return

        delta = chunk.choices[0].delta
        reasoning_content = getattr(delta, "reasoning_content", None)
        content = getattr(delta, "content", None)
        tool_calls = getattr(delta, "tool_calls", None)

        if reasoning_content:
            self._handle_reasoning(reasoning_content, state)

        if content:
            self._handle_content(content, state)

        if tool_calls:
            self._handle_tool_calls(tool_calls, state)

    def _handle_reasoning(
        self, reasoning_content: str, state: _ProcessingState
    ) -> None:
        """Handle reasoning content from chunk."""
        is_first = state.first_reasoning
        if state.first_reasoning:
            self._spinner.stop()
            state.first_reasoning = False
            state.has_reasoning = True
        self._output_handler.display_reasoning(reasoning_content, is_first)

    def _handle_content(self, content: str, state: _ProcessingState) -> None:
        """Handle content from chunk."""
        if not state.content_started:
            if not state.has_reasoning:
                self._spinner.stop()
            state.content_started = True

        self._output_handler.display_content(
            content, state.first_content, state.has_reasoning
        )

        if state.first_content:
            state.first_content = False
        state.full_content += content

    def _handle_tool_calls(
        self,
        tool_calls: list[ChoiceDeltaToolCall],
        state: _ProcessingState,
    ) -> None:
        """Handle tool call deltas from chunk."""
        for tool_call_delta in tool_calls:
            index = tool_call_delta.index

            if index not in state.tool_calls:
                self._spinner.stop()
                state.tool_calls[index] = _ToolCallBuilder()
                self._output_handler.display_tool_call_start()

            builder = state.tool_calls[index]

            if tool_call_delta.id:
                builder.id = tool_call_delta.id

            if tool_call_delta.function:
                if tool_call_delta.function.name:
                    builder.name = tool_call_delta.function.name
                    self._output_handler.display_tool_call_name(builder.name)
                if tool_call_delta.function.arguments:
                    builder.arguments += tool_call_delta.function.arguments

    def _finalize(self, state: _ProcessingState) -> StreamResult:
        """Finalize processing after all chunks are consumed."""
        if not state.content_started and not state.tool_calls:
            self._spinner.stop()

        self._output_handler.newline()

        if state.full_content:
            self._message_repository.add_assistant_message(state.full_content)

        tool_calls = [builder.to_tool_call() for builder in state.tool_calls.values()]

        if tool_calls:
            for tc in tool_calls:
                self._output_handler.display_tool_call(tc.name, tc.arguments)

        return StreamResult(
            content=state.full_content,
            tool_calls=tool_calls,
            has_content=bool(state.full_content),
        )
