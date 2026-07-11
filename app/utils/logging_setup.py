"""Application-wide logging configuration.

Configures a root logger that writes to both the console and a
timestamped log file under the ``logs/`` directory, per STYLE.md's
"never use print(), use logging" rule and CLAUDE.md's required
logging events.
"""

from __future__ import annotations

import logging
import sys
from datetime import datetime
from pathlib import Path

LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_LOGS_DIR = Path(__file__).resolve().parent.parent.parent / "logs"


def setup_logging(level: int = logging.INFO, logs_dir: Path | None = None) -> Path:
    """Configure the root logger for console and file output.

    Parameters
    ----------
    level:
        Minimum log level to emit. Defaults to ``logging.INFO``.
    logs_dir:
        Directory where the log file is written. Defaults to the
        project's top-level ``logs/`` directory.

    Returns
    -------
    Path
        The path to the log file created for this run.
    """
    target_dir = logs_dir if logs_dir is not None else _LOGS_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = target_dir / f"treasuremasterbot_{timestamp}.log"

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers.clear()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    return log_file
