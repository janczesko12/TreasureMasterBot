"""Capture backends: turn Android screen content into Frame objects.

Two backends implement the :class:`CaptureBackend` protocol:

``ScrcpyStreamBackend`` (primary)
    Streams a real scrcpy H.264 elementary stream from
    :class:`~app.core.scrcpy.ScrcpyServer` directly into a single
    persistent PyAV (``av``) decoder for the life of the session - the
    same decode model official scrcpy itself uses (open the decoder
    once, feed it NAL units incrementally, never reinitialize). This
    replaces an earlier disk-relay design (write bytes to a rolling
    buffer file, decode via ``cv2.VideoCapture`` reopened every few
    reads) that measured ~1 FPS at ~60% CPU on a real device: every
    reopen re-paid FFmpeg's container-probe cost and discarded decoder
    state, so most reopens failed to produce a frame until the next
    keyframe happened to land at the right buffer position. The decode
    step is still isolated behind :class:`CaptureBackend` so it can be
    replaced again later (e.g. hardware-accelerated decode) without
    touching ``CaptureThread`` or Vision.

``AdbScreencapBackend`` (fallback)
    Polls ``adb exec-out screencap -p`` and decodes the PNG with
    ``cv2.imdecode``. Used only when the scrcpy backend fails to
    start - never the default, per the approved architecture.

:func:`select_backend` is the single place backend selection happens:
scrcpy is tried first and is the long-term-performance-oriented,
architecture-centering backend; screencap is a safety net, not a user
toggle.
"""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path
from typing import Protocol

import av
import cv2
import numpy as np

from app.core import adb
from app.core.exceptions import AdbError, ScrcpyError
from app.core.frame_buffer import FrameMailbox
from app.core.models import Frame
from app.core.scrcpy import ScrcpyServer

logger = logging.getLogger(__name__)

DEFAULT_SCRCPY_CONNECT_TIMEOUT_S = 5.0
DEFAULT_SCREENCAP_TIMEOUT_S = 10.0
SCREENCAP_CMD = "screencap -p"
STREAM_READ_BUFFER_SIZE = 64 * 1024
FRAME_WAIT_TIMEOUT_S = 0.2


class CaptureBackend(Protocol):
    """Interface ``CaptureThread`` depends on, independent of which concrete backend is active."""

    def open(self) -> None:
        """Start capturing. Raises on failure to start (e.g. :class:`ScrcpyError`)."""
        ...

    def read_frame(self) -> Frame | None:
        """Return the next available frame, or ``None`` if none is ready yet."""
        ...

    def close(self) -> None:
        """Release all resources held by this backend."""
        ...


class ScrcpyStreamBackend:
    """Primary capture backend: real scrcpy H.264 stream decoded via a persistent PyAV decoder."""

    def __init__(
        self,
        serial: str,
        server_jar_path: Path,
        adb_path: str = "adb",
        connect_timeout_s: float = DEFAULT_SCRCPY_CONNECT_TIMEOUT_S,
    ) -> None:
        self._server = ScrcpyServer(serial, server_jar_path, adb_path=adb_path, connect_timeout_s=connect_timeout_s)
        self._codec_context: av.CodecContext | None = None
        self._latest_frame: FrameMailbox[Frame] = FrameMailbox()
        self._frame_ready = threading.Event()
        self._frame_index = 0
        self._decode_thread: threading.Thread | None = None
        self._stop_decoding = threading.Event()

    def open(self) -> None:
        """Start the scrcpy server and a background thread that decodes its H.264 stream.

        The PyAV codec context is created once here and lives for the
        whole session; it is never closed and reopened between reads,
        unlike the disk-relay design this replaces.

        Raises
        ------
        ScrcpyError
            Propagated from :meth:`ScrcpyServer.start` on any startup
            failure, or raised directly if the PyAV H.264 decoder
            cannot be created (e.g. no H.264 support in the installed
            FFmpeg build) - callers only need to handle one exception
            type for any capture-startup failure.
        """
        self._server.start()
        try:
            self._codec_context = av.CodecContext.create("h264", "r")
        except av.FFmpegError as exc:
            self._server.stop()
            raise ScrcpyError(f"Failed to create H.264 decoder: {exc}") from exc
        self._frame_index = 0
        self._frame_ready.clear()
        self._stop_decoding.clear()
        self._decode_thread = threading.Thread(target=self._decode_loop, name="ScrcpyDecodeLoop", daemon=True)
        self._decode_thread.start()

    def read_frame(self) -> Frame | None:
        """Return the next decoded frame, blocking briefly for one to become available.

        Waits up to :data:`FRAME_WAIT_TIMEOUT_S` for the decode thread to
        signal a new frame instead of returning instantly, giving the
        caller's polling loop real backpressure instead of a busy-spin.
        """
        if not self._frame_ready.wait(timeout=FRAME_WAIT_TIMEOUT_S):
            return None

        self._frame_ready.clear()
        return self._latest_frame.get()

    def close(self) -> None:
        """Stop the decode thread, drop the codec context, and stop the server."""
        self._stop_decoding.set()
        if self._decode_thread is not None:
            self._decode_thread.join(timeout=2.0)
            self._decode_thread = None

        self._codec_context = None
        self._server.stop()

    def _decode_loop(self) -> None:
        """Feed socket bytes into the persistent codec context and publish decoded frames.

        Runs on a single background thread for the codec context's
        entire lifetime, since PyAV decode state is not safe to share
        across threads. Decode errors on a single chunk/packet are
        logged and skipped rather than propagated, so a single
        malformed NAL unit cannot crash capture (per CLAUDE.md: capture
        failures must never crash the application).
        """
        codec_context = self._codec_context
        if codec_context is None:
            return

        while not self._stop_decoding.is_set():
            try:
                chunk = self._server.read(STREAM_READ_BUFFER_SIZE)
            except ScrcpyError:
                logger.warning("scrcpy stream ended unexpectedly")
                return

            try:
                packets = codec_context.parse(chunk)
            except av.FFmpegError:
                logger.warning("Failed to parse scrcpy H.264 stream chunk, discarding")
                continue

            for packet in packets:
                try:
                    decoded_frames = codec_context.decode(packet)
                except av.FFmpegError:
                    logger.warning("Failed to decode scrcpy H.264 packet, skipping")
                    continue

                for decoded_frame in decoded_frames:
                    image = decoded_frame.to_ndarray(format="bgr24")
                    frame = Frame(image=image, timestamp_s=time.monotonic(), frame_index=self._frame_index)
                    self._frame_index += 1
                    self._latest_frame.set(frame)
                    self._frame_ready.set()


class AdbScreencapBackend:
    """Fallback capture backend: polls ``adb exec-out screencap -p``, decoded via ``cv2.imdecode``."""

    def __init__(
        self,
        serial: str,
        adb_path: str = "adb",
        timeout_s: float = DEFAULT_SCREENCAP_TIMEOUT_S,
    ) -> None:
        self._serial = serial
        self._adb_path = adb_path
        self._timeout_s = timeout_s
        self._frame_index = 0

    def open(self) -> None:
        """No persistent connection is needed; each read is a fresh ``exec-out`` call."""

    def read_frame(self) -> Frame | None:
        """Capture and decode a single PNG screenshot via ``adb exec-out screencap -p``."""
        try:
            raw_png = adb.exec_out(self._serial, SCREENCAP_CMD, adb_path=self._adb_path, timeout_s=self._timeout_s)
        except AdbError as exc:
            logger.warning("screencap capture failed: %s", exc)
            return None

        image = cv2.imdecode(np.frombuffer(raw_png, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            logger.warning("screencap output could not be decoded")
            return None

        frame = Frame(image=image, timestamp_s=time.monotonic(), frame_index=self._frame_index)
        self._frame_index += 1
        return frame

    def close(self) -> None:
        """No persistent resources to release."""


def select_backend(
    serial: str,
    adb_path: str = "adb",
    scrcpy_server_jar_path: Path | None = None,
    scrcpy_connect_timeout_s: float = DEFAULT_SCRCPY_CONNECT_TIMEOUT_S,
) -> CaptureBackend:
    """Open and return the best available capture backend for ``serial``.

    Tries :class:`ScrcpyStreamBackend` first; on any :class:`ScrcpyError`
    (missing server jar, push/socket failure, decode-startup timeout),
    logs a warning and falls back to :class:`AdbScreencapBackend`. This
    is the sole place backend selection happens - scrcpy is the
    primary, architecture-centering backend, not a user-facing toggle.
    """
    if scrcpy_server_jar_path is not None:
        scrcpy_backend = ScrcpyStreamBackend(
            serial, scrcpy_server_jar_path, adb_path=adb_path, connect_timeout_s=scrcpy_connect_timeout_s
        )
        try:
            scrcpy_backend.open()
            logger.info("Capture backend: scrcpy (primary)")
            return scrcpy_backend
        except ScrcpyError as exc:
            logger.warning("scrcpy backend unavailable (%s), falling back to adb screencap", exc)

    screencap_backend = AdbScreencapBackend(serial, adb_path=adb_path)
    screencap_backend.open()
    logger.info("Capture backend: adb screencap (fallback)")
    return screencap_backend
