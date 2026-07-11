"""TreasureMasterBot application entry point.

Loads configuration, initializes logging, starts the Core thread
pipeline, and launches the minimal PySide6 main window described in
ROADMAP.md's v0.2 scope. Full GUI functionality (live preview,
settings, debug overlay) is out of scope until later versions.
"""

from __future__ import annotations

import logging
import queue
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow, QPushButton, QVBoxLayout, QWidget

from app.core.device import DeviceStateChange
from app.core.models import DeviceInfo, DeviceState
from app.core.threading_model import ThreadPipeline
from app.utils.config import AppConfig, load_config
from app.utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)

WINDOW_TITLE = "TreasureMasterBot"
WINDOW_MIN_WIDTH = 480
WINDOW_MIN_HEIGHT = 320
DEVICE_STATE_POLL_INTERVAL_MS = 250


class MainWindow(QMainWindow):
    """Minimal application window with a status label and Start/Stop controls.

    Start/Stop are wired to no-ops in this phase; device connection and
    the automation loop are implemented in later tasks.
    """

    def __init__(self, pipeline: ThreadPipeline) -> None:
        super().__init__()
        self._pipeline = pipeline

        self.setWindowTitle(WINDOW_TITLE)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        self.status_label = QLabel("Disconnected")
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")

        self.start_button.clicked.connect(self._on_start_clicked)
        self.stop_button.clicked.connect(self._on_stop_clicked)

        layout = QVBoxLayout()
        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self._device_state_timer = QTimer(self)
        self._device_state_timer.timeout.connect(self._poll_device_state)
        self._device_state_timer.start(DEVICE_STATE_POLL_INTERVAL_MS)

    def _on_start_clicked(self) -> None:
        """Handle the Start button. No-op until automation is implemented."""
        logger.info("Start requested (no-op in this version)")

    def _on_stop_clicked(self) -> None:
        """Handle the Stop button. No-op until automation is implemented."""
        logger.info("Stop requested (no-op in this version)")

    def _poll_device_state(self) -> None:
        """Drain device connection events from the Capture thread without blocking."""
        while True:
            try:
                event = self._pipeline.device_state_queue.get_nowait()
            except queue.Empty:
                return

            if isinstance(event, DeviceInfo):
                self.status_label.setText(f"Connected: {event.model or event.serial}")
            elif isinstance(event, DeviceStateChange):
                if event.new_state == DeviceState.CONNECTED:
                    self.status_label.setText(f"Connected: {event.serial}")
                else:
                    self.status_label.setText(f"Disconnected ({event.new_state.name})")


def main() -> int:
    """Initialize the application and run the Qt event loop."""
    config: AppConfig = load_config()
    setup_logging(level=config.log_level_int)
    logger.info("Startup")

    pipeline = ThreadPipeline(
        adb_path=config.adb_path,
        device_serial=config.device_serial,
        connect_timeout_s=config.connect_timeout_s,
    )
    pipeline.start()

    app = QApplication(sys.argv)
    window = MainWindow(pipeline)
    window.show()

    exit_code = app.exec()

    pipeline.stop()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
