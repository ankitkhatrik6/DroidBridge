"""
scrcpy service for command synthesis, version verification, and capability negotiation.
"""

import logging
import re
from typing import List, Optional, Tuple

from droidbridge.config import AppSettings
from droidbridge.constants import MIN_ANDROID_AUDIO_API, MIN_SCRCPY_VERSION, SCRCPY_VERSION_TIMEOUT
from droidbridge.utils.command_runner import find_executable, run_command
from droidbridge.utils.errors import ScrcpyIncompatibleVersionError, ScrcpyNotFoundError

logger = logging.getLogger(__name__)


def parse_version_tuple(version_str: str) -> Tuple[int, ...]:
    """Extracts major.minor.patch numeric tuple for version comparisons."""
    parts = []
    for token in re.findall(r"\d+", version_str):
        try:
            parts.append(int(token))
        except ValueError:
            break
    return tuple(parts) if parts else (0, 0)


class ScrcpyService:
    """Manages scrcpy binary discovery, validation, and command construction."""

    def __init__(self, scrcpy_path: Optional[str] = None):
        self._scrcpy_path = scrcpy_path or find_executable("scrcpy")
        self._cached_version: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self._scrcpy_path is not None

    @property
    def scrcpy_path(self) -> str:
        if not self._scrcpy_path:
            resolved = find_executable("scrcpy")
            if not resolved:
                raise ScrcpyNotFoundError()
            self._scrcpy_path = resolved
        return self._scrcpy_path

    def get_version(self) -> str:
        """Returns the version string of the installed scrcpy binary."""
        if self._cached_version:
            return self._cached_version

        result = run_command([self.scrcpy_path, "--version"], timeout=SCRCPY_VERSION_TIMEOUT)
        if not result.success:
            logger.warning(f"scrcpy --version returned {result.returncode}: {result.stderr}")

        # Typical output: "scrcpy 2.4 <https://github.com/Genymobile/scrcpy>"
        match = re.search(r"scrcpy\s+([0-9\.]+)", result.stdout + " " + result.stderr)
        if match:
            self._cached_version = match.group(1)
        else:
            self._cached_version = "Unknown"

        return self._cached_version

    def check_audio_compatibility(self) -> Tuple[bool, str]:
        """
        Validates if installed scrcpy version supports native audio forwarding.
        Audio capture requires scrcpy >= 2.0.
        """
        version = self.get_version()
        if version == "Unknown":
            return False, "Unable to determine scrcpy version."

        installed_tuple = parse_version_tuple(version)
        min_tuple = parse_version_tuple(MIN_SCRCPY_VERSION)

        if installed_tuple >= min_tuple:
            return True, f"scrcpy {version} supports audio forwarding."
        else:
            return False, f"scrcpy {version} is too old (requires {MIN_SCRCPY_VERSION}+ for audio)."

    def build_command(
        self,
        serial: str,
        settings: AppSettings,
        device_api_level: Optional[int] = None,
        device_name: Optional[str] = None,
    ) -> Tuple[List[str], bool]:
        """
        Builds structured scrcpy argument list.
        Returns:
            Tuple[List[str], bool]: (argument_list, audio_will_forward)
        """
        settings.validate()
        cmd = [self.scrcpy_path, "--serial", serial]

        # Descriptive window title
        title = settings.window_title
        if device_name:
            title = f"{title} - {device_name}"
        cmd.extend(["--window-title", title])

        # Video resolution & performance
        if settings.max_size > 0:
            cmd.extend(["--max-size", str(settings.max_size)])

        if settings.max_fps > 0:
            cmd.extend(["--max-fps", str(settings.max_fps)])

        if settings.video_bitrate:
            # scrcpy 1.x uses --bit-rate, scrcpy 2.0+ uses --video-bit-rate
            version = self.get_version()
            try:
                major = int(version.split(".")[0])
            except (ValueError, AttributeError):
                major = 2
            bitrate_flag = "--bit-rate" if major < 2 else "--video-bit-rate"
            cmd.extend([bitrate_flag, settings.video_bitrate])

        # Behavior toggles
        if settings.fullscreen:
            cmd.append("--fullscreen")

        if settings.stay_awake:
            cmd.append("--stay-awake")

        if settings.turn_screen_off:
            cmd.append("--turn-screen-off")

        if settings.show_touches:
            cmd.append("--show-touches")

        # Audio Forwarding Logic
        audio_supported, _ = self.check_audio_compatibility()
        device_supports_audio = (
            device_api_level is not None and device_api_level >= MIN_ANDROID_AUDIO_API
        ) if device_api_level is not None else True  # If unknown, attempt if enabled

        should_forward_audio = (
            settings.audio_enabled and audio_supported and device_supports_audio
        )

        if should_forward_audio:
            # scrcpy 2.0+ audio options
            cmd.extend([
                f"--audio-source={settings.audio_source}",
                f"--audio-codec={settings.audio_codec}",
            ])
            if settings.require_audio:
                cmd.append("--require-audio")
        else:
            # scrcpy 1.x has no audio support; --no-audio flag only exists in 2.0+
            version = self.get_version()
            try:
                major = int(version.split(".")[0])
            except (ValueError, AttributeError):
                major = 2
            if major >= 2:
                cmd.append("--no-audio")

        logger.info(f"Built scrcpy command for {serial} (audio={should_forward_audio}): {' '.join(cmd)}")
        return cmd, should_forward_audio
