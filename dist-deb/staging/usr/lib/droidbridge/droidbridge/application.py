"""
Application lifecycle manager for DroidBridge with libadwaita and standard GTK 4 support.
"""

import logging
import os
from pathlib import Path
import signal
import sys
from typing import Optional

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gdk, Gio, GLib, Gtk
    has_gtk = True
except Exception:
    has_gtk = False
    Gtk = None

# Attempt libadwaita integration
has_adw = False
Adw = None
try:
    import gi
    gi.require_version("Adw", "1")
    from gi.repository import Adw
    has_adw = True
except Exception:
    pass

from droidbridge.config import ConfigManager
from droidbridge.constants import APP_ID, APP_NAME, APP_VERSION
from droidbridge.services.adb_service import AdbService
from droidbridge.services.device_monitor import DeviceMonitor
from droidbridge.services.diagnostics import DiagnosticsService
from droidbridge.services.process_manager import ProcessManager
from droidbridge.services.scrcpy_service import ScrcpyService
from droidbridge.ui.main_window import MainWindow

logger = logging.getLogger(__name__)


def get_base_application_class():
    if has_adw and Adw is not None:
        return Adw.Application
    elif has_gtk and Gtk is not None:
        return Gtk.Application
    return object


BaseApp = get_base_application_class()


class DroidBridgeApplication(BaseApp):
    """Primary application controller handling window lifecycle, CSS, and services."""

    def __init__(self):
        if not has_gtk:
            logger.error("GTK 4 is not available in the current environment.")
            return

        super().__init__(
            application_id=APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE,
        )

        self.config_manager = ConfigManager()
        self.adb_service = AdbService()
        self.scrcpy_service = ScrcpyService()
        self.process_manager = ProcessManager()
        self.device_monitor = DeviceMonitor(self.adb_service)
        self.diagnostics_service = DiagnosticsService(self.adb_service, self.scrcpy_service)

        self.main_window: Optional[MainWindow] = None

    def do_startup(self) -> None:
        """GTK application startup hook."""
        BaseApp.do_startup(self)
        logger.info(f"Starting {APP_NAME} v{APP_VERSION}...")

        # Load custom CSS
        self._load_styles()

        # Connect OS shutdown signals
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, self._on_unix_signal, signal.SIGINT)
        GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGTERM, self._on_unix_signal, signal.SIGTERM)

        # Start background device monitor so connected USB devices are detected
        if self.device_monitor:
            self.device_monitor.start()

    def do_activate(self) -> None:
        """GTK activate hook: constructs or presents the main window."""
        if not self.main_window:
            self.main_window = MainWindow(
                application=self,
                config_manager=self.config_manager,
                adb_service=self.adb_service,
                scrcpy_service=self.scrcpy_service,
                process_manager=self.process_manager,
                device_monitor=self.device_monitor,
                diagnostics_service=self.diagnostics_service,
            )

        self.main_window.show()

    def _load_styles(self) -> None:
        """Loads styles.css into the GTK display provider."""
        try:
            css_path = Path(__file__).parent / "ui" / "styles.css"
            if css_path.exists():
                provider = Gtk.CssProvider()
                provider.load_from_path(str(css_path))
                display = Gdk.Display.get_default()
                if display:
                    Gtk.StyleContext.add_provider_for_display(
                        display,
                        provider,
                        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
                    )
                logger.debug("Applied application styles.css.")
        except Exception as exc:
            logger.warning(f"Could not load custom styles.css: {exc}")

    def _on_unix_signal(self, signum: int) -> bool:
        """Handles terminal interrupt/terminate signals cleanly."""
        logger.info(f"Received signal {signum}, initiating graceful shutdown...")
        if self.device_monitor:
            self.device_monitor.stop()
        if self.process_manager:
            self.process_manager.cleanup_all()
        self.quit()
        return GLib.SOURCE_REMOVE

# Device monitor ensures USB devices are detected on app launch
