"""Tests for SQLite processor."""

from __future__ import annotations

import json
import sqlite3
import tempfile
from pathlib import Path

import pytest

from src.tracing import Span
from src.tracing import SpanKind
from src.tracing import SQLiteProcessor
from src.tracing.processor import NullProcessor


@pytest.fixture
def temp_db_path():
    """Create a temporary database path."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield str(Path(tmpdir) / "test_traces.sqlite3")


@pytest.fixture
def processor(temp_db_path):
    """Create a SQLite processor with a temporary database."""
    proc = SQLiteProcessor(temp_db_path, sse_enabled=False)
    yield proc
    proc.shutdown()


@pytest.fixture
def span():
    """Create a test span."""
    s = Span(
        name="test.span",
        kind=SpanKind.TOOL,
        trace_id="tr_test123",
        processor=NullProcessor(),
        parent_id="sp_parent123",
        span_id="sp_test456",
    )
    s.set(tool_name="read_file", result_len=100)
    s.start()
    s.finish()
    return s


def test_creates_database_file(temp_db_path):
    processor = SQLiteProcessor(temp_db_path)
    assert Path(temp_db_path).exists()
    processor.shutdown()


def test_creates_spans_table(temp_db_path):
    processor = SQLiteProcessor(temp_db_path)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='spans'"
    )
    assert cursor.fetchone() is not None
    conn.close()
    processor.shutdown()


def test_inserts_span(processor, span, temp_db_path):
    processor.on_span_start(span)
    processor.on_span_end(span)

    conn = sqlite3.connect(temp_db_path)
    cursor = conn.execute("SELECT * FROM spans WHERE span_id = ?", (span.span_id,))
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    assert "tr_test123" in str(row)
    assert "sp_test456" in str(row)
    assert "test.span" in str(row)


def test_span_data_stored_as_json(processor, span, temp_db_path):
    processor.on_span_start(span)
    processor.on_span_end(span)

    conn = sqlite3.connect(temp_db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(
        "SELECT data_json FROM spans WHERE span_id = ?", (span.span_id,)
    )
    row = cursor.fetchone()
    conn.close()

    data = json.loads(row["data_json"])
    assert data["tool_name"] == "read_file"
    assert data["result_len"] == 100


def test_supports_sse_returns_false_when_disabled(temp_db_path):
    processor = SQLiteProcessor(temp_db_path, sse_enabled=False)
    assert processor.supports_sse() is False
    processor.shutdown()


def test_supports_sse_returns_true_when_enabled(temp_db_path):
    processor = SQLiteProcessor(temp_db_path, sse_enabled=True)
    assert processor.supports_sse() is True
    processor.shutdown()
