"""Tracing type definitions."""

from __future__ import annotations

from dataclasses import dataclass
from dataclasses import field
from enum import Enum


class SpanKind(Enum):
    """Classification of span types."""

    CONVERSATION = "conversation"
    TURN = "turn"
    LLM = "llm"
    TOOL = "tool"
    INTERNAL = "internal"


class SpanStatus(Enum):
    """Span completion status."""

    OK = "ok"
    ERROR = "error"


SpanValue = str | int | float | bool | None


@dataclass
class SpanData:
    """Arbitrary key-value data attached to a span."""

    _data: dict[str, SpanValue] = field(default_factory=dict)

    def set(self, **kwargs: SpanValue) -> None:
        """Set span data fields."""
        self._data.update(kwargs)

    def get(self, key: str, default: SpanValue = None) -> SpanValue:
        """Get a span data field."""
        return self._data.get(key, default)

    def to_dict(self) -> dict[str, SpanValue]:
        """Export data as dictionary."""
        return dict(self._data)
