"""
Structured custom exceptions with actionable user recovery hints for DroidBridge.
"""

from typing import Optional


class DroidBridgeError(Exception):
    """Base exception for all DroidBridge errors."""

    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.recovery_hint = recovery_hint or "Check your system dependencies and USB connection."

    def __str__(self) -> str:
        if self.recovery_hint:
            return f"{self.message}\nAction: {self.recovery_hint}"
        return self.message


class AdbNotFoundError(DroidBridgeError):
    """Raised when ADB is missing or not executable on the system PATH."""

    def __init__(self, path: Optional[str] = None):
        super().__init__(
            message="Android Debug Bridge (adb) was not found on your system PATH.",
            recovery_hint="Install ADB via your package manager: 'sudo apt install adb' or 'sudo apt install android-tools-adb'.",
        )
        self.path = path


class AdbCommandError(DroidBridgeError):
    """Raised when an ADB command fails or returns a non-zero exit code."""

    def __init__(self, command: str, returncode: int, stderr: str):
        super().__init__(
            message=f"ADB command failed with exit code {returncode}: {command}",
            recovery_hint=f"ADB error output: {stderr.strip() if stderr else 'Unknown error'}. Restart the ADB server via 'adb kill-server && adb start-server'.",
        )
        self.command = command
        self.returncode = returncode
        self.stderr = stderr


class DeviceUnauthorizedError(DroidBridgeError):
    """Raised when the connected Android device has not accepted USB debugging authorization."""

    def __init__(self, serial: str):
        super().__init__(
            message=f"Android device {serial} is unauthorized.",
            recovery_hint="Unlock your phone screen, check for the 'Allow USB debugging?' dialog, check 'Always allow from this computer', and tap 'Allow'.",
        )
        self.serial = serial


class DeviceOfflineError(DroidBridgeError):
    """Raised when the device reports an offline status to ADB."""

    def __init__(self, serial: str):
        super().__init__(
            message=f"Android device {serial} is offline.",
            recovery_hint="Unplug and replug the USB data cable, ensure a high-speed data-capable cable is used, or run 'adb reconnect'.",
        )
        self.serial = serial


class ScrcpyNotFoundError(DroidBridgeError):
    """Raised when the scrcpy binary is not found on the system PATH."""

    def __init__(self):
        super().__init__(
            message="scrcpy binary was not found on your system PATH.",
            recovery_hint="Install scrcpy 2.0+ via 'sudo apt install scrcpy' or install the official DroidBridge Debian package.",
        )


class ScrcpyIncompatibleVersionError(DroidBridgeError):
    """Raised when installed scrcpy version is older than required."""

    def __init__(self, installed_version: str, min_version: str = "2.0"):
        super().__init__(
            message=f"Installed scrcpy version ({installed_version}) does not meet the minimum requirement ({min_version}+).",
            recovery_hint="Audio forwarding requires scrcpy 2.0 or higher. Please upgrade scrcpy via your package manager or snap.",
        )
        self.installed_version = installed_version
        self.min_version = min_version


class ScrcpyExecutionError(DroidBridgeError):
    """Raised when scrcpy encounters a startup failure or unexpected crash."""

    def __init__(self, returncode: int, stderr: str):
        super().__init__(
            message=f"scrcpy exited unexpectedly with code {returncode}.",
            recovery_hint=f"Check scrcpy logs: {stderr.strip() if stderr else 'No error detail available'}.",
        )
        self.returncode = returncode
        self.stderr = stderr


class AudioForwardingError(DroidBridgeError):
    """Raised when audio forwarding fails during session startup."""

    def __init__(self, reason: str, recovery_hint: Optional[str] = None):
        super().__init__(
            message=f"Audio forwarding failed: {reason}",
            recovery_hint=recovery_hint or "Android 11+ is required. Ensure the phone screen was unlocked when starting the session.",
        )
