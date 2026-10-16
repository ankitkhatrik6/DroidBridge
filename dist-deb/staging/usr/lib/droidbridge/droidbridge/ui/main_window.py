"""
Primary native GTK 4 application window for DroidBridge.
"""

import logging
from typing import List, Optional

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import GLib, Gtk
except Exception:
    Gtk = None
    GLib = None

from droidbridge.config import ConfigManager
from droidbridge.constants import (
    APP_NAME,
    APP_VERSION,
    ConnectionState,
    MIN_ANDROID_AUDIO_API,
    PRESETS,
)
from droidbridge.services.adb_service import AdbDevice, AdbService
from droidbridge.services.audio_service import AudioService
from droidbridge.services.device_monitor import DeviceMonitor
from droidbridge.services.diagnostics import DiagnosticsService
from droidbridge.services.process_manager import ProcessManager
from droidbridge.services.scrcpy_service import ScrcpyService
from droidbridge.ui.device_card import DeviceCard
from droidbridge.ui.diagnostics_dialog import DiagnosticsDialog
from droidbridge.ui.settings_dialog import SettingsDialog

logger = logging.getLogger(__name__)


class MainWindow:
    """The main desktop control window for DroidBridge."""

    def __init__(
        self,
        application,
        config_manager: ConfigManager,
        adb_service: AdbService,
        scrcpy_service: ScrcpyService,
        process_manager: ProcessManager,
        device_monitor: DeviceMonitor,
        diagnostics_service: DiagnosticsService,
    ):
        self.application = application
        self.config_manager = config_manager
        self.adb_service = adb_service
        self.scrcpy_service = scrcpy_service
        self.process_manager = process_manager
        self.device_monitor = device_monitor
        self.diagnostics_service = diagnostics_service

        self.current_devices: List[AdbDevice] = []
        self.selected_device: Optional[AdbDevice] = None
        self.connection_state: ConnectionState = ConnectionState.CHECKING_DEPENDENCIES

        if Gtk is None:
            self.window = None
            return

        # Main GTK Window
        self.window = Gtk.ApplicationWindow(application=application, title=APP_NAME)
        self.window.set_default_size(540, 600)
        self.window.add_css_class("droidbridge-window")

        # Top HeaderBar
        header = Gtk.HeaderBar()
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        t_label = Gtk.Label(label=APP_NAME)
        t_label.add_css_class("header-title")
        sub_label = Gtk.Label(label=f"v{APP_VERSION} · Linux USB Mirroring")
        sub_label.add_css_class("header-subtitle")
        title_box.append(t_label)
        title_box.append(sub_label)
        header.set_title_widget(title_box)

        # Header action buttons
        diag_btn = Gtk.Button(label="Diagnostics")
        diag_btn.connect("clicked", self._on_open_diagnostics)
        header.pack_end(diag_btn)

        settings_btn = Gtk.Button(label="Settings")
        settings_btn.connect("clicked", self._on_open_settings)
        header.pack_end(settings_btn)

        self.window.set_titlebar(header)

        # Main Layout Box
        content_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=14)
        content_box.set_margin_top(16)
        content_box.set_margin_bottom(16)
        content_box.set_margin_start(16)
        content_box.set_margin_end(16)
        self.window.set_child(content_box)

        # 1. Device Selector (When multiple devices are connected)
        self.selector_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.selector_box.set_visible(False)
        self.selector_label = Gtk.Label(label="Selected Device:", xalign=0.0)
        self.selector_dropdown = Gtk.DropDown()
        self.selector_dropdown.connect("notify::selected", self._on_device_selected_from_dropdown)
        self.selector_box.append(self.selector_label)
        self.selector_box.append(self.selector_dropdown)
        content_box.append(self.selector_box)

        # 2. Connected Device Card
        self.device_card = DeviceCard()
        if self.device_card.widget:
            content_box.append(self.device_card.widget)

        # 3. Informational Notification Banner
        self.banner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.banner_box.add_css_class("info-banner")
        self.banner_label = Gtk.Label(xalign=0.0)
        self.banner_label.set_wrap(True)
        self.banner_box.append(self.banner_label)
        self.banner_box.set_visible(False)
        content_box.append(self.banner_box)

        # 4. Performance Preset Switcher
        preset_title = Gtk.Label(label="Performance Preset", xalign=0.0)
        preset_title.add_css_class("header-title")
        content_box.append(preset_title)

        self.preset_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.preset_buttons = {}
        for p_id, p_info in PRESETS.items():
            btn = Gtk.Button(label=p_info["name"])
            btn.add_css_class("preset-button")
            btn.set_hexpand(True)
            btn.connect("clicked", self._make_preset_handler(p_id))
            self.preset_box.append(btn)
            self.preset_buttons[p_id] = btn
        content_box.append(self.preset_box)

        # 5. Audio Forwarding Status Line
        self.audio_status_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.audio_status_label = Gtk.Label(xalign=0.0)
        self.audio_status_label.set_hexpand(True)
        self.audio_status_label.add_css_class("device-meta")
        self.audio_status_row.append(self.audio_status_label)
        content_box.append(self.audio_status_row)

        # Spacer
        spacer = Gtk.Box()
        spacer.set_vexpand(True)
        content_box.append(spacer)

        # 6. Primary Action Buttons
        self.action_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.action_box.set_halign(Gtk.Align.FILL)

        self.start_btn = Gtk.Button(label="Start Mirroring")
        self.start_btn.add_css_class("btn-primary-action")
        self.start_btn.set_hexpand(True)
        self.start_btn.connect("clicked", self._on_start_clicked)
        self.action_box.append(self.start_btn)

        self.stop_btn = Gtk.Button(label="Stop Session")
        self.stop_btn.add_css_class("btn-stop-action")
        self.stop_btn.connect("clicked", self._on_stop_clicked)
        self.stop_btn.set_visible(False)
        self.action_box.append(self.stop_btn)

        self.restart_btn = Gtk.Button(label="Restart")
        self.restart_btn.connect("clicked", self._on_restart_clicked)
        self.restart_btn.set_visible(False)
        self.action_box.append(self.restart_btn)

        content_box.append(self.action_box)

        # Wire callbacks
        self.device_monitor.on_devices_updated = self.on_devices_updated
        self.process_manager.on_state_changed = self.on_process_state_changed
        self.process_manager.on_audio_failure = self.on_audio_failure_detected

    def show(self) -> None:
        """Show the main window."""
        if self.window:
            self.window.show()

    # --- preset handling ---
    def _make_preset_handler(self, p_id: str):
        def handler(button):
            self.config_manager.settings.apply_preset(p_id)
            self.config_manager.save()
            self.update_audio_status_line()
        return handler

    # --- device / state updates ---
    def update_action_controls(self) -> None:
        """Enables or disables action buttons based on current state."""
        running = self.process_manager.is_running
        has_authorized_device = self.selected_device is not None and self.selected_device.is_authorized

        self.start_btn.set_visible(not running)
        self.stop_btn.set_visible(running)
        self.restart_btn.set_visible(running)

        self.start_btn.set_sensitive(has_authorized_device and not running)

    def _on_start_clicked(self, button) -> None:
        """Validates settings and launches scrcpy session."""
        if not self.selected_device or not self.selected_device.is_authorized:
            return

        cmd, forwards_audio = self.scrcpy_service.build_command(
            serial=self.selected_device.serial,
            settings=self.config_manager.settings,
            device_api_level=self.selected_device.api_level,
            device_name=self.selected_device.display_name,
        )

        success = self.process_manager.start_session(cmd, self.selected_device.serial)
        if success:
            self.connection_state = ConnectionState.MIRRORING_ACTIVE
            msg = "Screen mirroring active in separate window."
            if forwards_audio:
                msg += " Audio forwarded to PC speakers."
            else:
                msg += " (Audio not forwarded)."
            self.set_banner(msg, level="active")
            self.update_action_controls()

    def _on_stop_clicked(self, button) -> None:
        """Stops active scrcpy session."""
        self.process_manager.stop_session()
        self.update_action_controls()
        self.set_banner("Mirroring session stopped.", level="warning")

    def _on_restart_clicked(self, button) -> None:
        """Restarts active session."""
        self._on_stop_clicked(button)
        if GLib is not None:
            GLib.timeout_add(600, lambda: self._on_start_clicked(self.start_btn))
        else:
            self._on_start_clicked(self.start_btn)

    def on_process_state_changed(self, state: ConnectionState, message: str) -> None:
        """Callback from ProcessManager."""
        self.connection_state = state
        self.update_action_controls()
        if state == ConnectionState.MIRRORING_ACTIVE:
            self.set_banner(message, level="active")
        elif state == ConnectionState.SESSION_STOPPED:
            self.set_banner(message, level="warning")
        elif state == ConnectionState.RECOVERABLE_ERROR:
            self.set_banner(f"Session Error: {message}", level="error")

    def on_audio_failure_detected(self, stderr_line: str) -> None:
        """Handles scrcpy audio failure during active session."""
        self.set_banner(
            f"Audio capture failed: {stderr_line}. Screen mirroring remains active. (Ensure phone is unlocked).",
            level="warning",
        )

    def _on_open_settings(self, button) -> None:
        dialog = SettingsDialog(self.window, self.config_manager, on_saved=self.update_audio_status_line)
        dialog.show()

    def _on_open_diagnostics(self, button) -> None:
        dialog = DiagnosticsDialog(self.window, self.diagnostics_service)
        dialog.show()

    def _on_close_request(self, window) -> bool:
        """Clean shutdown handler."""
        logger.info("Main window close requested. Cleaning up...")
        self.device_monitor.stop()
        self.process_manager.stop_session()
        return False

    # --- banner / audio / device callbacks ---
    def set_banner(self, text: Optional[str], level: str = "warning") -> None:
        """Displays or hides the non-blocking informational banner."""
        if not text:
            self.banner_box.set_visible(False)
            return

        self.banner_box.set_visible(True)
        self.banner_label.set_text(text)
        for cls in ["info-banner-warning", "info-banner-error", "info-banner-active"]:
            self.banner_box.remove_css_class(cls)

        if level == "error":
            self.banner_box.add_css_class("info-banner-error")
        elif level == "active":
            self.banner_box.add_css_class("info-banner-active")
        else:
            self.banner_box.add_css_class("info-banner-warning")

    def on_devices_updated(self, devices: List[AdbDevice]) -> None:
        """Callback from DeviceMonitor when USB topology changes."""
        self.current_devices = devices

        # Update device selector dropdown if > 1 device
        if len(devices) > 1:
            self.selector_box.set_visible(True)
            strings = [f"{d.display_name} ({d.state})" for d in devices]
            model = Gtk.StringList.new(strings)
            self.selector_dropdown.set_model(model)
        else:
            self.selector_box.set_visible(False)

        # Select first or preserve active selection
        if devices:
            if self.selected_device:
                matched = next((d for d in devices if d.serial == self.selected_device.serial), None)
                self.selected_device = matched or devices[0]
            else:
                self.selected_device = devices[0]
        else:
            self.selected_device = None

        self.device_card.update_device(self.selected_device)
        self.update_action_controls()
        self.update_audio_status_line()

        # Handle specific connection states
        if not devices:
            self.connection_state = ConnectionState.WAITING_FOR_DEVICE
            self.set_banner(None)
        elif self.selected_device and self.selected_device.is_unauthorized:
            self.connection_state = ConnectionState.AUTHORIZATION_REQUIRED
            self.set_banner(
                "Phone is locked or unauthorized. Please unlock screen, check 'Always allow from this computer', and tap 'Allow'.",
                level="warning",
            )
        elif self.selected_device and self.selected_device.is_offline:
            self.connection_state = ConnectionState.DEVICE_OFFLINE
            self.set_banner("Device is offline. Please reconnect USB cable.", level="error")
        elif self.process_manager.is_running:
            self.connection_state = ConnectionState.MIRRORING_ACTIVE
        else:
            self.connection_state = ConnectionState.DEVICE_DETECTED
            # Check audio capability warning banner
            if self.selected_device and not self.selected_device.supports_audio:
                self.set_banner(
                    "Note: Device runs Android 10 or earlier. Screen mirroring will start without audio forwarding.",
                    level="warning",
                )
            else:
                self.set_banner(None)

    def _on_device_selected_from_dropdown(self, dropdown, param) -> None:
        idx = dropdown.get_selected()
        if 0 <= idx < len(self.current_devices):
            self.selected_device = self.current_devices[idx]
            self.device_card.update_device(self.selected_device)
            self.update_action_controls()
            self.update_audio_status_line()

    def update_audio_status_line(self) -> None:
        """Updates the audio forwarding status text."""
        if not self.selected_device:
            self.audio_status_label.set_text("")
            return
        if self.config_manager.settings.audio_enabled:
            if self.selected_device.supports_audio:
                self.audio_status_label.set_text("Audio forwarding: Enabled")
            else:
                self.audio_status_label.set_text("Audio forwarding: Not supported on this device")
        else:
            self.audio_status_label.set_text("Audio forwarding: Disabled")
