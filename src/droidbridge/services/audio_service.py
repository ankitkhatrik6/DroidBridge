"""
Audio capability analysis and host sound system inspection for DroidBridge.
"""

from dataclasses import dataclass
import logging
from typing import Optional, Tuple

from droidbridge.constants import AudioStatus, MIN_ANDROID_AUDIO_API
from droidbridge.utils.command_runner import find_executable, run_command

logger = logging.getLogger(__name__)


@dataclass
class AudioCapability:
    status: AudioStatus
    is_supported: bool
    title: str
    message: str
    action_hint: Optional[str] = None


class AudioService:
    """Evaluates host and device capabilities for Android audio forwarding."""

    @staticmethod
    def inspect_host_sound_system() -> Tuple[bool, str]:
        """Checks for PipeWire, PulseAudio, or ALSA presence on the host."""
        # 1. PipeWire
        if find_executable("pipewire"):
            res = run_command(["pactl", "info"], timeout=2.0)
            if res.success and "PipeWire" in res.stdout:
                return True, "PipeWire (PulseAudio emulation layer active)"
            return True, "PipeWire sound server detected"

        # 2. PulseAudio
        if find_executable("pulseaudio") or find_executable("pactl"):
            res = run_command(["pactl", "info"], timeout=2.0)
            if res.success:
                return True, "PulseAudio sound server active"
            return True, "PulseAudio installed"

        # 3. ALSA fallback
        if find_executable("aplay"):
            return True, "ALSA Linux sound architecture available"

        return False, "No active audio server (PipeWire/PulseAudio) detected on host."

    @staticmethod
    def evaluate_device_audio(
        api_level: Optional[int],
        scrcpy_audio_supported: bool,
        scrcpy_version: str,
        user_enabled: bool = True,
    ) -> AudioCapability:
        """
        Determines the expected audio forwarding capability based on Android version and scrcpy.
        """
        if not user_enabled:
            return AudioCapability(
                status=AudioStatus.DISABLED_BY_USER,
                is_supported=False,
                title="Audio Disabled",
                message="Audio forwarding is disabled in DroidBridge settings.",
                action_hint="Enable 'Forward Device Audio' in Settings to stream phone sound.",
            )

        if not scrcpy_audio_supported:
            return AudioCapability(
                status=AudioStatus.UNSUPPORTED_SCRCPY,
                is_supported=False,
                title="scrcpy 2.0+ Required for Audio",
                message=f"Installed scrcpy version ({scrcpy_version}) does not support audio capture.",
                action_hint="Upgrade scrcpy to version 2.0 or newer to enable audio forwarding.",
            )

        if api_level is not None and api_level < MIN_ANDROID_AUDIO_API:
            return AudioCapability(
                status=AudioStatus.UNSUPPORTED_ANDROID,
                is_supported=False,
                title="Android 11+ Required",
                message=f"Device API level {api_level} (Android 10 or earlier) cannot forward audio natively.",
                action_hint="Screen mirroring will proceed normally without audio. Audio capture requires Android 11+.",
            )

        # Android 11+ with scrcpy 2.0+
        return AudioCapability(
            status=AudioStatus.STREAMING,
            is_supported=True,
            title="Audio Supported",
            message="Internal audio will forward to host speakers using low-latency Opus codec.",
            action_hint="Note: If audio fails to start, ensure the phone is unlocked during session launch.",
        )
