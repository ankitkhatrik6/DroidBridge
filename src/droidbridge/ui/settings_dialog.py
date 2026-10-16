"""
Settings dialog for configuring video, audio, window behavior, and performance presets.
"""

from typing import Callable, Optional

try:
    import gi
    gi.require_version("Gtk", "4.0")
    from gi.repository import Gtk
except Exception:
    Gtk = None

from droidbridge.config import AppSettings, ConfigManager


class SettingsDialog:
    """Preferences window allowing fine-tuning of scrcpy and audio options."""

    def __init__(self, parent_window, config_manager: ConfigManager, on_saved: Optional[Callable[[], None]] = None):
        self.config_manager = config_manager
        self.settings = config_manager.settings
        self.on_saved = on_saved

        if Gtk is None:
            self.dialog = None
            return

        self.dialog = Gtk.Window(title="DroidBridge Settings", transient_for=parent_window, modal=True)
        self.dialog.set_default_size(460, 520)

        # Scrolled container
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.dialog.set_child(scrolled)

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        scrolled.set_child(main_box)

        # Section 1: Video Parameters
        v_title = Gtk.Label(label="Video & Display", xalign=0.0)
        v_title.add_css_class("header-title")
        main_box.append(v_title)

        grid = Gtk.Grid()
        grid.set_row_spacing(10)
        grid.set_column_spacing(16)
        main_box.append(grid)

        # Resolution dropdown
        grid.attach(Gtk.Label(label="Maximum Resolution:", xalign=0.0), 0, 0, 1, 1)
        self.res_combo = Gtk.DropDown.new_from_strings(["1080p (1920)", "720p (1280)", "4K (3840)", "Native / Unlimited (0)"])
        res_idx = {1920: 0, 1280: 1, 3840: 2, 0: 3}.get(self.settings.max_size, 0)
        self.res_combo.set_selected(res_idx)
        grid.attach(self.res_combo, 1, 0, 1, 1)

        # Max FPS dropdown
        grid.attach(Gtk.Label(label="Max Frame Rate:", xalign=0.0), 0, 1, 1, 1)
        self.fps_combo = Gtk.DropDown.new_from_strings(["60 FPS", "30 FPS", "90 FPS", "120 FPS"])
        fps_idx = {60: 0, 30: 1, 90: 2, 120: 3}.get(self.settings.max_fps, 0)
        self.fps_combo.set_selected(fps_idx)
        grid.attach(self.fps_combo, 1, 1, 1, 1)

        # Bitrate dropdown
        grid.attach(Gtk.Label(label="Video Bitrate:", xalign=0.0), 0, 2, 1, 1)
        self.bitrate_combo = Gtk.DropDown.new_from_strings(["16 Mbps (Balanced)", "8 Mbps (Fast)", "24 Mbps (High)", "4 Mbps (Low)"])
        bit_idx = {"16M": 0, "8M": 1, "24M": 2, "4M": 3}.get(self.settings.video_bitrate, 0)
        self.bitrate_combo.set_selected(bit_idx)
        grid.attach(self.bitrate_combo, 1, 2, 1, 1)

        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Section 2: Audio Forwarding
        a_title = Gtk.Label(label="Audio Forwarding", xalign=0.0)
        a_title.add_css_class("header-title")
        main_box.append(a_title)

        self.audio_switch = Gtk.Switch()
        self.audio_switch.set_active(self.settings.audio_enabled)
        audio_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        audio_lbl = Gtk.Label(label="Forward Phone Audio to PC Speakers", xalign=0.0)
        audio_lbl.set_hexpand(True)
        audio_row.append(audio_lbl)
        audio_row.append(self.audio_switch)
        main_box.append(audio_row)

        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Section 3: Window & Behavior
        w_title = Gtk.Label(label="Window & Behavior", xalign=0.0)
        w_title.add_css_class("header-title")
        main_box.append(w_title)

        # Fullscreen
        self.fs_check = Gtk.CheckButton(label="Open Mirroring in Fullscreen")
        self.fs_check.set_active(self.settings.fullscreen)
        main_box.append(self.fs_check)

        # Stay Awake
        self.awake_check = Gtk.CheckButton(label="Keep Phone Screen Awake while Mirroring")
        self.awake_check.set_active(self.settings.stay_awake)
        main_box.append(self.awake_check)

        # Turn Screen Off
        self.screenoff_check = Gtk.CheckButton(label="Turn Physical Phone Screen Off (Saves Battery)")
        self.screenoff_check.set_active(self.settings.turn_screen_off)
        main_box.append(self.screenoff_check)

        # Show Touches
        self.touches_check = Gtk.CheckButton(label="Show Finger Touch Indicators on Screen")
        self.touches_check.set_active(self.settings.show_touches)
        main_box.append(self.touches_check)

        main_box.append(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL))

        # Button Row: Reset Defaults, Cancel, Save
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.END)
        btn_box.set_margin_top(8)

        reset_btn = Gtk.Button(label="Reset Defaults")
        reset_btn.connect("clicked", self._on_reset)
        btn_box.append(reset_btn)

        close_btn = Gtk.Button(label="Cancel")
        close_btn.connect("clicked", lambda b: self.dialog.close())
        btn_box.append(close_btn)

        save_btn = Gtk.Button(label="Save Preferences")
        save_btn.add_css_class("btn-primary-action")
        save_btn.connect("clicked", self._on_save)
        btn_box.append(save_btn)

        main_box.append(btn_box)

    def show(self) -> None:
        if self.dialog:
            self.dialog.present()

    def _on_save(self, button) -> None:
        """Collects form inputs, validates, and persists to config file."""
        res_map = {0: 1920, 1: 1280, 2: 3840, 3: 0}
        fps_map = {0: 60, 1: 30, 2: 90, 3: 120}
        bit_map = {0: "16M", 1: "8M", 2: "24M", 3: "4M"}

        self.settings.max_size = res_map.get(self.res_combo.get_selected(), 1920)
        self.settings.max_fps = fps_map.get(self.fps_combo.get_selected(), 60)
        self.settings.video_bitrate = bit_map.get(self.bitrate_combo.get_selected(), "16M")
        self.settings.audio_enabled = self.audio_switch.get_active()
        self.settings.fullscreen = self.fs_check.get_active()
        self.settings.stay_awake = self.awake_check.get_active()
        self.settings.turn_screen_off = self.screenoff_check.get_active()
        self.settings.show_touches = self.touches_check.get_active()

        self.config_manager.save()
        if self.on_saved:
            self.on_saved()

        self.dialog.close()

    def _on_reset(self, button) -> None:
        """Resets to system defaults."""
        self.config_manager.reset_to_defaults()
        self.settings = self.config_manager.settings

        # Update UI components
        self.res_combo.set_selected(0)
        self.fps_combo.set_selected(0)
        self.bitrate_combo.set_selected(0)
        self.audio_switch.set_active(True)
        self.fs_check.set_active(False)
        self.awake_check.set_active(True)
        self.screenoff_check.set_active(False)
        self.touches_check.set_active(False)

        if self.on_saved:
            self.on_saved()
