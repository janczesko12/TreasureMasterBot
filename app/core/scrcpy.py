"""Minimal scrcpy server lifecycle: push, launch, and stream raw H.264.

Talks to the real scrcpy Android server component the same way the
reference scrcpy desktop client does: push ``scrcpy-server.jar`` to
the device, launch it with ``adb shell app_process``, expose its local
abstract socket over a TCP port with ``adb forward``, and read the raw
H.264 Annex-B elementary stream it writes to that socket.

The server jar itself is not bundled with this repository - like
``scrcpy-server.jar`` in the upstream scrcpy project, it is a compiled
Android component built with a full Android toolchain, not something
generated from Python source. It must be supplied externally and
pointed to via ``server_jar_path``, the same way ``adb.exe`` is
supplied externally via ``AppConfig.adb_path`` rather than bundled.
When the jar is missing, the push fails, or the server does not start
streaming in time, this module raises :class:`ScrcpyError` so callers
(``ScrcpyStreamBackend``) can fall back to ``AdbScreencapBackend``.

Protocol note: the scrcpy wire protocol (server launch arguments and
the video-socket handshake header written before the raw stream)
could not be verified against upstream source during this session -
see VERSION_0_3 planning notes. ``HANDSHAKE_HEADER_SKIP_BYTES`` below
is a best-effort value for common recent scrcpy server versions. A
mismatch degrades gracefully: the H.264 Annex-B decoder in
``ScrcpyStreamBackend`` scans for the next start code and resyncs, it
does not corrupt or crash on a slightly wrong skip length.
"""

from __future__ import annotations

import logging
import socket
import subprocess
import time
from pathlib import Path

from app.core import adb
from app.core.exceptions import AdbError, ScrcpyError

logger = logging.getLogger(__name__)

DEVICE_SERVER_PATH = "/data/local/tmp/scrcpy-server.jar"
SERVER_MAIN_CLASS = "com.genymobile.scrcpy.Server"
SERVER_VERSION = "2.4"
DEFAULT_LOCAL_PORT = 27183
DEFAULT_SOCKET_NAME = "scrcpy"
DEFAULT_CONNECT_TIMEOUT_S = 5.0
SOCKET_CONNECT_POLL_INTERVAL_S = 0.2
SOCKET_READ_TIMEOUT_S = 2.0
PROCESS_STOP_TIMEOUT_S = 2.0
HANDSHAKE_HEADER_SKIP_BYTES = 69


class ScrcpyServer:
    """Owns the on-device scrcpy server process and its video socket."""

    def __init__(
        self,
        serial: str,
        server_jar_path: Path,
        adb_path: str = "adb",
        local_port: int = DEFAULT_LOCAL_PORT,
        socket_name: str = DEFAULT_SOCKET_NAME,
        connect_timeout_s: float = DEFAULT_CONNECT_TIMEOUT_S,
    ) -> None:
        self._serial = serial
        self._server_jar_path = server_jar_path
        self._adb_path = adb_path
        self._local_port = local_port
        self._socket_name = socket_name
        self._connect_timeout_s = connect_timeout_s
        self._process: subprocess.Popen[bytes] | None = None
        self._socket: socket.socket | None = None

    def start(self) -> None:
        """Push, launch, and connect to the on-device scrcpy server.

        Raises
        ------
        ScrcpyError
            If the server jar is missing, the push or port-forward
            fails, the server process fails to launch or exits early,
            or the video socket does not become available within
            ``connect_timeout_s``.
        """
        if not self._server_jar_path.is_file():
            raise ScrcpyError(
                f"scrcpy server jar not found at {self._server_jar_path}. "
                "Download scrcpy-server.jar from an upstream scrcpy release "
                "matching SERVER_VERSION and configure its path."
            )

        try:
            self._push_server()
            self._forward_port()
            self._launch_process()
            self._connect_socket()
            self._skip_handshake_header()
        except ScrcpyError:
            self.stop()
            raise

        logger.info("scrcpy server streaming on %s (port %d)", self._serial, self._local_port)

    def read(self, buffer_size: int = 4096) -> bytes:
        """Read up to ``buffer_size`` raw H.264 bytes from the video socket."""
        if self._socket is None:
            raise ScrcpyError("scrcpy server socket is not open")
        try:
            data = self._socket.recv(buffer_size)
        except OSError as exc:
            raise ScrcpyError(f"scrcpy video socket read failed: {exc}") from exc
        if not data:
            raise ScrcpyError("scrcpy video socket closed by server")
        return data

    def stop(self) -> None:
        """Close the socket, terminate the server process, and remove the port forward."""
        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass
            self._socket = None

        if self._process is not None:
            self._process.terminate()
            try:
                self._process.wait(timeout=PROCESS_STOP_TIMEOUT_S)
            except subprocess.TimeoutExpired:
                self._process.kill()
            self._process = None

        try:
            adb.remove_forward(self._serial, self._local_port, adb_path=self._adb_path)
        except AdbError:
            logger.debug("Could not remove adb forward for port %d (already gone?)", self._local_port)

    def _push_server(self) -> None:
        try:
            adb.push(self._serial, str(self._server_jar_path), DEVICE_SERVER_PATH, adb_path=self._adb_path)
        except AdbError as exc:
            raise ScrcpyError(f"Failed to push scrcpy server to device: {exc}") from exc

    def _forward_port(self) -> None:
        try:
            adb.forward(self._serial, self._local_port, self._socket_name, adb_path=self._adb_path)
        except AdbError as exc:
            raise ScrcpyError(f"Failed to set up adb forward for scrcpy socket: {exc}") from exc

    def _launch_process(self) -> None:
        command = [
            self._adb_path,
            "-s",
            self._serial,
            "shell",
            f"CLASSPATH={DEVICE_SERVER_PATH}",
            "app_process",
            "/",
            SERVER_MAIN_CLASS,
            SERVER_VERSION,
            "tunnel_forward=true",
            "audio=false",
            "control=false",
            "cleanup=true",
            "send_device_meta=false",
            "send_dummy_byte=false",
        ]
        try:
            self._process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
        except OSError as exc:
            raise ScrcpyError(f"Failed to launch scrcpy server process: {exc}") from exc

    def _connect_socket(self) -> None:
        deadline = time.monotonic() + self._connect_timeout_s
        last_error: OSError | None = None
        while time.monotonic() < deadline:
            if self._process is not None and self._process.poll() is not None:
                stderr_text = self._process.stderr.read().decode(errors="replace") if self._process.stderr else ""
                raise ScrcpyError(f"scrcpy server process exited early: {stderr_text.strip()}")
            try:
                sock = socket.create_connection(("127.0.0.1", self._local_port), timeout=0.5)
                sock.settimeout(SOCKET_READ_TIMEOUT_S)
                self._socket = sock
                return
            except OSError as exc:
                last_error = exc
                time.sleep(SOCKET_CONNECT_POLL_INTERVAL_S)

        raise ScrcpyError(f"Timed out connecting to scrcpy video socket on port {self._local_port}: {last_error}")

    def _skip_handshake_header(self) -> None:
        if self._socket is None:
            return
        remaining = HANDSHAKE_HEADER_SKIP_BYTES
        while remaining > 0:
            chunk = self._socket.recv(remaining)
            if not chunk:
                raise ScrcpyError("scrcpy video socket closed during handshake read")
            remaining -= len(chunk)
