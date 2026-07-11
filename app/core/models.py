"""Core data models for Android device state and captured frames.

Defines :class:`DeviceInfo`, the structured representation of a
connected (or previously connected) Android device, built by
``app.core.device`` from ``adb devices -l`` and ``getprop`` output, and
:class:`Frame`, the Capture-to-Vision contract described in VISION.md.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto

import numpy as np


class DeviceState(Enum):
    """Connection state of an Android device as reported by ADB."""

    CONNECTED = auto()
    DISCONNECTED = auto()
    UNAUTHORIZED = auto()
    UNKNOWN = auto()


@dataclass(frozen=True, slots=True)
class DeviceInfo:
    """Immutable snapshot of an Android device known to ADB.

    Attributes
    ----------
    serial:
        The device serial number, as reported by ``adb devices -l``.
    state:
        Current connection state.
    model:
        Device model name (``ro.product.model``), ``None`` until retrieved.
    android_version:
        Android release version (``ro.build.version.release``), ``None``
        until retrieved.
    resolution:
        Screen resolution as ``(width, height)`` in pixels, ``None``
        until retrieved.
    """

    serial: str
    state: DeviceState
    model: str | None = None
    android_version: str | None = None
    resolution: tuple[int, int] | None = None


@dataclass(frozen=True, slots=True)
class Frame:
    """One captured video frame, ready for Vision to consume.

    This is the formal Capture-to-Vision boundary: Vision (VISION.md's
    Stage 1) declares its input as "Android Frame (BGR)"; this
    dataclass is that contract made explicit and typed instead of a
    bare ``np.ndarray`` passed between threads.

    Attributes
    ----------
    image:
        The decoded frame as a BGR ``np.ndarray`` (OpenCV's native
        channel order), shape ``(height, width, 3)``.
    timestamp_s:
        Capture time, in seconds, from a monotonic clock.
    frame_index:
        Monotonically increasing sequence number assigned by Capture.
    """

    image: np.ndarray
    timestamp_s: float
    frame_index: int
