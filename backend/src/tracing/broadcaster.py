"""Thread-safe broadcaster for real-time span streaming via SSE."""

from __future__ import annotations

import contextlib
import threading
from collections.abc import Iterator
from contextlib import contextmanager
from queue import Queue

type SpanEvent = dict[str, object]

_broadcaster: SpanBroadcaster | None = None
_lock = threading.Lock()


class SpanBroadcaster:
    """Broadcasts span events to multiple SSE subscribers (thread-safe)."""

    def __init__(self) -> None:
        self._subscribers: set[Queue[SpanEvent]] = set()
        self._lock = threading.Lock()

    def publish(self, event: SpanEvent) -> None:
        """Publish an event to all subscribers (thread-safe)."""
        with self._lock:
            for queue in self._subscribers:
                with contextlib.suppress(Exception):
                    queue.put_nowait(event)

    @contextmanager
    def subscribe(self) -> Iterator[Queue[SpanEvent]]:
        """Subscribe to span events. Yields a queue that receives events."""
        queue: Queue[SpanEvent] = Queue(maxsize=1000)
        with self._lock:
            self._subscribers.add(queue)
        try:
            yield queue
        finally:
            with self._lock:
                self._subscribers.discard(queue)


def get_broadcaster() -> SpanBroadcaster:
    """Get or create the global broadcaster instance."""
    global _broadcaster  # noqa: PLW0603
    with _lock:
        if _broadcaster is None:
            _broadcaster = SpanBroadcaster()
        return _broadcaster


def publish_span(event: SpanEvent) -> None:
    """Publish a span event (thread-safe)."""
    get_broadcaster().publish(event)
