"""Core module exception hierarchy.

Used throughout ``app.core`` in place of bare ``except`` clauses, per
STYLE.md. All ADB and device-communication failures should raise one
of these instead of letting a raw ``subprocess`` or OS-level exception
propagate to the caller.
"""

from __future__ import annotations


class CoreError(Exception):
    """Base class for all ``app.core`` exceptions."""


class AdbError(CoreError):
    """Raised when an ADB command fails, times out, or produces unexpected output."""


class DeviceNotFoundError(CoreError):
    """Raised when no suitable Android device is available to select."""


class ConnectionLostError(CoreError):
    """Raised when a previously connected device becomes unreachable and automatic reconnect is exhausted."""
