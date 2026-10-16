"""
Configuration management and validation for DroidBridge using XDG config directory.
"""

from dataclasses import asdict, dataclass, field
import json
import logging
import os
from pathlib import Path
import re
from typing import Any, Dict, Optional

from droidbridge.constants import CONFIG_DIR, CONFIG_FILE, PRESETS

logger = logging.getLogger(__name__)

BITRATE_PATTERN = re.compile(r"^\d+([kKMm])?$")


@dataclass
class AppSettings:
    """User preferences for mirroring, audio, and UI behavior."""

    # Video Settings
    max_size: int = 1920  # 0 = native, or e.g. 1920, 1280
    max_fps: int = 60     # 30, 60, 90, 120
    video_bitrate: str = "16M"  # e.g. 8M, 16M, 24M

    # Audio Settings
    audio_enabled: bool = True
    audio_codec: str = "opus"   # opus, aac, flac, raw
    audio_source: str = "output"  # output, mic
    require_audio: bool = False  # If True, fail if audio cannot be initialized
    audio_fallback_notify: bool = True  # Show banner if audio unsupported

    # Window & Input Controls
    fullscreen: bool = False
    window_title: str = "DroidBridge Mirror"
    stay_awake: bool = True
    turn_screen_off: bool = False
    show_touches: bool = False
    start_minimized: bool = False

    # Active preset identifier
    active_preset: str = "1080p_balanced"

    def validate(self) -> None:
        """Sanitizes and clamps settings to valid boundaries."""
        if not isinstance(self.max_size, int) or self.max_size < 0:
            self.max_size = 1920
        elif self.max_size > 7680:
            self.max_size = 7680

        if not isinstance(self.max_fps, int) or self.max_fps not in [0, 30, 60, 90, 120, 144]:
            self.max_fps = 60

        if not isinstance(self.video_bitrate, str) or not BITRATE_PATTERN.match(self.video_bitrate):
            self.video_bitrate = "16M"

        if self.audio_codec not in ["opus", "aac", "flac", "raw"]:
            self.audio_codec = "opus"

        if self.audio_source not in ["output", "mic"]:
            self.audio_source = "output"

        if not isinstance(self.window_title, str) or not self.window_title.strip():
            self.window_title = "DroidBridge Mirror"

        # Limit window title length to prevent scrcpy command line bloat
        self.window_title = self.window_title.strip()[:64]

    def apply_preset(self, preset_id: str) -> bool:
        """Applies a built-in performance preset."""
        if preset_id not in PRESETS:
            return False
        preset = PRESETS[preset_id]
        self.max_size = preset["max_size"]
        self.max_fps = preset["max_fps"]
        self.video_bitrate = preset["video_bitrate"]
        self.audio_enabled = preset["audio_enabled"]
        self.active_preset = preset_id
        return True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppSettings":
        filtered_data = {}
        fields = cls.__dataclass_fields__  # type: ignore
        for key, value in data.items():
            if key in fields:
                # Type cast check
                expected_type = fields[key].type
                if expected_type == int:
                    try:
                        filtered_data[key] = int(value)
                    except (ValueError, TypeError):
                        pass
                elif expected_type == bool:
                    filtered_data[key] = bool(value)
                elif expected_type == str:
                    filtered_data[key] = str(value)
                else:
                    filtered_data[key] = value

        instance = cls(**filtered_data)
        instance.validate()
        return instance


class ConfigManager:
    """Handles thread-safe reading and writing of user configuration to XDG directory."""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or CONFIG_FILE
        self.settings = AppSettings()
        self.load()

    def load(self) -> AppSettings:
        """Loads configuration from JSON file or initializes defaults."""
        if not self.config_path.exists():
            logger.info(f"Config file not found at {self.config_path}, using defaults.")
            self.settings = AppSettings()
            return self.settings

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.settings = AppSettings.from_dict(data)
            logger.debug(f"Loaded configuration from {self.config_path}")
        except Exception as exc:
            logger.error(f"Error reading config file {self.config_path}: {exc}. Reverting to defaults.")
            self.settings = AppSettings()

        return self.settings

    def save(self) -> bool:
        """Persists current settings to XDG config directory."""
        try:
            self.settings.validate()
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Atomic write via temporary file
            temp_path = self.config_path.with_suffix(".tmp")
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(self.settings.to_dict(), f, indent=2)

            temp_path.replace(self.config_path)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as exc:
            logger.exception(f"Failed to save configuration to {self.config_path}: {exc}")
            return False

    def reset_to_defaults(self) -> AppSettings:
        """Resets settings to defaults and saves."""
        self.settings = AppSettings()
        self.save()
        return self.settings
