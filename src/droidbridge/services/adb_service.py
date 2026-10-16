"""
Android Debug Bridge (ADB) service for device discovery, authorization, and inspection.
"""

from dataclasses import dataclass
import logging
import re
from typing import Dict, List, Optional

from droidbridge.constants import ADB_COMMAND_TIMEOUT, ADB_DEVICES_TIMEOUT
from droidbridge.utils.command_runner import find_executable, run_command
from droidbridge.utils.errors import (
    AdbCommandError,
    AdbNotFoundError,
    DeviceOfflineError,
    DeviceUnauthorizedError,
)

logger = logging.getLogger(__name__)


@dataclass
class AdbDevice:
    serial: str
    state: str  # 'device' (authorized), 'unauthorized', 'offline', 'authorizing'
    model: str = "Unknown Device"
    product: str = ""
    device: str = ""
    transport_id: str = ""
    usb_port: str = ""
    android_version: Optional[str] = None
    api_level: Optional[int] = None
    manufacturer: Optional[str] = None
    battery_level: Optional[int] = None

    @property
    def is_authorized(self) -> bool:
        return self.state == "device"

    @property
    def is_unauthorized(self) -> bool:
        return self.state in ["unauthorized", "authorizing"]

    @property
    def is_offline(self) -> bool:
        return self.state == "offline"

    @property
    def supports_audio(self) -> bool:
        """Audio capture via scrcpy requires Android 11 (API level 30) or higher."""
        if not self.is_authorized:
            return False
        if self.api_level is not None:
            return self.api_level >= 30
        return False

    @property
    def display_name(self) -> str:
        clean_model = self.model.replace("_", " ").strip()
        if self.manufacturer and not clean_model.lower().startswith(self.manufacturer.lower()):
            return f"{self.manufacturer} {clean_model}"
        return clean_model or self.serial


class AdbService:
    """Encapsulates all interaction with the ADB binary."""

    def __init__(self, adb_path: Optional[str] = None):
        self._adb_path = adb_path or find_executable("adb")
        self._cached_version: Optional[str] = None

    @property
    def is_available(self) -> bool:
        return self._adb_path is not None

    @property
    def adb_path(self) -> str:
        if not self._adb_path:
            resolved = find_executable("adb")
            if not resolved:
                raise AdbNotFoundError()
            self._adb_path = resolved
        return self._adb_path

    def get_version(self) -> str:
        """Returns the version string reported by adb version."""
        if self._cached_version:
            return self._cached_version

        result = run_command([self.adb_path, "version"], timeout=ADB_COMMAND_TIMEOUT)
        if not result.success:
            raise AdbCommandError("adb version", result.returncode, result.stderr)

        match = re.search(r"Android Debug Bridge version\s+([0-9\.]+)", result.stdout)
        if match:
            self._cached_version = match.group(1)
        else:
            self._cached_version = result.stdout.strip().split("\n")[0]

        return self._cached_version

    def start_server(self) -> bool:
        """Ensures the ADB user daemon is running."""
        result = run_command([self.adb_path, "start-server"], timeout=ADB_COMMAND_TIMEOUT)
        return result.success

    def list_devices(self) -> List[AdbDevice]:
        """
        Executes `adb devices -l` and parses the output into structured AdbDevice objects.
        Does not block indefinitely.
        """
        result = run_command([self.adb_path, "devices", "-l"], timeout=ADB_DEVICES_TIMEOUT)
        if not result.success:
            logger.error(f"Failed to query devices: {result.stderr}")
            return []

        devices: List[AdbDevice] = []
        lines = result.stdout.strip().splitlines()

        for line in lines:
            line = line.strip()
            if not line or line.startswith("*") or line.startswith("List of devices"):
                continue

            parts = line.split()
            if len(parts) < 2:
                continue

            serial = parts[0]
            state = parts[1]

            # Parse key-value attributes (e.g. model:Pixel_8_Pro usb:1-1)
            props: Dict[str, str] = {}
            for item in parts[2:]:
                if ":" in item:
                    k, v = item.split(":", 1)
                    props[k] = v

            device = AdbDevice(
                serial=serial,
                state=state,
                model=props.get("model", "Android Device"),
                product=props.get("product", ""),
                device=props.get("device", ""),
                transport_id=props.get("transport_id", ""),
                usb_port=props.get("usb", ""),
            )

            # Enrich authorized devices with Android OS properties
            if device.is_authorized:
                self._enrich_device_details(device)

            devices.append(device)

        return devices

    def _enrich_device_details(self, device: AdbDevice) -> None:
        """Queries device properties via getprop safely."""
        try:
            # Query OS release and SDK version in a single command
            result = run_command(
                [self.adb_path, "-s", device.serial, "shell", "getprop ro.build.version.release; getprop ro.build.version.sdk; getprop ro.product.manufacturer"],
                timeout=3.0,
            )
            if result.success and result.stdout:
                props = [p.strip() for p in result.stdout.strip().splitlines() if p.strip()]
                if len(props) >= 1 and props[0]:
                    device.android_version = props[0]
                if len(props) >= 2 and props[1].isdigit():
                    device.api_level = int(props[1])
                if len(props) >= 3 and props[2]:
                    device.manufacturer = props[2].capitalize()
        except Exception as exc:
            logger.debug(f"Could not query detailed properties for {device.serial}: {exc}")

    def get_battery_level(self, serial: str) -> Optional[int]:
        """Queries battery level percentage for a device."""
        try:
            result = run_command(
                [self.adb_path, "-s", serial, "shell", "dumpsys", "battery"],
                timeout=3.0,
            )
            if result.success:
                match = re.search(r"level:\s+(\d+)", result.stdout)
                if match:
                    return int(match.group(1))
        except Exception as exc:
            logger.debug(f"Battery query failed for {serial}: {exc}")
        return None

    def reconnect(self, serial: Optional[str] = None) -> bool:
        """Sends adb reconnect command to recover stalled or offline USB sessions."""
        cmd = [self.adb_path]
        if serial:
            cmd.extend(["-s", serial])
        cmd.append("reconnect")
        result = run_command(cmd, timeout=5.0)
        return result.success
