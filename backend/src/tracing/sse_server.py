"""Simple SSE server for streaming span events."""

from __future__ import annotations

import json
import sqlite3
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from pathlib import Path
from queue import Empty
from threading import Thread
from typing import TYPE_CHECKING

from .broadcaster import get_broadcaster

if TYPE_CHECKING:
    from .broadcaster import SpanEvent

DEFAULT_PORT = 8765


class SSEHandler(BaseHTTPRequestHandler):
    """HTTP handler for SSE endpoints."""

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Suppress default logging."""

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/api/spans/stream":
            self._handle_sse_stream()
        elif self.path == "/api/spans/history":
            self._handle_history()
        elif self.path == "/api/health":
            self._send_json({"status": "ok"})
        else:
            self.send_error(404)

    def do_OPTIONS(self) -> None:
        """Handle CORS preflight requests."""
        self._handle_cors_preflight()

    def _handle_cors_preflight(self) -> None:
        """Send CORS headers for preflight."""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_cors_headers(self) -> None:
        """Add CORS headers to response."""
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Last-Event-ID")

    def _send_json(self, data: dict[str, object]) -> None:
        """Send a JSON response."""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def _handle_sse_stream(self) -> None:
        """Stream SSE events to client."""
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._send_cors_headers()
        self.end_headers()

        broadcaster = get_broadcaster()
        event_id = 0

        with broadcaster.subscribe() as queue:
            while True:
                try:
                    event = queue.get(timeout=15.0)
                    event_id += 1
                    self._write_sse_event(event_id, event)
                except Empty:
                    self._write_keepalive()
                except (BrokenPipeError, ConnectionResetError):
                    break

    def _write_sse_event(self, event_id: int, event: SpanEvent) -> None:
        """Write an SSE event to the response."""
        lines = [
            f"id: {event_id}",
            "event: span",
            f"data: {json.dumps(event)}",
            "",
            "",
        ]
        self.wfile.write("\n".join(lines).encode())
        self.wfile.flush()

    def _write_keepalive(self) -> None:
        """Write a keepalive comment."""
        self.wfile.write(b": ping\n\n")
        self.wfile.flush()

    def _handle_history(self) -> None:
        """Return historical spans from SQLite."""
        db_path: Path | None = getattr(self.server, "db_path", None)
        if db_path is None or not db_path.exists():
            self._send_json({"spans": []})
            return

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.execute(
            """
            SELECT ts, trace_id, span_id, parent_id, name, kind,
                   duration_ms, status, data_json, error
            FROM spans
            ORDER BY ts ASC
            """
        )
        spans = []
        for row in cursor:
            spans.append({
                "ts": row["ts"],
                "trace_id": row["trace_id"],
                "span_id": row["span_id"],
                "parent_id": row["parent_id"],
                "name": row["name"],
                "kind": row["kind"],
                "duration_ms": row["duration_ms"],
                "status": row["status"],
                "data": json.loads(row["data_json"]),
                "error": row["error"],
            })
        conn.close()
        self._send_json({"spans": spans})


class SSEServer:
    """SSE server for streaming spans to the trace viewer."""

    def __init__(self, port: int = DEFAULT_PORT, db_path: Path | None = None) -> None:
        self._port = port
        self._db_path = db_path
        self._server: HTTPServer | None = None
        self._thread: Thread | None = None

    def start(self) -> None:
        """Start the SSE server in a background thread."""
        self._server = HTTPServer(("127.0.0.1", self._port), SSEHandler)
        self._server.db_path = self._db_path  # type: ignore[attr-defined]
        self._thread = Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the SSE server."""
        if self._server is not None:
            self._server.shutdown()
            self._server = None

    @property
    def port(self) -> int:
        """Get the server port."""
        return self._port

    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"http://127.0.0.1:{self._port}"
