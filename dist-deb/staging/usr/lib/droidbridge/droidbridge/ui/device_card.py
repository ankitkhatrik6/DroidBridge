"""
Native GTK 4 device card widget displaying USB connection status and capabilities.
"""

from typing import Optional

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk
except Exception:
    Gtk = None

from droidbridge.services.adb_service import AdbDevice
from droidbridge.utils.logging_setup import redact_text


class DeviceCard:
    """Encapsulates the connected Android device display widget."""

    def __init__(self):
        if Gtk is None:
            self.widget = None
            return

        self.widget = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.widget.add_css_class("device-card")

        # Top row: Device name and Status Badge
        self.header_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        self.header_box.set_hexpand(True)

        self.title_label = Gtk.Label(xalign=0.0)
        self.title_label.add_css_class("device-title")
        self.title_label.set_hexpand(True)
        self.header_box.append(self.title_label)

        self.status_badge = Gtk.Label()
        self.status_badge.add_css_class("status-badge")
        self.header_box.append(self.status_badge)

        self.widget.append(self.header_box)

        # Meta row: Serial and USB Port
        self.meta_label = Gtk.Label(xalign=0.0)
        self.meta_label.add_css_class("device-meta")
        self.widget.append(self.meta_label)

        # Capabilities row: OS version and Audio Forwarding badge
        self.caps_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        self.caps_box.set_margin_top(4)

        self.os_label = Gtk.Label(xalign=0.0)
        self.os_label.add_css_class("device-meta")
        self.caps_box.append(self.os_label)

        self.audio_badge = Gtk.Label(xalign=0.0)
        self.audio_badge.add_css_class("device-meta")
        self.caps_box.append(self.audio_badge)

        self.widget.append(self.caps_box)

        # Empty state by default
        self.show_empty_state()

    def update_device(self, device: Optional[AdbDevice]) -> None:
        """Updates the card with real device properties."""
        if self.widget is None:
            return

        if device is None:
            self.show_empty_state()
            return

        self.widget.remove_css_class("device-card-empty")
        self.header_box.set_visible(True)
        self.meta_label.set_visible(True)
        self.caps_box.set_visible(True)

        self.title_label.set_text(device.display_name)
        masked_serial = redact_text(device.serial)
        usb_info = f" · USB port {device.usb_port}" if device.usb_port else ""
        self.meta_label.set_text(f"Serial: {masked_serial}{usb_info}")

        # Status badge styling
        for cls in ["status-authorized", "status-unauthorized", "status-offline", "status-active"]:
            self.status_badge.remove_css_class(cls)

        if device.is_authorized:
            self.status_badge.set_text("Authorized")
            self.status_badge.add_css_class("status-authorized")
        elif device.is_unauthorized:
            self.status_badge.set_text("Authorization Required")
            self.status_badge.add_css_class("status-unauthorized")
        elif device.is_offline:
            self.status_badge.set_text("Offline")
            self.status_badge.add_css_class("status-offline")
        else:
            self.status_badge.set_text(device.state.capitalize())

        # OS and Audio Capability
        if device.android_version:
            api = device.api_level or "?"
            self.os_label.set_text(f"Android {device.android_version} (API {api})")
        else:
            self.os_label.set_text("OS Version: Pending authorization")

        if device.is_authorized:
            if device.supports_audio:
                self.audio_badge.set_text("Audio: Supported (Android 11+)")
            else:
                self.audio_badge.set_text("Audio: Video Only (Android < 11)")
        else:
            self.audio_badge.set_text("Audio: Unknown")

    def show_empty_state(self) -> None:
        """Renders the empty waiting-for-device state."""
        if self.widget is None:
            return

        self.widget.add_css_class("device-card-empty")
        self.title_label.set_text("No Android Device Connected")
        self.status_badge.set_text("Waiting for USB Connection")
        for cls in ["status-authorized", "status-unauthorized", "status-offline", "status-active"]:
            self.status_badge.remove_css_class(cls)

        self.meta_label.set_text("Connect your phone with a USB data cable and enable USB debugging.")
        self.caps_box.set_visible(False)
