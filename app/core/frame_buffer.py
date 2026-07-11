"""Frame hand-off primitives between the Capture thread and its consumers.

Two distinct hand-off shapes are needed:

``DropOldestBuffer``
    A small, bounded queue for the eventual Vision consumer. A
    producer emitting frames faster than any consumer can drain them
    must never grow without bound - a stale frame is worse than a
    dropped one in a real-time pipeline, so this discards the oldest
    queued item on overflow instead of blocking the producer.

``FrameMailbox``
    A single-slot, thread-safe "latest value" cell for the GUI live
    preview. The GUI only ever wants the newest frame, not a backlog,
    and must never block on Vision's consumption rate.
"""

from __future__ import annotations

import queue
import threading
from typing import Generic, TypeVar

T = TypeVar("T")

DEFAULT_MAX_SIZE = 4


class DropOldestBuffer(Generic[T]):
    """Fixed-capacity queue that discards the oldest item on overflow."""

    def __init__(self, max_size: int = DEFAULT_MAX_SIZE) -> None:
        self._queue: queue.Queue[T] = queue.Queue(maxsize=max_size)

    def put_latest(self, item: T) -> None:
        """Add ``item``, dropping the oldest queued item if the buffer is full."""
        while True:
            try:
                self._queue.put_nowait(item)
                return
            except queue.Full:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    continue

    def get(self, block: bool = True, timeout: float | None = None) -> T:
        """Return an item, matching ``queue.Queue.get``'s signature.

        Mirroring ``queue.Queue.get`` (rather than a bespoke signature)
        lets this buffer stand in for a plain ``queue.Queue`` wherever
        code already calls ``.get(timeout=...)`` - e.g. the unmodified
        ``QueueWorkerThread.run`` drain loop once Vision consumes this
        buffer in a later version.
        """
        return self._queue.get(block=block, timeout=timeout)

    def get_nowait(self) -> T:
        """Return an item without blocking, raising ``queue.Empty`` if none is available."""
        return self._queue.get_nowait()

    def task_done(self) -> None:
        """Mark the most recently retrieved item as processed, matching ``queue.Queue.task_done``.

        Needed for the same reason as :meth:`get`: ``QueueWorkerThread.run``
        calls ``input_queue.task_done()`` unconditionally after processing
        each item, so this buffer must support it to stand in for
        ``capture_to_vision`` once Vision drains it.
        """
        self._queue.task_done()

    def qsize(self) -> int:
        """Return the approximate number of items currently buffered."""
        return self._queue.qsize()


class FrameMailbox(Generic[T]):
    """Thread-safe single-slot cell holding only the most recently written item."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._item: T | None = None

    def set(self, item: T) -> None:
        """Overwrite the held item."""
        with self._lock:
            self._item = item

    def get(self) -> T | None:
        """Return the most recently set item, or ``None`` if nothing has been set yet."""
        with self._lock:
            return self._item
