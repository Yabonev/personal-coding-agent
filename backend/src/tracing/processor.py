"""Trace processors for outputting span events."""

from __future__ import annotations

import json
import sqlite3
import sys
from datetime import UTC
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING
from typing import Protocol

if TYPE_CHECKING:
    from .span import Span


class TracingProcessor(Protocol):
    """Protocol for processing completed spans."""

    def on_span_start(self, span: Span) -> None:
        """Called when a span starts."""
        ...

    def on_span_end(self, span: Span) -> None:
        """Called when a span finishes."""
        ...

    def shutdown(self) -> None:
        """Clean up resources."""
        ...

    def supports_sse(self) -> bool:
        """Whether this processor supports SSE broadcasting."""
        ...


def _span_to_dict(span: Span, *, is_start: bool = False) -> dict[str, object]:
    """Convert a span to a dictionary for serialization."""
    return {
        "ts": datetime.now(UTC).isoformat(timespec="milliseconds"),
        "trace_id": span.trace_id,
        "span_id": span.span_id,
        "parent_id": span.parent_id,
        "name": span.name,
        "kind": span.kind.value,
        "duration_ms": span.duration_ms,
        "status": "running" if is_start else span.status.value,
        "data": span.data.to_dict(),
        "error": span.error,
    }


class NullProcessor:
    """Processor that discards all spans."""

    def on_span_start(self, span: Span) -> None:
        """Discard the span."""

    def on_span_end(self, span: Span) -> None:
        """Discard the span."""

    def shutdown(self) -> None:
        """Nothing to clean up."""

    def supports_sse(self) -> bool:
        """SSE not supported."""
        return False


class ConsoleProcessor:
    """Processor that writes spans to stderr as JSON."""

    def on_span_start(self, span: Span) -> None:
        """Write span start to stderr."""
        event = _span_to_dict(span, is_start=True)
        sys.stderr.write(json.dumps(event) + "\n")
        sys.stderr.flush()

    def on_span_end(self, span: Span) -> None:
        """Write span to stderr."""
        event = _span_to_dict(span)
        sys.stderr.write(json.dumps(event) + "\n")
        sys.stderr.flush()

    def shutdown(self) -> None:
        """Nothing to clean up."""

    def supports_sse(self) -> bool:
        """SSE not supported."""
        return False


class FileProcessor:
    """Processor that writes spans to a JSON Lines file."""

    def __init__(self, file_path: str) -> None:
        self._file_path = Path(file_path)
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def on_span_start(self, span: Span) -> None:
        """Append span start to file."""
        event = _span_to_dict(span, is_start=True)
        with self._file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def on_span_end(self, span: Span) -> None:
        """Append span to file."""
        event = _span_to_dict(span)
        with self._file_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(event) + "\n")

    def shutdown(self) -> None:
        """Nothing to clean up."""

    def supports_sse(self) -> bool:
        """SSE not supported."""
        return False


_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS spans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    span_id TEXT NOT NULL UNIQUE,
    parent_id TEXT,
    name TEXT NOT NULL,
    kind TEXT NOT NULL,
    duration_ms REAL,
    status TEXT NOT NULL,
    data_json TEXT NOT NULL,
    error TEXT
);

CREATE INDEX IF NOT EXISTS spans_trace_id ON spans(trace_id);
CREATE INDEX IF NOT EXISTS spans_parent_id ON spans(parent_id);
"""


class SQLiteProcessor:
    """Processor that writes spans to a SQLite database."""

    def __init__(self, db_path: str, *, sse_enabled: bool = False) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._sse_enabled = sse_enabled

        self._conn = sqlite3.connect(
            str(self._db_path),
            check_same_thread=False,
        )
        self._conn.executescript("PRAGMA journal_mode=WAL; PRAGMA synchronous=NORMAL;")
        self._conn.executescript(_SQLITE_SCHEMA)
        self._conn.commit()

    def on_span_start(self, span: Span) -> None:
        """Insert span into database when it starts."""
        event = _span_to_dict(span, is_start=True)

        self._conn.execute(
            """
            INSERT INTO spans (ts, trace_id, span_id, parent_id, name, kind,
                               duration_ms, status, data_json, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event["ts"],
                event["trace_id"],
                event["span_id"],
                event["parent_id"],
                event["name"],
                event["kind"],
                event["duration_ms"],
                event["status"],
                json.dumps(event["data"]),
                event["error"],
            ),
        )
        self._conn.commit()

        if self._sse_enabled:
            from .broadcaster import publish_span  # noqa: PLC0415

            publish_span(event)

    def on_span_end(self, span: Span) -> None:
        """Update span in database when it ends."""
        event = _span_to_dict(span)

        self._conn.execute(
            """
            UPDATE spans
            SET duration_ms = ?, status = ?, data_json = ?, error = ?
            WHERE span_id = ?
            """,
            (
                event["duration_ms"],
                event["status"],
                json.dumps(event["data"]),
                event["error"],
                event["span_id"],
            ),
        )
        self._conn.commit()

        if self._sse_enabled:
            from .broadcaster import publish_span  # noqa: PLC0415

            publish_span(event)

    def shutdown(self) -> None:
        """Close database connection."""
        self._conn.close()

    def supports_sse(self) -> bool:
        """SSE supported when enabled."""
        return self._sse_enabled
