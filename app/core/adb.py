"""Thin subprocess wrapper around the ``adb`` executable.

Exposes the minimal set of ADB operations Core needs: listing
devices, querying state, running shell commands, connecting to a
network device, and restarting the ADB server. Every call has an
explicit timeout and raises a typed :class:`AdbError` instead of
letting a raw ``subprocess`` exception propagate, per STYLE.md.
"""

from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass

from app.core.exceptions import AdbError

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_S = 10.0


@dataclass(frozen=True, slots=True)
class RawDeviceEntry:
    """One parsed line of ``adb devices -l`` output, before ``DeviceInfo`` construction."""

    serial: str
    state_text: str


def _run(adb_path: str, args: list[str], timeout_s: float) -> str:
    """Run an ``adb`` command and return its stdout, raising :class:`AdbError` on failure."""
    command = [adb_path, *args]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except FileNotFoundError as exc:
        raise AdbError(f"adb executable not found: {adb_path}") from exc
    except subprocess.TimeoutExpired as exc:
        raise AdbError(f"adb command timed out after {timeout_s}s: {' '.join(command)}") from exc

    if result.returncode != 0:
        raise AdbError(
            f"adb command failed (exit {result.returncode}): {' '.join(command)} - {result.stderr.strip()}"
        )

    return result.stdout


def list_devices(adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> list[RawDeviceEntry]:
    """Return the raw ``adb devices -l`` entries.

    Parameters
    ----------
    adb_path:
        Path to the ``adb`` executable.
    timeout_s:
        Timeout, in seconds, for the underlying command.
    """
    output = _run(adb_path, ["devices", "-l"], timeout_s)
    entries: list[RawDeviceEntry] = []
    for raw_line in output.splitlines()[1:]:
        line = raw_line.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        entries.append(RawDeviceEntry(serial=parts[0], state_text=parts[1]))

    logger.debug("Discovered %d ADB device entries", len(entries))
    return entries


def get_state(serial: str, adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> str:
    """Return the connection state of a specific device serial (e.g. ``"device"``, ``"offline"``)."""
    output = _run(adb_path, ["-s", serial, "get-state"], timeout_s)
    return output.strip()


def shell(serial: str, cmd: str, adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> str:
    """Run a shell command on the given device and return its stdout."""
    return _run(adb_path, ["-s", serial, "shell", cmd], timeout_s)


def connect(address: str, adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> str:
    """Connect to a network ADB device at ``host:port``."""
    logger.info("Connecting to ADB device at %s", address)
    return _run(adb_path, ["connect", address], timeout_s)


def kill_server(adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
    """Stop the local ADB server."""
    logger.info("Stopping ADB server")
    _run(adb_path, ["kill-server"], timeout_s)


def start_server(adb_path: str = "adb", timeout_s: float = DEFAULT_TIMEOUT_S) -> None:
    """Start the local ADB server."""
    logger.info("Starting ADB server")
    _run(adb_path, ["start-server"], timeout_s)
