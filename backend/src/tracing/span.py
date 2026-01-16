"""Span implementation for timing and tracing operations."""

from __future__ import annotations

import time
import uuid
from contextvars import Token
from types import TracebackType
from typing import TYPE_CHECKING
from typing import Self

from .context import reset_current_span
from .context import set_current_span
from .types import SpanData
from .types import SpanKind
from .types import SpanStatus
from .types import SpanValue

if TYPE_CHECKING:
    from .processor import TracingProcessor


class Span:
    """A span represents a single operation within a trace."""

    def __init__(  # noqa: PLR0913
        self,
        name: str,
        kind: SpanKind,
        trace_id: str,
        processor: TracingProcessor,
        parent_id: str | None = None,
        span_id: str | None = None,
    ) -> None:
        self._name = name
        self._kind = kind
        self._trace_id = trace_id
        self._parent_id = parent_id
        self._span_id = span_id or f"sp_{uuid.uuid4().hex[:12]}"
        self._processor = processor

        self._data = SpanData()
        self._status = SpanStatus.OK
        self._error: str | None = None

        self._start_time: float | None = None
        self._end_time: float | None = None
        self._context_token: Token[Span | None] | None = None

    @property
    def name(self) -> str:
        """Span name."""
        return self._name

    @property
    def kind(self) -> SpanKind:
        """Span kind."""
        return self._kind

    @property
    def trace_id(self) -> str:
        """Parent trace ID."""
        return self._trace_id

    @property
    def span_id(self) -> str:
        """Unique span ID."""
        return self._span_id

    @property
    def parent_id(self) -> str | None:
        """Parent span ID, if any."""
        return self._parent_id

    @property
    def data(self) -> SpanData:
        """Span data."""
        return self._data

    @property
    def status(self) -> SpanStatus:
        """Span status."""
        return self._status

    @property
    def error(self) -> str | None:
        """Error message if status is ERROR."""
        return self._error

    @property
    def duration_ms(self) -> float | None:
        """Duration in milliseconds."""
        if self._start_time is None or self._end_time is None:
            return None
        return (self._end_time - self._start_time) * 1000

    def set(self, **kwargs: SpanValue) -> None:
        """Set span data fields."""
        self._data.set(**kwargs)

    def set_error(self, error: str) -> None:
        """Mark span as errored with a message."""
        self._status = SpanStatus.ERROR
        self._error = error

    def start(self) -> Span:
        """Start the span and set it as current."""
        self._start_time = time.perf_counter()
        self._context_token = set_current_span(self)
        self._processor.on_span_start(self)
        return self

    def finish(self) -> None:
        """Finish the span and emit to processor."""
        self._end_time = time.perf_counter()
        if self._context_token is not None:
            reset_current_span(self._context_token)
        self._processor.on_span_end(self)

    def __enter__(self) -> Self:
        """Enter span context."""
        return self.start()  # type: ignore[return-value]

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit span context, capturing any exception."""
        if exc_val is not None:
            self.set_error(f"{exc_type.__name__ if exc_type else 'Error'}: {exc_val}")
        self.finish()
