"""Android device detection and selection.

Builds :class:`~app.core.models.DeviceInfo` records from raw ``adb
devices -l`` output and selects the device Core should target, per
ROADMAP.md's v0.2 "Device Communication" scope.
"""

from __future__ import annotations

import dataclasses
import logging
import re
import time

from app.core import adb
from app.core.exceptions import AdbError, ConnectionLostError, DeviceNotFoundError
from app.core.models import DeviceInfo, DeviceState

logger = logging.getLogger(__name__)

_MODEL_PROP = "ro.product.model"
_ANDROID_VERSION_PROP = "ro.build.version.release"
_WM_SIZE_PATTERN = re.compile(r"(\d+)x(\d+)")

DEFAULT_MAX_RECONNECT_ATTEMPTS = 5
DEFAULT_RECONNECT_BACKOFF_BASE_S = 1.0

_STATE_TEXT_MAP: dict[str, DeviceState] = {
    "device": DeviceState.CONNECTED,
    "offline": DeviceState.DISCONNECTED,
    "unauthorized": DeviceState.UNAUTHORIZED,
}

_SKIPPABLE_STATES = (DeviceState.UNAUTHORIZED, DeviceState.DISCONNECTED)


def _parse_state(state_text: str) -> DeviceState:
    """Map an ``adb devices -l`` state token to a :class:`DeviceState`."""
    return _STATE_TEXT_MAP.get(state_text, DeviceState.UNKNOWN)


def list_device_info(adb_path: str = "adb", timeout_s: float = adb.DEFAULT_TIMEOUT_S) -> list[DeviceInfo]:
    """Return :class:`DeviceInfo` for every device ``adb`` currently reports."""
    raw_entries = adb.list_devices(adb_path=adb_path, timeout_s=timeout_s)
    devices = [DeviceInfo(serial=entry.serial, state=_parse_state(entry.state_text)) for entry in raw_entries]
    logger.debug("Parsed %d device(s) from adb", len(devices))
    return devices


def select_device(devices: list[DeviceInfo], preferred_serial: str | None = None) -> DeviceInfo:
    """Select the device Core should target.

    Parameters
    ----------
    devices:
        Devices discovered via :func:`list_device_info`.
    preferred_serial:
        Serial to select explicitly (from :class:`~app.utils.config.AppConfig`),
        if provided.

    Returns
    -------
    DeviceInfo
        The selected device.

    Raises
    ------
    DeviceNotFoundError
        If no eligible device is available.
    """
    if preferred_serial is not None:
        for device in devices:
            if device.serial == preferred_serial:
                if device.state in _SKIPPABLE_STATES:
                    logger.warning("Configured device %s is in state %s", device.serial, device.state.name)
                return device
        raise DeviceNotFoundError(f"Configured device serial not found: {preferred_serial}")

    for device in devices:
        if device.state == DeviceState.CONNECTED:
            return device
        logger.warning("Skipping device %s in state %s", device.serial, device.state.name)

    raise DeviceNotFoundError("No connected Android device found")


def _parse_resolution(wm_size_output: str) -> tuple[int, int] | None:
    """Extract ``(width, height)`` from ``wm size`` output (e.g. ``"Physical size: 1080x2400"``)."""
    match = _WM_SIZE_PATTERN.search(wm_size_output)
    if match is None:
        return None
    return int(match.group(1)), int(match.group(2))


def fetch_device_details(
    device: DeviceInfo,
    adb_path: str = "adb",
    timeout_s: float = adb.DEFAULT_TIMEOUT_S,
) -> DeviceInfo:
    """Return a copy of ``device`` populated with model, Android version, and resolution.

    Only valid for a device in :attr:`DeviceState.CONNECTED` state;
    the caller is responsible for that check.
    """
    model = adb.shell(device.serial, f"getprop {_MODEL_PROP}", adb_path=adb_path, timeout_s=timeout_s).strip()
    android_version = adb.shell(
        device.serial, f"getprop {_ANDROID_VERSION_PROP}", adb_path=adb_path, timeout_s=timeout_s
    ).strip()
    wm_size_output = adb.shell(device.serial, "wm size", adb_path=adb_path, timeout_s=timeout_s)
    resolution = _parse_resolution(wm_size_output)

    logger.info("Device %s: model=%s android=%s resolution=%s", device.serial, model, android_version, resolution)

    return dataclasses.replace(
        device,
        model=model or None,
        android_version=android_version or None,
        resolution=resolution,
    )


@dataclasses.dataclass(frozen=True, slots=True)
class DeviceStateChange:
    """A detected transition in a device's connection state."""

    serial: str
    previous_state: DeviceState
    new_state: DeviceState


class DeviceHealthMonitor:
    """Polls a single device's connection state and reports transitions.

    Intended to be driven periodically (e.g. from :class:`~app.core.threading_model.CaptureThread`)
    via :meth:`poll`, which returns ``None`` when the state is unchanged
    and a :class:`DeviceStateChange` when it isn't.
    """

    def __init__(
        self,
        device: DeviceInfo,
        adb_path: str = "adb",
        timeout_s: float = adb.DEFAULT_TIMEOUT_S,
    ) -> None:
        self.serial = device.serial
        self._adb_path = adb_path
        self._timeout_s = timeout_s
        self._current_state = device.state

    @property
    def current_state(self) -> DeviceState:
        """The most recently observed state."""
        return self._current_state

    def poll(self) -> DeviceStateChange | None:
        """Check the device's current state, returning a change if one occurred."""
        try:
            state_text = adb.get_state(self.serial, adb_path=self._adb_path, timeout_s=self._timeout_s)
            new_state = _parse_state(state_text)
        except AdbError:
            new_state = DeviceState.DISCONNECTED

        if new_state == self._current_state:
            return None

        change = DeviceStateChange(serial=self.serial, previous_state=self._current_state, new_state=new_state)
        logger.info(
            "Device %s state changed: %s -> %s",
            self.serial,
            change.previous_state.name,
            change.new_state.name,
        )
        self._current_state = new_state
        return change


def attempt_reconnect(
    serial: str,
    adb_path: str = "adb",
    timeout_s: float = adb.DEFAULT_TIMEOUT_S,
    max_attempts: int = DEFAULT_MAX_RECONNECT_ATTEMPTS,
    backoff_base_s: float = DEFAULT_RECONNECT_BACKOFF_BASE_S,
) -> DeviceInfo:
    """Attempt to restore a lost ADB connection to ``serial`` with exponential backoff.

    Cycles ``adb kill-server`` -> ``adb start-server`` -> re-detection on
    each attempt, waiting longer between attempts each time.

    Raises
    ------
    ConnectionLostError
        If ``max_attempts`` are exhausted without the device reappearing
        in :attr:`~app.core.models.DeviceState.CONNECTED` state.
    """
    logger.info("Recovery Started")

    for attempt in range(1, max_attempts + 1):
        delay_s = backoff_base_s * (2 ** (attempt - 1))
        logger.info("Reconnect attempt %d/%d for %s (waiting %.1fs)", attempt, max_attempts, serial, delay_s)
        time.sleep(delay_s)

        try:
            adb.kill_server(adb_path=adb_path, timeout_s=timeout_s)
            adb.start_server(adb_path=adb_path, timeout_s=timeout_s)
            devices = list_device_info(adb_path=adb_path, timeout_s=timeout_s)
        except AdbError as exc:
            logger.warning("Reconnect attempt %d failed: %s", attempt, exc)
            continue

        for device in devices:
            if device.serial == serial and device.state == DeviceState.CONNECTED:
                logger.info("Recovery Completed")
                return device

    logger.error("Recovery failed for device %s after %d attempts", serial, max_attempts)
    raise ConnectionLostError(f"Failed to reconnect to device {serial} after {max_attempts} attempts")
