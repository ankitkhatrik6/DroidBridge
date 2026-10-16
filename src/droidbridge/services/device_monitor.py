"""
Non-blocking background device monitor and connection state watcher.
"""

import logging
import threading
import time
from typing import Callable, List, Optional

from droidbridge.constants import DEVICE_POLL_INTERVAL_SECONDS
from droidbridge.services.adb_service import AdbDevice, AdbService

logger = logging.getLogger(__name__)


class DeviceMonitor:
    """Watches USB ADB device topology changes without blocking the GUI main loop."""

    def __init__(self, adb_service: Optional[AdbService] = None):
        self.adb_service = adb_service or AdbService()
        self._thread: Optional[threading.Thread] = None
        self._running = False
        self._cached_devices: List[AdbDevice] = []
        self._lock = threading.Lock()

        # Callbacks
        self.on_devices_updated: Optional[Callable[[List[AdbDevice]], None]] = None

    @property
    def is_running(self) -> bool:
        return self._running

    def start(self) -> None:
        """Starts the background device polling thread."""
        with self._lock:
            if self._running:
                return
            self._running = True

        self._thread = threading.Thread(
            target=self._polling_loop,
            daemon=True,
            name="DroidBridgeDeviceMonitor",
        )
        self._thread.start()
        logger.info("Device monitor polling thread started.")

    def stop(self) -> None:
        """Stops device polling gracefully."""
        with self._lock:
            self._running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
        logger.info("Device monitor stopped.")

    def refresh_now(self) -> List[AdbDevice]:
        """Performs an immediate device scan."""
        try:
            if not self.adb_service.is_available:
                return []
            devices = self.adb_service.list_devices()
            with self._lock:
                self._cached_devices = devices
            self._dispatch_update(devices)
            return devices
        except Exception as exc:
            logger.error(f"Error refreshing devices: {exc}")
            return []

    def get_cached_devices(self) -> List[AdbDevice]:
        with self._lock:
            return list(self._cached_devices)

    def _polling_loop(self) -> None:
        """Internal polling loop with differential change detection."""
        last_signature = ""

        while self._running:
            try:
                if self.adb_service.is_available:
                    devices = self.adb_service.list_devices()
                    with self._lock:
                        self._cached_devices = devices

                    # Create a quick signature to detect changes
                    sig = ",".join(f"{d.serial}:{d.state}:{d.model}" for d in devices)
                    if sig != last_signature:
                        last_signature = sig
                        self._dispatch_update(devices)
            except Exception as exc:
                logger.debug(f"Device monitor poll error: {exc}")

            # Sleep in small slices so thread terminates quickly on stop()
            for _ in range(int(DEVICE_POLL_INTERVAL_SECONDS * 10)):
                if not self._running:
                    break
                time.sleep(0.1)

    def _dispatch_update(self, devices: List[AdbDevice]) -> None:
        """Safely dispatches device updates to the UI main loop."""
        if not self.on_devices_updated:
            return

        # Attempt to use GLib.idle_add for thread safety in GTK apps
        try:
            import gi
            from gi.repository import GLib
            GLib.idle_add(self.on_devices_updated, devices)
        except Exception:
            # Fallback for headless CLI or tests
            self.on_devices_updated(devices)
