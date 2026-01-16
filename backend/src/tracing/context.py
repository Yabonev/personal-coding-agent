"""Context management for tracing using contextvars."""

from __future__ import annotations

from contextvars import ContextVar
from contextvars import Token
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .span import Span
    from .trace import Trace

_current_trace: ContextVar[Trace | None] = ContextVar("current_trace", default=None)
_current_span: ContextVar[Span | None] = ContextVar("current_span", default=None)


def get_current_trace() -> Trace | None:
    """Get the current trace from context."""
    return _current_trace.get()


def set_current_trace(trace: Trace | None) -> Token[Trace | None]:
    """Set the current trace in context."""
    return _current_trace.set(trace)


def reset_current_trace(token: Token[Trace | None]) -> None:
    """Reset the current trace to its previous value."""
    _current_trace.reset(token)


def get_current_span() -> Span | None:
    """Get the current span from context."""
    return _current_span.get()


def set_current_span(span: Span | None) -> Token[Span | None]:
    """Set the current span in context."""
    return _current_span.set(span)


def reset_current_span(token: Token[Span | None]) -> None:
    """Reset the current span to its previous value."""
    _current_span.reset(token)
