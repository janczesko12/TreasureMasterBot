"""Unit tests for app.core.scrcpy.

All ``adb`` calls, the server ``subprocess.Popen``, and the video
socket are mocked, so these tests require no real device or scrcpy
server jar, per TESTING.md.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core import scrcpy
from app.core.exceptions import AdbError, ScrcpyError


def _make_running_process() -> MagicMock:
    process = MagicMock()
    process.poll.return_value = None
    process.stderr = MagicMock()
    process.stderr.read.return_value = b""
    return process


def _make_connected_socket(handshake_bytes: bytes = b"h" * scrcpy.HANDSHAKE_HEADER_SKIP_BYTES) -> MagicMock:
    sock = MagicMock()
    sock.recv.side_effect = [handshake_bytes]
    return sock


@pytest.fixture
def server_jar(tmp_path: Path) -> Path:
    jar_path = tmp_path / "scrcpy-server.jar"
    jar_path.write_bytes(b"fake-jar-bytes")
    return jar_path


class TestStart:
    def test_raises_when_jar_missing(self, tmp_path: Path) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", tmp_path / "missing.jar")

        with pytest.raises(ScrcpyError, match="not found"):
            server.start()

    def test_succeeds_and_skips_handshake_header(self, server_jar: Path) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", server_jar)
        connected_socket = _make_connected_socket()

        with (
            patch("app.core.scrcpy.adb.push") as mock_push,
            patch("app.core.scrcpy.adb.forward") as mock_forward,
            patch("app.core.scrcpy.adb.remove_forward"),
            patch("app.core.scrcpy.subprocess.Popen", return_value=_make_running_process()),
            patch("app.core.scrcpy.socket.create_connection", return_value=connected_socket),
        ):
            server.start()

        mock_push.assert_called_once_with(
            "emulator-5554", str(server_jar), scrcpy.DEVICE_SERVER_PATH, adb_path="adb"
        )
        mock_forward.assert_called_once()
        connected_socket.recv.assert_called_once_with(scrcpy.HANDSHAKE_HEADER_SKIP_BYTES)

    def test_raises_and_cleans_up_when_push_fails(self, server_jar: Path) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", server_jar)

        with (
            patch("app.core.scrcpy.adb.push", side_effect=AdbError("push failed")),
            patch("app.core.scrcpy.adb.remove_forward") as mock_remove_forward,
        ):
            with pytest.raises(ScrcpyError, match="push"):
                server.start()

        mock_remove_forward.assert_called_once()

    def test_raises_when_process_exits_early(self, server_jar: Path) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", server_jar)
        exited_process = MagicMock()
        exited_process.poll.return_value = 1
        exited_process.stderr = MagicMock()
        exited_process.stderr.read.return_value = b"server crashed"

        with (
            patch("app.core.scrcpy.adb.push"),
            patch("app.core.scrcpy.adb.forward"),
            patch("app.core.scrcpy.adb.remove_forward"),
            patch("app.core.scrcpy.subprocess.Popen", return_value=exited_process),
        ):
            with pytest.raises(ScrcpyError, match="exited early"):
                server.start()

    def test_raises_on_socket_connect_timeout(self, server_jar: Path) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", server_jar, connect_timeout_s=0.0)

        with (
            patch("app.core.scrcpy.adb.push"),
            patch("app.core.scrcpy.adb.forward"),
            patch("app.core.scrcpy.adb.remove_forward"),
            patch("app.core.scrcpy.subprocess.Popen", return_value=_make_running_process()),
        ):
            with pytest.raises(ScrcpyError, match="Timed out"):
                server.start()


class TestRead:
    def test_returns_bytes_from_socket(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))
        server._socket = MagicMock()
        server._socket.recv.return_value = b"\x00\x01\x02"

        assert server.read() == b"\x00\x01\x02"

    def test_raises_when_no_socket_open(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))

        with pytest.raises(ScrcpyError, match="not open"):
            server.read()

    def test_raises_when_socket_closed_by_server(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))
        server._socket = MagicMock()
        server._socket.recv.return_value = b""

        with pytest.raises(ScrcpyError, match="closed by server"):
            server.read()

    def test_raises_on_socket_error(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))
        server._socket = MagicMock()
        server._socket.recv.side_effect = OSError("broken pipe")

        with pytest.raises(ScrcpyError, match="read failed"):
            server.read()


class TestStop:
    def test_closes_socket_process_and_forward(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))
        server._socket = MagicMock()
        server._process = MagicMock()
        server._process.wait.return_value = None

        with patch("app.core.scrcpy.adb.remove_forward") as mock_remove_forward:
            server.stop()

        assert server._socket is None
        mock_remove_forward.assert_called_once()

    def test_kills_process_when_terminate_times_out(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))
        server._process = MagicMock()
        server._process.wait.side_effect = subprocess.TimeoutExpired(cmd="adb", timeout=2.0)

        with patch("app.core.scrcpy.adb.remove_forward"):
            server.stop()

        assert server._process is None

    def test_tolerates_remove_forward_failure(self) -> None:
        server = scrcpy.ScrcpyServer("emulator-5554", Path("unused.jar"))

        with patch("app.core.scrcpy.adb.remove_forward", side_effect=AdbError("gone")):
            server.stop()
