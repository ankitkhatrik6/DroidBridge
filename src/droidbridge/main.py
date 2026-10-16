"""
Command-line and graphical entrypoint for DroidBridge.
"""

import argparse
import os
import sys

from droidbridge.constants import APP_NAME, APP_VERSION
from droidbridge.services.adb_service import AdbService
from droidbridge.services.diagnostics import DiagnosticsService
from droidbridge.utils.logging_setup import setup_logging


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="droidbridge",
        description=f"{APP_NAME} - Native Linux Android USB Screen Mirroring & Audio Forwarding",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"{APP_NAME} {APP_VERSION}",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable detailed debug logging to stdout and state directory",
    )
    parser.add_argument(
        "--diagnostics",
        action="store_true",
        help="Run comprehensive environment diagnostics and print report to stdout",
    )
    parser.add_argument(
        "--list-devices",
        action="store_true",
        help="List currently connected Android devices via ADB",
    )
    parser.add_argument(
        "-s", "--device",
        metavar="SERIAL",
        help="Target specific Android device serial number",
    )
    parser.add_argument(
        "--allow-root",
        action="store_true",
        help="Bypass root user safety check (for CI or container environments)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    logger = setup_logging(debug=args.debug)

    # Security check: Prohibit running GUI as root unless explicitly bypassed for CI
    is_root = hasattr(os, "geteuid") and os.geteuid() == 0
    if is_root and not args.diagnostics and not args.list_devices and not args.allow_root:
        print("Warning: Running DroidBridge GUI as root (superuser) is discouraged for security reasons.", file=sys.stderr)
        print("Please run DroidBridge as a regular desktop user, or pass --allow-root if testing in a container.", file=sys.stderr)
        return 1

    # CLI Diagnostics Mode
    if args.diagnostics:
        diag = DiagnosticsService()
        report = diag.generate_report_text(redact=False)
        print(report)
        return 0

    # CLI List Devices Mode
    if args.list_devices:
        adb = AdbService()
        if not adb.is_available:
            print("Error: adb binary is not installed or not in PATH.", file=sys.stderr)
            return 1
        devices = adb.list_devices()
        if not devices:
            print("No Android devices connected.")
            return 0
        print(f"Connected Android Devices ({len(devices)}):")
        for dev in devices:
            os_info = f" [Android {dev.android_version}]" if dev.android_version else ""
            audio_info = " (Audio Supported)" if dev.supports_audio else " (Audio Unsupported)"
            print(f"  • {dev.serial}\t{dev.state}\t{dev.display_name}{os_info}{audio_info}")
        return 0

    # Launch GTK 4 GUI
    try:
        from droidbridge.application import DroidBridgeApplication, has_gtk
        if not has_gtk:
            print(
                "Error: GTK 4 and PyGObject are required to run the graphical interface.\n"
                "Install them on Debian/Ubuntu with:\n"
                "    sudo apt install python3-gi gir1.2-gtk-4.0",
                file=sys.stderr,
            )
            return 1

        app = DroidBridgeApplication()
        return app.run(sys.argv)
    except Exception as exc:
        logger.exception(f"Unhandled fatal error starting DroidBridge: {exc}")
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
