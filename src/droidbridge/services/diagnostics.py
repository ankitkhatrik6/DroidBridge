"""
Comprehensive system diagnostics and environment health checking service.
"""

from dataclasses import dataclass
import os
import platform
import sys
from typing import Dict, List, Optional, Tuple

from droidbridge.constants import APP_NAME, APP_VERSION, MIN_SCRCPY_VERSION
from droidbridge.services.adb_service import AdbDevice, AdbService
from droidbridge.services.audio_service import AudioService
from droidbridge.services.scrcpy_service import ScrcpyService
from droidbridge.utils.command_runner import find_executable
from droidbridge.utils.logging_setup import redact_text


@dataclass
class DiagnosticCheck:
    id: str
    name: str
    passed: bool
    status_text: str
    details: str
    action_hint: Optional[str] = None


class DiagnosticsService:
    """Runs all environmental and dependency checks for DroidBridge."""

    def __init__(self, adb_service: Optional[AdbService] = None, scrcpy_service: Optional[ScrcpyService] = None):
        self.adb_service = adb_service or AdbService()
        self.scrcpy_service = scrcpy_service or ScrcpyService()

    def run_all_checks(self, devices: Optional[List[AdbDevice]] = None) -> List[DiagnosticCheck]:
        checks: List[DiagnosticCheck] = []

        # 1. Python Environment
        py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        py_pass = sys.version_info >= (3, 9)
        checks.append(
            DiagnosticCheck(
                id="python_runtime",
                name="Python Runtime",
                passed=py_pass,
                status_text=f"Python {py_ver}",
                details=f"Executable: {sys.executable}\nOS: {platform.system()} {platform.release()} ({platform.machine()})",
                action_hint=None if py_pass else "Upgrade to Python 3.9 or newer.",
            )
        )

        # 2. GTK 4 and PyGObject
        gtk4_available = False
        adw_available = False
        gtk_details = []
        try:
            import gi
            gi.require_version("Gtk", "4.0")
            from gi.repository import Gtk
            gtk4_available = True
            gtk_details.append(f"GTK 4: Available (PyGObject {gi.__version__})")
        except Exception as exc:
            gtk_details.append(f"GTK 4: Missing or load error ({exc})")

        try:
            import gi
            gi.require_version("Adw", "1")
            from gi.repository import Adw
            adw_available = True
            gtk_details.append("libadwaita: Available (Adw 1.x)")
        except Exception:
            gtk_details.append("libadwaita: Not installed (using native GTK 4 fallback)")

        checks.append(
            DiagnosticCheck(
                id="gui_toolkit",
                name="Desktop GUI Toolkit",
                passed=gtk4_available or ("gi" in sys.modules),
                status_text="GTK 4 / libadwaita" if adw_available else ("GTK 4" if gtk4_available else "Not loaded"),
                details="\n".join(gtk_details),
                action_hint=None if gtk4_available else "Install 'python3-gi' and 'gir1.2-gtk-4.0' via apt.",
            )
        )

        # 3. ADB Binary & Version
        adb_path = getattr(self.adb_service, "_adb_path", None) or find_executable("adb")
        adb_pass = adb_path is not None
        adb_ver = "Not installed"
        adb_details = f"Path: {adb_path or 'Not found in PATH'}"
        if adb_pass:
            try:
                adb_ver = self.adb_service.get_version()
                adb_details += f"\nVersion: {adb_ver}"
            except Exception as exc:
                adb_details += f"\nError querying version: {exc}"

        checks.append(
            DiagnosticCheck(
                id="adb_binary",
                name="Android Debug Bridge (ADB)",
                passed=adb_pass,
                status_text=f"ADB {adb_ver}" if adb_pass else "Not Found",
                details=adb_details,
                action_hint=None if adb_pass else "Install ADB: 'sudo apt install adb' or 'sudo apt install android-tools-adb'.",
            )
        )

        # 4. scrcpy Binary & Audio Support
        scrcpy_path = getattr(self.scrcpy_service, "_scrcpy_path", None) or find_executable("scrcpy")
        scrcpy_pass = scrcpy_path is not None
        scrcpy_ver = "Not installed"
        scrcpy_audio = False
        scrcpy_msg = ""
        scrcpy_details = f"Path: {scrcpy_path or 'Not found in PATH'}"

        if scrcpy_pass:
            try:
                scrcpy_ver = self.scrcpy_service.get_version()
                scrcpy_audio, scrcpy_msg = self.scrcpy_service.check_audio_compatibility()
                scrcpy_details += f"\nVersion: {scrcpy_ver}\nAudio Forwarding Support: {'Yes' if scrcpy_audio else 'No'}"
                if scrcpy_msg:
                    scrcpy_details += f" ({scrcpy_msg})"
            except Exception as exc:
                scrcpy_details += f"\nError: {exc}"

        checks.append(
            DiagnosticCheck(
                id="scrcpy_binary",
                name="scrcpy Engine",
                passed=scrcpy_pass,
                status_text=f"scrcpy {scrcpy_ver}" if scrcpy_pass else "Not Found",
                details=scrcpy_details,
                action_hint=None if (scrcpy_pass and scrcpy_audio) else (
                    f"Upgrade scrcpy to {MIN_SCRCPY_VERSION}+ for audio: 'sudo apt install scrcpy' or via official PPA/snap."
                    if scrcpy_pass else "Install scrcpy: 'sudo apt install scrcpy'."
                ),
            )
        )

        # 5. Host Audio System
        sound_ok, sound_desc = AudioService.inspect_host_sound_system()
        checks.append(
            DiagnosticCheck(
                id="host_audio",
                name="Host Sound System",
                passed=sound_ok,
                status_text="Active" if sound_ok else "Not Detected",
                details=sound_desc,
                action_hint=None if sound_ok else "Ensure PipeWire or PulseAudio is running on your Linux desktop.",
            )
        )

        # 6. Connected Android Devices & Authorization
        dev_list = devices if devices is not None else (self.adb_service.list_devices() if adb_pass else [])
        if not dev_list:
            checks.append(
                DiagnosticCheck(
                    id="usb_device",
                    name="Connected Devices",
                    passed=False,
                    status_text="No Device Detected",
                    details="No Android devices visible via 'adb devices'.",
                    action_hint="1. Connect phone with a data-capable USB cable.\n2. Enable Developer options (tap Build Number 7 times).\n3. Turn on 'USB debugging'.",
                )
            )
        else:
            authorized_count = sum(1 for d in dev_list if d.is_authorized)
            unauth_count = sum(1 for d in dev_list if d.is_unauthorized)
            offline_count = sum(1 for d in dev_list if d.is_offline)

            status_summary = f"{len(dev_list)} device(s) connected: {authorized_count} authorized"
            dev_lines = []
            hint = None

            for dev in dev_list:
                masked_serial = redact_text(dev.serial)
                dev_lines.append(f"• {dev.display_name} [{masked_serial}] - State: {dev.state.upper()}")
                if dev.android_version:
                    dev_lines.append(f"  OS: Android {dev.android_version} (API {dev.api_level})")
                if dev.is_unauthorized:
                    hint = "Unlock phone screen, check 'Always allow from this computer', and tap 'Allow'."
                elif dev.is_offline:
                    hint = "Device is offline. Reconnect USB cable or run 'adb reconnect'."

            checks.append(
                DiagnosticCheck(
                    id="usb_device",
                    name="Connected Devices",
                    passed=authorized_count > 0,
                    status_text=status_summary,
                    details="\n".join(dev_lines),
                    action_hint=hint,
                )
            )

        return checks

    def generate_report_text(self, redact: bool = True) -> str:
        """Produces a clean diagnostic report suitable for copying to clipboard or bug reports."""
        checks = self.run_all_checks()
        lines = [
            f"=== {APP_NAME} v{APP_VERSION} Diagnostic Report ===",
            f"OS: {platform.system()} {platform.release()} ({platform.machine()})",
            f"Python: {platform.python_version()}",
            "--------------------------------------------------",
        ]

        for check in checks:
            mark = "[PASS]" if check.passed else "[WARN/FAIL]"
            lines.append(f"{mark} {check.name}: {check.status_text}")
            for detail_line in check.details.strip().splitlines():
                lines.append(f"    {detail_line}")
            if check.action_hint:
                lines.append(f"    Action Hint: {check.action_hint}")
            lines.append("")

        report = "\n".join(lines)
        if redact:
            report = redact_text(report)
        return report
