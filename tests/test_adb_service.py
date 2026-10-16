"""
Unit tests for ADB output parsing, device inspection, and authorization states.
"""

import unittest
from unittest.mock import MagicMock, patch

from droidbridge.services.adb_service import AdbDevice, AdbService
from droidbridge.utils.command_runner import CommandResult
from droidbridge.utils.errors import AdbNotFoundError


class TestAdbService(unittest.TestCase):

    def setUp(self):
        self.adb = AdbService(adb_path="/usr/bin/adb")

    @patch("droidbridge.services.adb_service.run_command")
    def test_list_devices_empty(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["adb", "devices", "-l"],
            returncode=0,
            stdout="List of devices attached\n\n",
            stderr="",
            duration_ms=10.0,
        )
        devices = self.adb.list_devices()
        self.assertEqual(len(devices), 0)

    @patch("droidbridge.services.adb_service.run_command")
    def test_list_devices_single_authorized(self, mock_run):
        # 1st call: devices -l, 2nd call: shell getprop
        mock_run.side_effect = [
            CommandResult(
                args=["adb", "devices", "-l"],
                returncode=0,
                stdout=(
                    "List of devices attached\n"
                    "RFCW10JABCD            device usb:1-1 product:husky model:Pixel_8_Pro device:husky transport_id:1\n"
                ),
                stderr="",
                duration_ms=15.0,
            ),
            CommandResult(
                args=["adb", "shell", "getprop"],
                returncode=0,
                stdout="14\n34\nGoogle\n",
                stderr="",
                duration_ms=20.0,
            ),
        ]

        devices = self.adb.list_devices()
        self.assertEqual(len(devices), 1)
        dev = devices[0]
        self.assertEqual(dev.serial, "RFCW10JABCD")
        self.assertEqual(dev.state, "device")
        self.assertTrue(dev.is_authorized)
        self.assertFalse(dev.is_unauthorized)
        self.assertFalse(dev.is_offline)
        self.assertEqual(dev.model, "Pixel_8_Pro")
        self.assertEqual(dev.display_name, "Google Pixel 8 Pro")
        self.assertEqual(dev.android_version, "14")
        self.assertEqual(dev.api_level, 34)
        self.assertTrue(dev.supports_audio)

    @patch("droidbridge.services.adb_service.run_command")
    def test_list_devices_multiple_mixed_states(self, mock_run):
        mock_run.return_value = CommandResult(
            args=["adb", "devices", "-l"],
            returncode=0,
            stdout=(
                "List of devices attached\n"
                "DEVICE_AUTH_1234       device usb:1-1 product:oriole model:Pixel_6 transport_id:2\n"
                "DEVICE_UNAUTH_999      unauthorized usb:1-2 transport_id:3\n"
                "DEVICE_OFFLINE_000     offline usb:1-3 transport_id:4\n"
            ),
            stderr="",
            duration_ms=25.0,
        )

        devices = self.adb.list_devices()
        self.assertEqual(len(devices), 3)

        dev1, dev2, dev3 = devices

        # Authorized device
        self.assertTrue(dev1.is_authorized)
        self.assertEqual(dev1.serial, "DEVICE_AUTH_1234")

        # Unauthorized device
        self.assertTrue(dev2.is_unauthorized)
        self.assertFalse(dev2.is_authorized)
        self.assertEqual(dev2.serial, "DEVICE_UNAUTH_999")
        self.assertFalse(dev2.supports_audio)

        # Offline device
        self.assertTrue(dev3.is_offline)
        self.assertEqual(dev3.serial, "DEVICE_OFFLINE_000")

    @patch("droidbridge.services.adb_service.run_command")
    def test_audio_support_matrix(self, mock_run):
        # Android 10 (API 29) -> Audio unsupported
        dev_android10 = AdbDevice(serial="SER1", state="device", api_level=29)
        self.assertFalse(dev_android10.supports_audio)

        # Android 11 (API 30) -> Audio supported
        dev_android11 = AdbDevice(serial="SER2", state="device", api_level=30)
        self.assertTrue(dev_android11.supports_audio)

        # Android 14 (API 34) -> Audio supported
        dev_android14 = AdbDevice(serial="SER3", state="device", api_level=34)
        self.assertTrue(dev_android14.supports_audio)

        # Unauthorized Android 14 -> Audio unsupported until authorized
        dev_unauth = AdbDevice(serial="SER4", state="unauthorized", api_level=34)
        self.assertFalse(dev_unauth.supports_audio)

    @patch("droidbridge.services.adb_service.find_executable")
    def test_adb_not_found(self, mock_find):
        mock_find.return_value = None
        adb = AdbService(adb_path=None)
        with self.assertRaises(AdbNotFoundError):
            _ = adb.adb_path


if __name__ == "__main__":
    unittest.main()
