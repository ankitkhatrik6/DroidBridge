"""
System diagnostics dialog displaying environment health checks and clipboard export.
"""

from typing import List, Optional

try:
    import gi
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")
    from gi.repository import Gdk, Gtk
except Exception:
    Gtk = None
    Gdk = None

from droidbridge.services.diagnostics import DiagnosticCheck, DiagnosticsService


class DiagnosticsDialog:
    """Provides visual environment verification and diagnostic export."""

    def __init__(self, parent_window, diagnostics_service: DiagnosticsService):
        self.diagnostics_service = diagnostics_service

        if Gtk is None:
            self.dialog = None
            return

        self.dialog = Gtk.Window(title="DroidBridge Diagnostics", transient_for=parent_window, modal=True)
        self.dialog.set_default_size(520, 560)

        # Main vertical box
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(18)
        main_box.set_margin_bottom(18)
        main_box.set_margin_start(18)
        main_box.set_margin_end(18)
        self.dialog.set_child(main_box)

        # Header
        h_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        h_title = Gtk.Label(label="System & USB Health Checks", xalign=0.0)
        h_title.add_css_class("header-title")
        h_title.set_hexpand(True)
        h_box.append(h_title)

        refresh_btn = Gtk.Button(label="Refresh")
        refresh_btn.connect("clicked", self._on_refresh)
        h_box.append(refresh_btn)

        main_box.append(h_box)

        # Scrolled container for check rows
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_vexpand(True)
        main_box.append(scrolled)

        self.checks_list_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        scrolled.set_child(self.checks_list_box)

        # Bottom Bar: Copy to clipboard and Close
        btn_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_bar.set_margin_top(8)

        self.copy_btn = Gtk.Button(label="Copy Report (Redacted)")
        self.copy_btn.connect("clicked", self._on_copy_clipboard)
        btn_bar.append(self.copy_btn)

        self.status_feedback = Gtk.Label(label="", xalign=0.0)
        self.status_feedback.set_hexpand(True)
        self.status_feedback.add_css_class("device-meta")
        btn_bar.append(self.status_feedback)

        close_btn = Gtk.Button(label="Close")
        close_btn.connect("clicked", lambda b: self.dialog.close())
        btn_bar.append(close_btn)

        main_box.append(btn_bar)

        self.populate_checks()

    def show(self) -> None:
        if self.dialog:
            self.dialog.present()

    def populate_checks(self) -> None:
        """Runs diagnostics and rebuilds check rows."""
        # Clear existing rows
        while self.checks_list_box.get_first_child():
            self.checks_list_box.remove(self.checks_list_box.get_first_child())

        checks: List[DiagnosticCheck] = self.diagnostics_service.run_all_checks()

        for check in checks:
            card = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
            card.add_css_class("device-card")
            card.set_margin_start(0)
            card.set_margin_end(0)

            # Title & Badge
            top_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
            name_lbl = Gtk.Label(label=check.name, xalign=0.0)
            name_lbl.add_css_class("device-title")
            name_lbl.set_hexpand(True)
            top_row.append(name_lbl)

            badge = Gtk.Label(label=check.status_text)
            badge.add_css_class("status-badge")
            if check.passed:
                badge.add_css_class("status-authorized")
            else:
                badge.add_css_class("status-unauthorized")
            top_row.append(badge)
            card.append(top_row)

            # Details
            details_lbl = Gtk.Label(label=check.details, xalign=0.0)
            details_lbl.add_css_class("diagnostics-text")
            details_lbl.set_wrap(True)
            details_lbl.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
            card.append(details_lbl)

            # Action hint
            if check.action_hint:
                hint_lbl = Gtk.Label(label=f"Action: {check.action_hint}", xalign=0.0)
                hint_lbl.add_css_class("device-meta")
                hint_lbl.set_wrap(True)
                card.append(hint_lbl)

            self.checks_list_box.append(card)

    def _on_refresh(self, button) -> None:
        self.populate_checks()
        self.status_feedback.set_text("Checks refreshed.")

    def _on_copy_clipboard(self, button) -> None:
        report = self.diagnostics_service.generate_report_text(redact=True)
        if Gdk is not None and self.dialog:
            display = self.dialog.get_display()
            clipboard = display.get_clipboard()
            clipboard.set(report)
            self.status_feedback.set_text("Report copied to clipboard!")
        else:
            self.status_feedback.set_text("Report generated.")
