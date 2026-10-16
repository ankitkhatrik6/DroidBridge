"""
Unit tests for configuration validation, persistence, and performance presets.
"""

import json
from pathlib import Path
import tempfile
import unittest

from droidbridge.config import AppSettings, ConfigManager
from droidbridge.constants import PRESETS


class TestConfig(unittest.TestCase):

    def test_settings_validation_boundaries(self):
        s = AppSettings(
            max_size=-100,
            max_fps=999,
            video_bitrate="invalid_bitrate",
            audio_codec="unknown_codec",
        )
        s.validate()
        self.assertEqual(s.max_size, 1920)
        self.assertEqual(s.max_fps, 60)
        self.assertEqual(s.video_bitrate, "16M")
        self.assertEqual(s.audio_codec, "opus")

    def test_apply_preset(self):
        s = AppSettings()
        self.assertTrue(s.apply_preset("720p_low_lat"))
        self.assertEqual(s.max_size, 1280)
        self.assertEqual(s.video_bitrate, "8M")
        self.assertEqual(s.active_preset, "720p_low_lat")

        self.assertFalse(s.apply_preset("non_existent_preset"))

    def test_config_persistence_and_reload(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = Path(tmp_dir) / "test_config.json"
            mgr = ConfigManager(config_path=cfg_file)

            # Modify settings
            mgr.settings.max_size = 1280
            mgr.settings.fullscreen = True
            mgr.settings.video_bitrate = "8M"
            saved = mgr.save()
            self.assertTrue(saved)
            self.assertTrue(cfg_file.exists())

            # Read raw JSON to verify structure
            with open(cfg_file, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            self.assertEqual(raw_data["max_size"], 1280)
            self.assertTrue(raw_data["fullscreen"])

            # Reload with a new instance
            mgr2 = ConfigManager(config_path=cfg_file)
            self.assertEqual(mgr2.settings.max_size, 1280)
            self.assertTrue(mgr2.settings.fullscreen)

    def test_reset_defaults(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            cfg_file = Path(tmp_dir) / "test_config.json"
            mgr = ConfigManager(config_path=cfg_file)
            mgr.settings.max_size = 3840
            mgr.settings.fullscreen = True
            mgr.save()

            mgr.reset_to_defaults()
            self.assertEqual(mgr.settings.max_size, 1920)
            self.assertFalse(mgr.settings.fullscreen)


if __name__ == "__main__":
    unittest.main()
