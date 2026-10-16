"""
Unit tests for ProcessManager subprocess supervision, lifecycle callbacks, and stderr draining.
"""

import io
import threading
import time
import unittest
from unittest.mock import MagicMock, patch

from droidbridge.constants import ConnectionState
from droidbridge.services.process_manager import ProcessManager


class TestProcessManager(unittest.TestCase):

    def setUp(self):
        self.pm = ProcessManager()

    def tearDown(self):
        self.pm.stop_session(timeout=0.5)

    @patch("subprocess.Popen")
    def test_start_session_lifecycle(self, mock_popen):
        exit_event = threading.Event()

        fake_proc = MagicMock()
        fake_proc.poll.side_effect = lambda: None if not exit_event.is_set() else 0
        fake_proc.pid = 4321
        fake_proc.stderr = io.StringIO("INFO: scrcpy 2.4 started\n")

        def fake_wait(timeout=None):
            exit_event.wait(timeout=timeout or 0.5)
            return 0

        fake_proc.wait.side_effect = fake_wait
        mock_popen.return_value = fake_proc

        state_changes = []
        self.pm.on_state_changed = lambda s, m: state_changes.append((s, m))

        success = self.pm.start_session(["scrcpy", "--serial", "DEVICE_123"], "DEVICE_123")
        self.assertTrue(success)
        self.assertTrue(self.pm.is_running)
        self.assertEqual(self.pm.active_serial, "DEVICE_123")
        self.assertTrue(any(s == ConnectionState.MIRRORING_ACTIVE for s, _ in state_changes))

        # Attempt duplicate start while active
        dup_success = self.pm.start_session(["scrcpy", "--serial", "DEVICE_123"], "DEVICE_123")
        self.assertFalse(dup_success)

        # Signal exit and clean up
        exit_event.set()
        time.sleep(0.05)

    @patch("subprocess.Popen")
    def test_audio_failure_cue_detection(self, mock_popen):
        exit_event = threading.Event()
        fake_proc = MagicMock()
        fake_proc.poll.side_effect = lambda: None if not exit_event.is_set() else 0
        fake_proc.pid = 5678
        fake_proc.stderr = io.StringIO("WARN: Audio capture failed: permission denied\n")
        fake_proc.wait.side_effect = lambda timeout=None: exit_event.wait(timeout=timeout or 0.5) or 0
        mock_popen.return_value = fake_proc

        audio_failures = []
        self.pm.on_audio_failure = lambda msg: audio_failures.append(msg)

        self.pm.start_session(["scrcpy", "--serial", "DEV"], "DEV")
        time.sleep(0.1)  # Allow stderr thread to process line

        self.assertTrue(len(audio_failures) >= 1)
        self.assertIn("Audio capture failed", audio_failures[0])
        exit_event.set()

    @patch("subprocess.Popen")
    @patch("os.killpg")
    @patch("os.getpgid")
    def test_stop_session(self, mock_getpgid, mock_killpg, mock_popen):
        exit_event = threading.Event()
        fake_proc = MagicMock()
        fake_proc.poll.side_effect = lambda: None if not exit_event.is_set() else 0
        fake_proc.pid = 9876
        fake_proc.stderr = io.StringIO("")

        def fake_wait(timeout=None):
            exit_event.wait(timeout=timeout or 0.5)
            return 0

        fake_proc.wait.side_effect = fake_wait
        mock_popen.return_value = fake_proc
        mock_getpgid.return_value = 9876

        # When killpg is called, simulate the process receiving signal and exiting
        mock_killpg.side_effect = lambda pgid, sig: exit_event.set()

        self.pm.start_session(["scrcpy"], "DEV")
        self.assertTrue(self.pm.is_running)

        stopped = self.pm.stop_session(timeout=1.0)
        self.assertTrue(stopped)
        mock_killpg.assert_called()


if __name__ == "__main__":
    unittest.main()
