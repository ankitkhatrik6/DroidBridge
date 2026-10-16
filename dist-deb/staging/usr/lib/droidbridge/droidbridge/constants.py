"""
Application constants and defaults for DroidBridge.
"""

from enum import Enum
import os
from pathlib import Path


APP_ID = "org.droidbridge.DroidBridge"
APP_NAME = "DroidBridge"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "Native Linux Android USB Screen Mirroring & Audio Forwarding"

# XDG Paths
XDG_CONFIG_HOME = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
XDG_STATE_HOME = Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local" / "state"))
XDG_DATA_HOME = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))

CONFIG_DIR = XDG_CONFIG_HOME / "droidbridge"
STATE_DIR = XDG_STATE_HOME / "droidbridge"
CONFIG_FILE = CONFIG_DIR / "config.json"
LOG_FILE = STATE_DIR / "droidbridge.log"

# Minimum required versions
MIN_SCRCPY_VERSION = "2.0"
MIN_ANDROID_AUDIO_API = 30  # Android 11+ required for internal audio forwarding

# Timeouts in seconds
ADB_COMMAND_TIMEOUT = 10.0
ADB_DEVICES_TIMEOUT = 5.0
SCRCPY_VERSION_TIMEOUT = 5.0
DEVICE_POLL_INTERVAL_SECONDS = 2.5


class ConnectionState(str, Enum):
    CHECKING_DEPENDENCIES = "CHECKING_DEPENDENCIES"
    WAITING_FOR_DEVICE = "WAITING_FOR_DEVICE"
    DEVICE_DETECTED = "DEVICE_DETECTED"
    AUTHORIZATION_REQUIRED = "AUTHORIZATION_REQUIRED"
    DEVICE_OFFLINE = "DEVICE_OFFLINE"
    STARTING_SESSION = "STARTING_SESSION"
    MIRRORING_ACTIVE = "MIRRORING_ACTIVE"
    AUDIO_UNAVAILABLE = "AUDIO_UNAVAILABLE"
    SESSION_STOPPED = "SESSION_STOPPED"
    RECOVERABLE_ERROR = "RECOVERABLE_ERROR"


class AudioStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    INITIALIZING = "INITIALIZING"
    STREAMING = "STREAMING"
    UNSUPPORTED_ANDROID = "UNSUPPORTED_ANDROID"
    UNSUPPORTED_SCRCPY = "UNSUPPORTED_SCRCPY"
    DISABLED_BY_USER = "DISABLED_BY_USER"
    CAPTURE_FAILED = "CAPTURE_FAILED"


PRESETS = {
    "1080p_balanced": {
        "id": "1080p_balanced",
        "name": "1080p Balanced",
        "description": "1920x1080, 60fps, 16 Mbps video (Recommended)",
        "max_size": 1920,
        "max_fps": 60,
        "video_bitrate": "16M",
        "audio_enabled": True,
    },
    "720p_low_lat": {
        "id": "720p_low_lat",
        "name": "720p Low Latency",
        "description": "1280x720, 60fps, 8 Mbps video (Fastest response)",
        "max_size": 1280,
        "max_fps": 60,
        "video_bitrate": "8M",
        "audio_enabled": True,
    },
    "4k_hq": {
        "id": "4k_hq",
        "name": "4K High Quality",
        "description": "Native/3840x2160, 60fps, 24 Mbps video (USB 3.0+)",
        "max_size": 3840,
        "max_fps": 60,
        "video_bitrate": "24M",
        "audio_enabled": True,
    },
}
