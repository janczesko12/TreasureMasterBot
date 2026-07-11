"""Core data models for Android device state.

Defines :class:`DeviceInfo`, the structured representation of a
connected (or previously connected) Android device, built by
``app.core.device`` from ``adb devices -l`` and ``getprop`` output.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


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
