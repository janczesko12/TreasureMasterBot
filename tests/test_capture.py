"""Unit tests for app.core.capture.

New test-only file; nothing imports it except pytest's test discovery.
Covers the public API of ``app/core/capture.py`` (``ScrcpyStreamBackend``,
``AdbScreencapBackend``, ``select_backend``). ``TestScrcpyStreamBackend``
was rewritten for the persistent-PyAV-decoder redesign (replacing the
earlier disk-relay + ``cv2.VideoCapture``-reopen design) per the
approved capture-pipeline-redesign plan. No real device, scrcpy server
jar, or sample H.264 clip is available in this sandbox, so
``ScrcpyServer`` and ``av.CodecContext`` are mocked rather than
exercising real decode; ``AdbScreencapBackend`` is tested against a
real small PNG so its ``cv2.imdecode`` path is genuinely exercised. No
data schemas involved.
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import av
import cv2
import numpy as np
import pytest

from app.core.capture import (
    AdbScreencapBackend,
    ScrcpyStreamBackend,
    select_backend,
)
from app.core.exceptions import AdbError, ScrcpyError
from app.core.models import Frame


def _encode_png(image: np.ndarray) -> bytes:
    ok, buffer = cv2.imencode(".png", image)
    assert ok
    return buffer.tobytes()


class TestAdbScreencapBackend:
    def test_read_frame_returns_frame_on_success(self) -> None:
        backend = AdbScreencapBackend("emulator-5554")
        raw_png = _encode_png(np.zeros((4, 4, 3), dtype=np.uint8))

        with patch("app.core.capture.adb.exec_out", return_value=raw_png):
            frame = backend.read_frame()

        assert isinstance(frame, Frame)
        assert frame.image.shape == (4, 4, 3)
        assert frame.frame_index == 0

    def test_read_frame_increments_frame_index(self) -> None:
        backend = AdbScreencapBackend("emulator-5554")
        raw_png = _encode_png(np.zeros((2, 2, 3), dtype=np.uint8))

        with patch("app.core.capture.adb.exec_out", return_value=raw_png):
            first = backend.read_frame()
            second = backend.read_frame()

        assert first is not None
        assert second is not None
        assert (first.frame_index, second.frame_index) == (0, 1)

    def test_read_frame_returns_none_on_adb_error(self) -> None:
        backend = AdbScreencapBackend("emulator-5554")

        with patch("app.core.capture.adb.exec_out", side_effect=AdbError("device offline")):
            assert backend.read_frame() is None

    def test_read_frame_returns_none_on_undecodable_bytes(self) -> None:
        backend = AdbScreencapBackend("emulator-5554")

        with patch("app.core.capture.adb.exec_out", return_value=b"not a png"):
            assert backend.read_frame() is None

    def test_open_and_close_do_not_raise(self) -> None:
        backend = AdbScreencapBackend("emulator-5554")
        backend.open()
        backend.close()


class TestScrcpyStreamBackend:
    def test_open_starts_server_and_creates_codec_context_once(self, tmp_path: Path) -> None:
        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create") as mock_codec_create,
        ):
            mock_server = mock_server_cls.return_value
            mock_server.read.side_effect = ScrcpyError("stream ended")
            mock_codec_create.return_value = MagicMock()

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            backend.open()
            try:
                mock_server.start.assert_called_once()
                mock_codec_create.assert_called_once_with("h264", "r")
            finally:
                backend.close()

        mock_server.stop.assert_called_once()

    def test_open_raises_scrcpy_error_and_stops_server_when_codec_creation_fails(self, tmp_path: Path) -> None:
        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create", side_effect=av.FFmpegError(-1, "no h264 decoder")),
        ):
            mock_server = mock_server_cls.return_value

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            with pytest.raises(ScrcpyError, match="decoder"):
                backend.open()

        mock_server.start.assert_called_once()
        mock_server.stop.assert_called_once()

    def test_read_frame_returns_decoded_frames_without_reopening_codec(self, tmp_path: Path) -> None:
        fake_image = np.zeros((2, 2, 3), dtype=np.uint8)
        mock_packet = MagicMock()
        mock_av_frame = MagicMock()
        mock_av_frame.to_ndarray.return_value = fake_image

        mock_codec_context = MagicMock()
        mock_codec_context.parse.return_value = [mock_packet]
        mock_codec_context.decode.return_value = [mock_av_frame]

        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create", return_value=mock_codec_context) as mock_codec_create,
        ):
            mock_server = mock_server_cls.return_value
            mock_server.read.return_value = b"\x00\x00\x00\x01fake-nal-unit"

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            backend.open()
            try:
                first = backend.read_frame()
                second = backend.read_frame()
            finally:
                backend.close()

        assert first is not None
        assert second is not None
        assert first.image.shape == (2, 2, 3)
        assert second.image.shape == (2, 2, 3)
        assert second.frame_index > first.frame_index
        mock_codec_create.assert_called_once()

    def test_read_frame_returns_none_when_no_frame_ready_within_timeout(self, tmp_path: Path) -> None:
        mock_codec_context = MagicMock()
        mock_codec_context.parse.return_value = []

        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create", return_value=mock_codec_context),
            patch("app.core.capture.FRAME_WAIT_TIMEOUT_S", 0.01),
        ):
            mock_server = mock_server_cls.return_value
            mock_server.read.return_value = b"\x00\x00\x00\x01no-frame-yet"

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            backend.open()
            try:
                frame = backend.read_frame()
            finally:
                backend.close()

        assert frame is None

    def test_decode_loop_skips_chunk_on_parse_error_without_crashing(self, tmp_path: Path) -> None:
        fake_image = np.zeros((2, 2, 3), dtype=np.uint8)
        mock_av_frame = MagicMock()
        mock_av_frame.to_ndarray.return_value = fake_image
        mock_packet = MagicMock()

        # A plain function (rather than a side_effect list) so the decode
        # thread - which keeps calling parse() in a tight loop against the
        # mocked, always-ready server - never exhausts a finite iterator and
        # raises StopIteration from inside the mock.
        parse_call_count = 0

        def parse_side_effect(_chunk: bytes) -> list[MagicMock]:
            nonlocal parse_call_count
            parse_call_count += 1
            if parse_call_count == 1:
                raise av.FFmpegError(-1, "corrupt data")
            return [mock_packet]

        mock_codec_context = MagicMock()
        mock_codec_context.parse.side_effect = parse_side_effect
        mock_codec_context.decode.return_value = [mock_av_frame]

        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create", return_value=mock_codec_context),
        ):
            mock_server = mock_server_cls.return_value
            mock_server.read.return_value = b"\x00\x00\x00\x01chunk"

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            backend.open()
            try:
                frame = backend.read_frame()
            finally:
                backend.close()

        assert frame is not None
        assert parse_call_count >= 2

    def test_close_stops_decode_thread_and_server(self, tmp_path: Path) -> None:
        mock_codec_context = MagicMock()
        mock_codec_context.parse.return_value = []

        with (
            patch("app.core.capture.ScrcpyServer") as mock_server_cls,
            patch("app.core.capture.av.CodecContext.create", return_value=mock_codec_context),
        ):
            mock_server = mock_server_cls.return_value
            mock_server.read.return_value = b"\x00\x00\x00\x01idle"

            backend = ScrcpyStreamBackend("emulator-5554", tmp_path / "server.jar")
            backend.open()
            decode_thread = backend._decode_thread

            backend.close()

        assert backend._decode_thread is None
        assert decode_thread is not None
        assert not decode_thread.is_alive()
        mock_server.stop.assert_called_once()


class TestSelectBackend:
    def test_selects_scrcpy_when_it_opens_successfully(self, tmp_path: Path) -> None:
        with patch("app.core.capture.ScrcpyStreamBackend") as mock_scrcpy_cls:
            mock_scrcpy_cls.return_value.open.return_value = None

            backend = select_backend("emulator-5554", scrcpy_server_jar_path=tmp_path / "server.jar")

        assert backend is mock_scrcpy_cls.return_value

    def test_falls_back_to_screencap_when_scrcpy_fails_to_open(self, tmp_path: Path) -> None:
        with patch("app.core.capture.ScrcpyStreamBackend") as mock_scrcpy_cls:
            mock_scrcpy_cls.return_value.open.side_effect = ScrcpyError("no jar")

            backend = select_backend("emulator-5554", scrcpy_server_jar_path=tmp_path / "server.jar")

        assert isinstance(backend, AdbScreencapBackend)

    def test_uses_screencap_directly_when_no_jar_path_given(self) -> None:
        with patch("app.core.capture.ScrcpyStreamBackend") as mock_scrcpy_cls:
            backend = select_backend("emulator-5554", scrcpy_server_jar_path=None)

        mock_scrcpy_cls.assert_not_called()
        assert isinstance(backend, AdbScreencapBackend)
