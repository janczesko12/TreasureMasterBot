"""Queue-driven worker thread skeleton.

Implements the Capture -> Vision -> Solver -> Automation thread chain
from ARCHITECTURE.md's Thread Model. Each stage runs on its own
thread and communicates exclusively through ``queue.Queue`` instances,
per STYLE.md's rule against shared mutable state between threads.

Later phases feed real payloads (frames, detection results, actions)
through these queues; for now each worker drains its input queue and
emits periodic heartbeat log entries.
"""

from __future__ import annotations

import logging
import queue
import threading
import time
from pathlib import Path
from typing import Any

from app.core import device as device_lifecycle
from app.core.capture import CaptureBackend, DEFAULT_SCRCPY_CONNECT_TIMEOUT_S, ScrcpyStreamBackend, select_backend
from app.core.exceptions import CoreError
from app.core.fps import FpsCounter
from app.core.frame_buffer import DropOldestBuffer, FrameMailbox
from app.core.models import DeviceInfo, Frame

logger = logging.getLogger(__name__)

DEFAULT_QUEUE_TIMEOUT_S = 0.5
DEFAULT_HEARTBEAT_INTERVAL_S = 5.0
FRAME_LOOP_IDLE_SLEEP_S = 0.2
BACKEND_RETRY_BACKOFF_S = 2.0
MAX_CONSECUTIVE_READ_FAILURES = 10


class QueueWorkerThread(threading.Thread):
    """Base class for a thread that drains an input queue in a loop.

    Subclasses implement :meth:`process_item` to handle a single item
    pulled from ``input_queue``. The loop exits cleanly when
    :meth:`stop` is called.
    """

    def __init__(
        self,
        name: str,
        input_queue: queue.Queue[Any] | DropOldestBuffer[Any] | None = None,
        output_queue: queue.Queue[Any] | None = None,
        heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S,
    ) -> None:
        super().__init__(name=name, daemon=True)
        self.input_queue: queue.Queue[Any] | DropOldestBuffer[Any] = (
            input_queue if input_queue is not None else queue.Queue()
        )
        self.output_queue: queue.Queue[Any] | None = output_queue
        self._heartbeat_interval_s = heartbeat_interval_s
        self._stop_event = threading.Event()

    def run(self) -> None:
        """Drain ``input_queue`` until :meth:`stop` is called."""
        logger.info("%s started", self.name)
        while not self._stop_event.is_set():
            try:
                item = self.input_queue.get(timeout=self._heartbeat_interval_s)
            except queue.Empty:
                logger.debug("%s heartbeat", self.name)
                self.on_heartbeat()
                continue

            try:
                self.process_item(item)
            except Exception:
                logger.exception("%s failed to process item", self.name)
            finally:
                self.input_queue.task_done()

        logger.info("%s stopped", self.name)

    def process_item(self, item: Any) -> None:
        """Handle a single item drained from ``input_queue``.

        The base implementation forwards the item to ``output_queue``
        when one is configured. Subclasses override this to add
        stage-specific behavior in later phases.
        """
        if self.output_queue is not None:
            self.output_queue.put(item)

    def stop(self) -> None:
        """Signal the worker loop to exit after its current wait."""
        self._stop_event.set()

    def on_heartbeat(self) -> None:
        """Called when the input queue wait times out with no item.

        Subclasses use this to run periodic work (e.g. device polling)
        without blocking the queue-drain loop. The base implementation
        does nothing.
        """


class CaptureThread(QueueWorkerThread):
    """Owns device frame capture and the device connection lifecycle.

    Beyond frame capture (implemented in v0.3), this thread owns the
    device detection/health-check/reconnect lifecycle from
    ``app.core.device``, publishing :class:`~app.core.models.DeviceInfo`
    and :class:`~app.core.device.DeviceStateChange` events onto
    ``device_state_queue`` so the GUI thread can display connection
    status without blocking.
    """

    def __init__(
        self,
        output_buffer: DropOldestBuffer[Frame] | None = None,
        frame_mailbox: FrameMailbox[Frame] | None = None,
        device_state_queue: queue.Queue[Any] | None = None,
        adb_path: str = "adb",
        device_serial: str | None = None,
        connect_timeout_s: float = 10.0,
        scrcpy_server_jar_path: Path | None = None,
        scrcpy_connect_timeout_s: float = DEFAULT_SCRCPY_CONNECT_TIMEOUT_S,
    ) -> None:
        super().__init__(name="CaptureThread")
        self.device_state_queue: queue.Queue[Any] = device_state_queue if device_state_queue is not None else queue.Queue()
        self.output_buffer = output_buffer
        self.frame_mailbox = frame_mailbox
        self._adb_path = adb_path
        self._device_serial = device_serial
        self._connect_timeout_s = connect_timeout_s
        self._scrcpy_server_jar_path = scrcpy_server_jar_path
        self._scrcpy_connect_timeout_s = scrcpy_connect_timeout_s
        self._monitor: device_lifecycle.DeviceHealthMonitor | None = None
        self._backend: CaptureBackend | None = None
        self._fps_counter = FpsCounter()

    @property
    def fps(self) -> float:
        """Return the current rolling-window capture frames-per-second."""
        return self._fps_counter.fps

    @property
    def active_backend_name(self) -> str:
        """Return ``"scrcpy"``, ``"screencap"``, or ``"none"`` for the currently active backend."""
        if self._backend is None:
            return "none"
        return "scrcpy" if isinstance(self._backend, ScrcpyStreamBackend) else "screencap"

    def run(self) -> None:
        """Produce frames from the active capture backend until :meth:`stop` is called.

        ``CaptureThread`` is a producer, not a queue consumer, so it does
        not use ``QueueWorkerThread``'s drain loop. Device-health polling
        (:meth:`on_heartbeat`) instead runs on its own
        ``heartbeat_interval_s`` cadence, tracked by elapsed time inside
        this loop, independent of the frame-capture cadence.
        """
        logger.info("%s started", self.name)
        last_heartbeat = time.monotonic()
        consecutive_failures = 0

        while not self._stop_event.is_set():
            now = time.monotonic()
            if now - last_heartbeat >= self._heartbeat_interval_s:
                self.on_heartbeat()
                last_heartbeat = now

            if self._monitor is None:
                time.sleep(FRAME_LOOP_IDLE_SLEEP_S)
                continue

            if self._backend is None:
                self._backend = self._open_backend()
                if self._backend is None:
                    time.sleep(BACKEND_RETRY_BACKOFF_S)
                    continue
                consecutive_failures = 0

            try:
                frame = self._backend.read_frame()
            except Exception:
                logger.exception("%s backend read failed", self.name)
                frame = None

            if frame is None:
                consecutive_failures += 1
                if consecutive_failures >= MAX_CONSECUTIVE_READ_FAILURES:
                    logger.warning("%s backend unresponsive, re-selecting", self.name)
                    self._close_backend()
                    consecutive_failures = 0
                    time.sleep(BACKEND_RETRY_BACKOFF_S)
                continue

            consecutive_failures = 0
            self._fps_counter.tick()
            if self.output_buffer is not None:
                self.output_buffer.put_latest(frame)
            if self.frame_mailbox is not None:
                self.frame_mailbox.set(frame)

        self._close_backend()
        logger.info("%s stopped", self.name)

    def _open_backend(self) -> CaptureBackend | None:
        """Select and open a capture backend for the current device, or ``None`` on failure."""
        if self._monitor is None:
            return None
        try:
            return select_backend(
                self._monitor.serial,
                adb_path=self._adb_path,
                scrcpy_server_jar_path=self._scrcpy_server_jar_path,
                scrcpy_connect_timeout_s=self._scrcpy_connect_timeout_s,
            )
        except CoreError as exc:
            logger.warning("Failed to open any capture backend: %s", exc)
            return None

    def _close_backend(self) -> None:
        """Close and clear the active backend, if any."""
        if self._backend is not None:
            self._backend.close()
            self._backend = None

    def on_heartbeat(self) -> None:
        """Detect a device if none is selected yet, otherwise poll its health."""
        if self._monitor is None:
            self._try_select_device()
            return

        change = self._monitor.poll()
        if change is None:
            return

        self.device_state_queue.put(change)

        if change.new_state != device_lifecycle.DeviceState.CONNECTED:
            self._close_backend()
            self._try_reconnect()

    def _try_select_device(self) -> None:
        try:
            devices = device_lifecycle.list_device_info(adb_path=self._adb_path, timeout_s=self._connect_timeout_s)
            selected = device_lifecycle.select_device(devices, preferred_serial=self._device_serial)
            selected = device_lifecycle.fetch_device_details(
                selected, adb_path=self._adb_path, timeout_s=self._connect_timeout_s
            )
        except CoreError as exc:
            logger.warning("No device available yet: %s", exc)
            return

        logger.info("Device Connected: %s", selected)
        self._monitor = device_lifecycle.DeviceHealthMonitor(
            selected, adb_path=self._adb_path, timeout_s=self._connect_timeout_s
        )
        self.device_state_queue.put(selected)

    def _try_reconnect(self) -> None:
        if self._monitor is None:
            return
        try:
            reconnected: DeviceInfo = device_lifecycle.attempt_reconnect(
                self._monitor.serial, adb_path=self._adb_path, timeout_s=self._connect_timeout_s
            )
        except CoreError as exc:
            logger.error("Automatic reconnect failed: %s", exc)
            self._monitor = None
            return

        self._monitor = device_lifecycle.DeviceHealthMonitor(
            reconnected, adb_path=self._adb_path, timeout_s=self._connect_timeout_s
        )
        self.device_state_queue.put(reconnected)


class VisionThread(QueueWorkerThread):
    """Converts captured frames into structured detection results."""

    def __init__(
        self,
        input_queue: queue.Queue[Any] | None = None,
        output_queue: queue.Queue[Any] | None = None,
    ) -> None:
        super().__init__(name="VisionThread", input_queue=input_queue, output_queue=output_queue)


class SolverThread(QueueWorkerThread):
    """Turns detection results into automation actions."""

    def __init__(
        self,
        input_queue: queue.Queue[Any] | None = None,
        output_queue: queue.Queue[Any] | None = None,
    ) -> None:
        super().__init__(name="SolverThread", input_queue=input_queue, output_queue=output_queue)


class AutomationThread(QueueWorkerThread):
    """Executes actions against the Android device."""

    def __init__(self, input_queue: queue.Queue[Any] | None = None) -> None:
        super().__init__(name="AutomationThread", input_queue=input_queue)


class ThreadPipeline:
    """Wires the four worker threads together with connecting queues."""

    def __init__(
        self,
        adb_path: str = "adb",
        device_serial: str | None = None,
        connect_timeout_s: float = 10.0,
        scrcpy_server_jar_path: Path | None = None,
        scrcpy_connect_timeout_s: float = DEFAULT_SCRCPY_CONNECT_TIMEOUT_S,
    ) -> None:
        self.capture_to_vision: DropOldestBuffer[Frame] = DropOldestBuffer()
        self.vision_to_solver: queue.Queue[Any] = queue.Queue()
        self.solver_to_automation: queue.Queue[Any] = queue.Queue()
        self.device_state_queue: queue.Queue[Any] = queue.Queue()
        self.frame_mailbox: FrameMailbox[Frame] = FrameMailbox()

        self.capture = CaptureThread(
            output_buffer=self.capture_to_vision,
            frame_mailbox=self.frame_mailbox,
            device_state_queue=self.device_state_queue,
            adb_path=adb_path,
            device_serial=device_serial,
            connect_timeout_s=connect_timeout_s,
            scrcpy_server_jar_path=scrcpy_server_jar_path,
            scrcpy_connect_timeout_s=scrcpy_connect_timeout_s,
        )
        self.vision = VisionThread(input_queue=self.capture_to_vision, output_queue=self.vision_to_solver)
        self.solver = SolverThread(input_queue=self.vision_to_solver, output_queue=self.solver_to_automation)
        self.automation = AutomationThread(input_queue=self.solver_to_automation)

        self._workers: tuple[QueueWorkerThread, ...] = (
            self.capture,
            self.vision,
            self.solver,
            self.automation,
        )

    def start(self) -> None:
        """Start all worker threads."""
        for worker in self._workers:
            worker.start()

    def stop(self, timeout_s: float = 2.0) -> None:
        """Signal all worker threads to stop and wait for them to exit."""
        for worker in self._workers:
            worker.stop()
        for worker in self._workers:
            worker.join(timeout=timeout_s)
