"""
Structured logging configuration with log rotation and serial number redaction.
"""

import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
from typing import Optional

from droidbridge.constants import LOG_FILE, STATE_DIR

# Regex pattern for device serial numbers (alphanumeric, 8 to 24 chars)
SERIAL_PATTERN = re.compile(r"\b([a-zA-Z0-9]{8,24})\b")


class SerialRedactionFilter(logging.Filter):
    """Redacts hardware serial numbers from logs for privacy."""

    def __init__(self, preserved_serials: Optional[list] = None):
        super().__init__()
        self.preserved_serials = preserved_serials or []

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Redact suspected serials unless they are common words
            def replace_serial(match):
                val = match.group(1)
                # Keep common lowercase/mixed words
                if len(val) >= 10 and (val.isalnum() and not val.isalpha()):
                    return f"{val[:3]}...{val[-2:]}"
                return val

            record.msg = SERIAL_PATTERN.sub(replace_serial, record.msg)
        return True


def redact_text(text: str) -> str:
    """Utility to redact serial numbers from text output (e.g. diagnostics exports)."""
    if not text:
        return ""

    def replace_serial(match):
        val = match.group(1)
        if len(val) >= 8 and any(c.isdigit() for c in val) and any(c.isalpha() for c in val):
            return f"{val[:2]}***{val[-2:]}"
        return val

    return SERIAL_PATTERN.sub(replace_serial, text)


def setup_logging(debug: bool = False) -> logging.Logger:
    """Configures application logger with rotating file handler and console output."""
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        print(f"Warning: Could not create log directory {STATE_DIR}: {exc}")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG if debug else logging.INFO)

    # Avoid duplicate handlers on re-init
    if root_logger.handlers:
        return logging.getLogger("droidbridge")

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console Handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG if debug else logging.INFO)
    root_logger.addHandler(console_handler)

    # Rotating File Handler (Max 2 MB, 3 backups)
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=2 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.DEBUG)
        file_handler.addFilter(SerialRedactionFilter())
        root_logger.addHandler(file_handler)
    except Exception as exc:
        print(f"Warning: Could not initialize rotating file logger at {LOG_FILE}: {exc}")

    logger = logging.getLogger("droidbridge")
    logger.info("DroidBridge logging initialized.")
    return logger
