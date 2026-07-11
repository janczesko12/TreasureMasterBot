"""Unit tests for app.core.adb.

All ``subprocess.run`` calls are mocked with canned ``adb`` output so
these tests require no real device or ADB installation, per
TESTING.md.
"""

from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest

from app.core import adb
from app.core.exceptions import AdbError


def _mock_completed_process(stdout: str = "", stderr: str = "", returncode: int = 0) -> MagicMock:
    result = MagicMock()
    result.stdout = stdout
    result.stderr = stderr
    result.returncode = returncode
    return result


class TestRun:
    def test_returns_stdout_on_success(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stdout="ok\n")) as mock_run:
            output = adb._run("adb", ["devices"], timeout_s=5.0)

        assert output == "ok\n"
        mock_run.assert_called_once()

    def test_raises_adb_error_on_nonzero_exit(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stderr="boom", returncode=1)):
            with pytest.raises(AdbError):
                adb._run("adb", ["devices"], timeout_s=5.0)

    def test_raises_adb_error_when_executable_missing(self) -> None:
        with patch("app.core.adb.subprocess.run", side_effect=FileNotFoundError()):
            with pytest.raises(AdbError):
                adb._run("adb", ["devices"], timeout_s=5.0)

    def test_raises_adb_error_on_timeout(self) -> None:
        with patch("app.core.adb.subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="adb", timeout=5.0)):
            with pytest.raises(AdbError):
                adb._run("adb", ["devices"], timeout_s=5.0)


class TestListDevices:
    def test_parses_multiple_devices(self) -> None:
        raw_output = (
            "List of devices attached\n"
            "emulator-5554\tdevice product:sdk_gphone64_x86_64 model:sdk_gphone64_x86_64 device:emu64a\n"
            "ABC123\tunauthorized usb:1-1 product:unknown\n"
            "\n"
        )
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stdout=raw_output)):
            entries = adb.list_devices()

        assert len(entries) == 2
        assert entries[0] == adb.RawDeviceEntry(serial="emulator-5554", state_text="device")
        assert entries[1] == adb.RawDeviceEntry(serial="ABC123", state_text="unauthorized")

    def test_returns_empty_list_when_no_devices(self) -> None:
        raw_output = "List of devices attached\n\n"
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stdout=raw_output)):
            entries = adb.list_devices()

        assert entries == []


class TestGetState:
    def test_returns_stripped_state(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stdout="device\n")):
            state = adb.get_state("emulator-5554")

        assert state == "device"


class TestShell:
    def test_returns_command_stdout(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process(stdout="sdk_gphone64\n")):
            output = adb.shell("emulator-5554", "getprop ro.product.model")

        assert output == "sdk_gphone64\n"


class TestServerControl:
    def test_kill_server_invokes_adb(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process()) as mock_run:
            adb.kill_server()

        args = mock_run.call_args[0][0]
        assert args == ["adb", "kill-server"]

    def test_start_server_invokes_adb(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process()) as mock_run:
            adb.start_server()

        args = mock_run.call_args[0][0]
        assert args == ["adb", "start-server"]

    def test_connect_invokes_adb_with_address(self) -> None:
        with patch("app.core.adb.subprocess.run", return_value=_mock_completed_process()) as mock_run:
            adb.connect("192.168.1.50:5555")

        args = mock_run.call_args[0][0]
        assert args == ["adb", "connect", "192.168.1.50:5555"]
