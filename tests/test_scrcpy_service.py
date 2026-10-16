"""
Unit tests for scrcpy argument construction, version checks, and audio forwarding flags.
"""

import unittest
from unittest.mock import MagicMock, patch

from droidbridge.config import AppSettings
from droidbridge.services.scrcpy_service import ScrcpyService, parse_version_tuple
from droidbridge.utils.command_runner import CommandResult
from droidbridge.utils.errors import ScrcpyNotFoundError


class TestScrcpyService(unittest.TestCase):

    def setUp(self):
        self.scrcpy = ScrcpyService(scrcpy_path="/usr/bin/scrcpy")

    def test_version_tuple_parsing(self):
        self.assertEqual(parse_version_tuple("2.4"), (2, 4))
        self.assertEqual(parse_version_tuple("scrcpy 2.3.1"), (2, 3, 1))
        self.assertEqual(parse_version_tuple("1.25"), (1, 25))
        self.assertTrue(parse_version_tuple("2.0") >= parse_version_tuple("2.0"))
        self.assertTrue(parse_version_tuple("2.4") > parse_version_tuple("2.0"))
        self.assertFalse(parse_version_tuple("1.25") >= parse_version_tuple("2.0"))

    @patch("droidbridge.services.scrcpy_service.run_command")
    def test_audio_compatibility_scrcpy_2(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["scrcpy", "--version"],
            returncode=0,
            stdout="scrcpy 2.4 <https://github.com/Genymobile/scrcpy>\nDependencies: SDL 2.28.5, FFmpeg 6.1.1\n",
            stderr="",
            duration_ms=5.0,
        )
        supported, msg = self.scrcpy.check_audio_compatibility()
        self.assertTrue(supported)
        self.assertIn("supports audio", msg)

    @patch("droidbridge.services.scrcpy_service.run_command")
    def test_audio_compatibility_scrcpy_1(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["scrcpy", "--version"],
            returncode=0,
            stdout="scrcpy 1.25\n",
            stderr="",
            duration_ms=5.0,
        )
        self.scrcpy._cached_version = None
        supported, msg = self.scrcpy.check_audio_compatibility()
        self.assertFalse(supported)
        self.assertIn("too old", msg)

    @patch("droidbridge.services.scrcpy_service.run_command")
    def test_build_command_android_14_audio(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["scrcpy", "--version"],
            returncode=0,
            stdout="scrcpy 2.4\n",
            stderr="",
            duration_ms=5.0,
        )
        settings = AppSettings(
            max_size=1920,
            max_fps=60,
            video_bitrate="16M",
            audio_enabled=True,
            stay_awake=True,
            fullscreen=False,
        )

        cmd, forwards_audio = self.scrcpy.build_command(
            serial="PIXEL8_1234",
            settings=settings,
            device_api_level=34,  # Android 14
            device_name="Google Pixel 8",
        )

        self.assertTrue(forwards_audio)
        self.assertIn("--serial", cmd)
        self.assertIn("PIXEL8_1234", cmd)
        self.assertIn("--max-size", cmd)
        self.assertIn("1920", cmd)
        self.assertIn("--max-fps", cmd)
        self.assertIn("60", cmd)
        self.assertIn("--video-bit-rate", cmd)
        self.assertIn("16M", cmd)
        self.assertIn("--audio-source=output", cmd)
        self.assertIn("--audio-codec=opus", cmd)
        self.assertNotIn("--no-audio", cmd)

    @patch("droidbridge.services.scrcpy_service.run_command")
    def test_build_command_android_10_no_audio(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["scrcpy", "--version"],
            returncode=0,
            stdout="scrcpy 2.4\n",
            stderr="",
            duration_ms=5.0,
        )
        settings = AppSettings(audio_enabled=True)

        cmd, forwards_audio = self.scrcpy.build_command(
            serial="OLD_PHONE",
            settings=settings,
            device_api_level=29,  # Android 10
            device_name="Old Phone",
        )

        # Must fall back gracefully to --no-audio without failing
        self.assertFalse(forwards_audio)
        self.assertIn("--no-audio", cmd)
        self.assertNotIn("--audio-source=output", cmd)


if __name__ == "__main__":
    unittest.main()
