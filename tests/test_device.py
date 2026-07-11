"""Unit tests for app.core.device.

All ADB interaction is mocked with canned output so these tests
require no real device, per TESTING.md.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from app.core import device
from app.core.adb import RawDeviceEntry
from app.core.exceptions import AdbError, ConnectionLostError, DeviceNotFoundError
from app.core.models import DeviceInfo, DeviceState


class TestParseState:
    @pytest.mark.parametrize(
        ("state_text", "expected"),
        [
            ("device", DeviceState.CONNECTED),
            ("offline", DeviceState.DISCONNECTED),
            ("unauthorized", DeviceState.UNAUTHORIZED),
            ("bootloader", DeviceState.UNKNOWN),
        ],
    )
    def test_maps_known_and_unknown_states(self, state_text: str, expected: DeviceState) -> None:
        assert device._parse_state(state_text) == expected


class TestListDeviceInfo:
    def test_converts_raw_entries_to_device_info(self) -> None:
        raw_entries = [
            RawDeviceEntry(serial="emulator-5554", state_text="device"),
            RawDeviceEntry(serial="ABC123", state_text="unauthorized"),
        ]
        with patch("app.core.device.adb.list_devices", return_value=raw_entries):
            devices = device.list_device_info()

        assert devices == [
            DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED),
            DeviceInfo(serial="ABC123", state=DeviceState.UNAUTHORIZED),
        ]


class TestSelectDevice:
    def test_selects_first_connected_device(self) -> None:
        devices = [
            DeviceInfo(serial="offline-1", state=DeviceState.DISCONNECTED),
            DeviceInfo(serial="good-1", state=DeviceState.CONNECTED),
        ]

        selected = device.select_device(devices)

        assert selected.serial == "good-1"

    def test_raises_when_no_connected_device(self) -> None:
        devices = [DeviceInfo(serial="offline-1", state=DeviceState.DISCONNECTED)]

        with pytest.raises(DeviceNotFoundError):
            device.select_device(devices)

    def test_prefers_configured_serial_even_if_not_connected(self) -> None:
        devices = [
            DeviceInfo(serial="good-1", state=DeviceState.CONNECTED),
            DeviceInfo(serial="target", state=DeviceState.UNAUTHORIZED),
        ]

        selected = device.select_device(devices, preferred_serial="target")

        assert selected.serial == "target"

    def test_raises_when_configured_serial_absent(self) -> None:
        devices = [DeviceInfo(serial="good-1", state=DeviceState.CONNECTED)]

        with pytest.raises(DeviceNotFoundError):
            device.select_device(devices, preferred_serial="missing")


class TestFetchDeviceDetails:
    def test_populates_model_version_and_resolution(self) -> None:
        base_device = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)
        shell_responses = {
            "getprop ro.product.model": "sdk_gphone64_x86_64\n",
            "getprop ro.build.version.release": "14\n",
            "wm size": "Physical size: 1080x2400\n",
        }

        def fake_shell(serial: str, cmd: str, adb_path: str = "adb", timeout_s: float = 10.0) -> str:
            return shell_responses[cmd]

        with patch("app.core.device.adb.shell", side_effect=fake_shell):
            enriched = device.fetch_device_details(base_device)

        assert enriched.model == "sdk_gphone64_x86_64"
        assert enriched.android_version == "14"
        assert enriched.resolution == (1080, 2400)
        assert enriched.serial == base_device.serial


class TestDeviceHealthMonitor:
    def test_poll_returns_none_when_state_unchanged(self) -> None:
        base_device = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)
        monitor = device.DeviceHealthMonitor(base_device)

        with patch("app.core.device.adb.get_state", return_value="device"):
            result = monitor.poll()

        assert result is None
        assert monitor.current_state == DeviceState.CONNECTED

    def test_poll_returns_change_when_state_transitions(self) -> None:
        base_device = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)
        monitor = device.DeviceHealthMonitor(base_device)

        with patch("app.core.device.adb.get_state", return_value="offline"):
            result = monitor.poll()

        assert result == device.DeviceStateChange(
            serial="emulator-5554",
            previous_state=DeviceState.CONNECTED,
            new_state=DeviceState.DISCONNECTED,
        )
        assert monitor.current_state == DeviceState.DISCONNECTED

    def test_poll_treats_adb_error_as_disconnected(self) -> None:
        base_device = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)
        monitor = device.DeviceHealthMonitor(base_device)

        with patch("app.core.device.adb.get_state", side_effect=AdbError("no device")):
            result = monitor.poll()

        assert result is not None
        assert result.new_state == DeviceState.DISCONNECTED


class TestAttemptReconnect:
    def test_succeeds_on_first_attempt(self) -> None:
        reconnected = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)

        with (
            patch("app.core.device.time.sleep"),
            patch("app.core.device.adb.kill_server"),
            patch("app.core.device.adb.start_server"),
            patch("app.core.device.list_device_info", return_value=[reconnected]),
        ):
            result = device.attempt_reconnect("emulator-5554", max_attempts=3)

        assert result == reconnected

    def test_raises_connection_lost_after_exhausting_attempts(self) -> None:
        with (
            patch("app.core.device.time.sleep"),
            patch("app.core.device.adb.kill_server"),
            patch("app.core.device.adb.start_server"),
            patch("app.core.device.list_device_info", return_value=[]),
        ):
            with pytest.raises(ConnectionLostError):
                device.attempt_reconnect("emulator-5554", max_attempts=2)

    def test_continues_past_adb_errors_during_attempts(self) -> None:
        reconnected = DeviceInfo(serial="emulator-5554", state=DeviceState.CONNECTED)

        with (
            patch("app.core.device.time.sleep"),
            patch("app.core.device.adb.kill_server", side_effect=[AdbError("busy"), None]),
            patch("app.core.device.adb.start_server"),
            patch("app.core.device.list_device_info", return_value=[reconnected]),
        ):
            result = device.attempt_reconnect("emulator-5554", max_attempts=3)

        assert result == reconnected
