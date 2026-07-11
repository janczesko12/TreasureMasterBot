"""Application configuration.

Defines the immutable :class:`AppConfig` used throughout the app for
ADB path, device selection, timeouts, and logging level. Values are
loaded from an optional ``config.json`` at the project root, falling
back to sane defaults for any missing key, per TESTING.md's
requirement that configuration be testable without a GUI.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config.json"

DEFAULT_ADB_PATH = "adb"
DEFAULT_CONNECT_TIMEOUT_S = 10.0
DEFAULT_POLL_INTERVAL_S = 2.0
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_SCRCPY_SERVER_JAR_PATH = "vendor/scrcpy-server.jar"


@dataclass(frozen=True, slots=True)
class AppConfig:
    """Immutable application configuration.

    Attributes
    ----------
    adb_path:
        Path to the ``adb`` executable. Defaults to ``"adb"`` (resolved
        via ``PATH``).
    device_serial:
        Explicit device serial to target. ``None`` selects the first
        connected device automatically.
    connect_timeout_s:
        Timeout, in seconds, for individual ADB operations.
    poll_interval_s:
        Interval, in seconds, between device connection health checks.
    log_level:
        Root logger level name (e.g. ``"INFO"``, ``"DEBUG"``).
    scrcpy_server_jar_path:
        Path to a locally supplied ``scrcpy-server.jar`` (not bundled
        with this repository - see ``app.core.scrcpy``). Relative
        paths are resolved from the project root. Defaults to
        ``"vendor/scrcpy-server.jar"``; if missing, ``CaptureThread``
        falls back to the ``AdbScreencapBackend``.
    """

    adb_path: str = DEFAULT_ADB_PATH
    device_serial: str | None = None
    connect_timeout_s: float = DEFAULT_CONNECT_TIMEOUT_S
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S
    log_level: str = DEFAULT_LOG_LEVEL
    scrcpy_server_jar_path: str = DEFAULT_SCRCPY_SERVER_JAR_PATH

    @property
    def log_level_int(self) -> int:
        """Return the configured log level as a ``logging`` module constant."""
        return logging.getLevelNamesMapping().get(self.log_level.upper(), logging.INFO)


def load_config(config_path: Path | None = None) -> AppConfig:
    """Load :class:`AppConfig` from a JSON file, falling back to defaults.

    Parameters
    ----------
    config_path:
        Path to the JSON config file. Defaults to ``config.json`` at
        the project root. Missing files produce a default
        :class:`AppConfig` with no error.

    Returns
    -------
    AppConfig
        The resolved configuration.
    """
    target_path = config_path if config_path is not None else _DEFAULT_CONFIG_PATH

    if not target_path.exists():
        logger.info("No config file found at %s, using defaults", target_path)
        return AppConfig()

    try:
        raw_data: dict[str, Any] = json.loads(target_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        logger.warning("Failed to read config file %s (%s), using defaults", target_path, exc)
        return AppConfig()

    known_fields = {field for field in AppConfig.__dataclass_fields__}
    filtered_data = {key: value for key, value in raw_data.items() if key in known_fields}

    return AppConfig(**filtered_data)
