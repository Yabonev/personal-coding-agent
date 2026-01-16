"""Tracing configuration."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class TracingSink(Enum):
    """Output destination for trace events."""

    NULL = "null"
    CONSOLE = "console"
    FILE = "file"
    SQLITE = "sqlite"


@dataclass
class TracingConfig:
    """Configuration for the tracing system."""

    enabled: bool = True
    sink: TracingSink = TracingSink.FILE
    file_path: str = "traces.jsonl"
    sqlite_path: str = "traces.sqlite3"
    include_sensitive_data: bool = False
    sse_enabled: bool = False

    @classmethod
    def disabled(cls) -> TracingConfig:
        """Create a disabled tracing configuration."""
        return cls(enabled=False)

    @classmethod
    def console(cls) -> TracingConfig:
        """Create a console-output tracing configuration."""
        return cls(sink=TracingSink.CONSOLE)

    @classmethod
    def file(cls, path: str = "traces.jsonl") -> TracingConfig:
        """Create a file-output tracing configuration."""
        return cls(sink=TracingSink.FILE, file_path=path)

    @classmethod
    def sqlite(
        cls,
        path: str = "traces.sqlite3",
        *,
        sse_enabled: bool = True,
        include_sensitive_data: bool = True,
    ) -> TracingConfig:
        """Create a SQLite-output tracing configuration with optional SSE."""
        return cls(
            sink=TracingSink.SQLITE,
            sqlite_path=path,
            sse_enabled=sse_enabled,
            include_sensitive_data=include_sensitive_data,
        )
