"""
Unit tests for diagnostics service and serial redaction.
"""

import unittest
from unittest.mock import MagicMock

from droidbridge.services.adb_service import AdbDevice
from droidbridge.services.diagnostics import DiagnosticsService
from droidbridge.utils.logging_setup import redact_text


class TestDiagnostics(unittest.TestCase):

    def test_serial_redaction(self):
        text = "Device connected: RFCW10JABCD on port usb:1-1"
        redacted = redact_text(text)
        self.assertNotIn("RFCW10JABCD", redacted)
        self.assertIn("***", redacted)

    def test_diagnostics_with_mock_devices(self):
        mock_adb = MagicMock()
        mock_adb.is_available = True
        mock_adb.get_version.return_value = "34.0.5"

        mock_scrcpy = MagicMock()
        mock_scrcpy.is_available = True
        mock_scrcpy.get_version.return_value = "2.4"
        mock_scrcpy.check_audio_compatibility.return_value = (True, "scrcpy 2.4 supports audio")

        diag = DiagnosticsService(adb_service=mock_adb, scrcpy_service=mock_scrcpy)

        devices = [
            AdbDevice(
                serial="ABC12345DEF",
                state="device",
                model="Pixel_8_Pro",
                android_version="14",
                api_level=34,
            )
        ]

        checks = diag.run_all_checks(devices=devices)
        check_ids = {c.id: c for c in checks}

        self.assertIn("python_runtime", check_ids)
        self.assertIn("adb_binary", check_ids)
        self.assertIn("scrcpy_binary", check_ids)
        self.assertIn("usb_device", check_ids)

        self.assertTrue(check_ids["adb_binary"].passed)
        self.assertTrue(check_ids["scrcpy_binary"].passed)
        self.assertTrue(check_ids["usb_device"].passed)

        report = diag.generate_report_text(redact=True)
        self.assertIn("Diagnostic Report", report)
        self.assertNotIn("ABC12345DEF", report)


if __name__ == "__main__":
    unittest.main()
