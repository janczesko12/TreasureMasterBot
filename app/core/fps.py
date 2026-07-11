"""Rolling-window frames-per-second counter.

Framework-agnostic (no Qt or OpenCV dependency) so Capture today, and
Vision or the GUI overlay in later versions, can share one
implementation instead of duplicating FPS math, per VISION.md and
OPENCV.md's overlay FPS requirement.
"""

from __future__ import annotations

import time
from collections import deque

DEFAULT_WINDOW_S = 2.0


class FpsCounter:
    """Tracks recent tick timestamps and reports a rolling-window FPS."""

    def __init__(self, window_s: float = DEFAULT_WINDOW_S) -> None:
        self._window_s = window_s
        self._timestamps: deque[float] = deque()

    def tick(self, now_s: float | None = None) -> None:
        """Record one frame event at ``now_s`` (defaults to the current monotonic time)."""
        timestamp = now_s if now_s is not None else time.monotonic()
        self._timestamps.append(timestamp)
        self._trim(timestamp)

    def _trim(self, now_s: float) -> None:
        cutoff = now_s - self._window_s
        while self._timestamps and self._timestamps[0] < cutoff:
            self._timestamps.popleft()

    @property
    def fps(self) -> float:
        """Return the current rolling-window frames-per-second, or ``0.0`` with fewer than 2 samples."""
        if len(self._timestamps) < 2:
            return 0.0
        elapsed = self._timestamps[-1] - self._timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self._timestamps) - 1) / elapsed
