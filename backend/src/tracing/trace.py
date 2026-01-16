"""Trace implementation for grouping spans."""

from __future__ import annotations

import uuid
from contextvars import Token
from types import TracebackType
from typing import Self

from .config import TracingConfig
from .config import TracingSink
from .context import get_current_span
from .context import get_current_trace
from .context import reset_current_trace
from .context import set_current_trace
from .processor import ConsoleProcessor
from .processor import FileProcessor
from .processor import NullProcessor
from .processor import SQLiteProcessor
from .processor import TracingProcessor
from .span import Span
from .types import SpanKind
from .types import SpanValue


def _create_processor(config: TracingConfig) -> TracingProcessor:
    """Create a processor based on configuration."""
    if not config.enabled:
        return NullProcessor()
    if config.sink == TracingSink.CONSOLE:
        return ConsoleProcessor()
    if config.sink == TracingSink.FILE:
        return FileProcessor(config.file_path)
    if config.sink == TracingSink.SQLITE:
        return SQLiteProcessor(config.sqlite_path, sse_enabled=config.sse_enabled)
    return NullProcessor()


class Trace:
    """A trace groups related spans for a single user interaction."""

    def __init__(
        self,
        name: str,
        config: TracingConfig | None = None,
        trace_id: str | None = None,
    ) -> None:
        self._name = name
        self._config = config or TracingConfig()
        self._trace_id = trace_id or f"tr_{uuid.uuid4().hex[:12]}"
        self._processor = _create_processor(self._config)
        self._context_token: Token[Trace | None] | None = None
        self._root_span: Span | None = None

    @property
    def trace_id(self) -> str:
        """Unique trace ID."""
        return self._trace_id

    @property
    def name(self) -> str:
        """Trace name."""
        return self._name

    @property
    def config(self) -> TracingConfig:
        """Tracing configuration."""
        return self._config

    @property
    def processor(self) -> TracingProcessor:
        """The processor for this trace."""
        return self._processor

    def set(self, **data: SpanValue) -> None:
        """Set data on the root span."""
        if self._root_span is not None:
            self._root_span.set(**data)

    def span(
        self,
        name: str,
        kind: SpanKind = SpanKind.INTERNAL,
        **data: SpanValue,
    ) -> Span:
        """Create a new span within this trace."""
        current_span = get_current_span()
        parent_id = current_span.span_id if current_span else None

        span = Span(
            name=name,
            kind=kind,
            trace_id=self._trace_id,
            processor=self._processor,
            parent_id=parent_id,
        )
        if data:
            span.set(**data)
        return span

    def start(self) -> Trace:
        """Start the trace and its root span."""
        self._context_token = set_current_trace(self)
        self._root_span = Span(
            name=self._name,
            kind=SpanKind.CONVERSATION,
            trace_id=self._trace_id,
            processor=self._processor,
        )
        self._root_span.start()
        return self

    def finish(self) -> None:
        """Finish the trace and its root span."""
        if self._root_span:
            self._root_span.finish()
        if self._context_token is not None:
            reset_current_trace(self._context_token)

    def __enter__(self) -> Self:
        """Enter trace context."""
        return self.start()  # type: ignore[return-value]

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit trace context."""
        if exc_val is not None and self._root_span:
            self._root_span.set_error(
                f"{exc_type.__name__ if exc_type else 'Error'}: {exc_val}"
            )
        self.finish()


def trace(
    name: str,
    config: TracingConfig | None = None,
    **data: SpanValue,
) -> Trace:
    """Create a new trace."""
    t = Trace(name=name, config=config)
    if data:
        t.set(**data)
    return t


def span(
    name: str,
    kind: SpanKind = SpanKind.INTERNAL,
    **data: SpanValue,
) -> Span:
    """Create a span in the current trace context."""
    current_trace = get_current_trace()
    if current_trace:
        return current_trace.span(name, kind, **data)

    return Span(
        name=name,
        kind=kind,
        trace_id="no_trace",
        processor=NullProcessor(),
    )
