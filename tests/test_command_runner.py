"""
Unit tests for command_runner.py subprocess utilities, timeouts, and structured arguments.
"""

import subprocess
import unittest
from unittest.mock import patch

from droidbridge.utils.command_runner import find_executable, run_command


class TestCommandRunner(unittest.TestCase):

    def test_run_command_success(self):
        result = run_command(["echo", "hello"], timeout=5.0)
        self.assertTrue(result.success)
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout.strip(), "hello")
        self.assertTrue(result.duration_ms >= 0)

    def test_run_command_missing_binary(self):
        result = run_command(["non_existent_binary_xyz123"], timeout=2.0)
        self.assertFalse(result.success)
        self.assertEqual(result.returncode, 127)
        self.assertIn("Executable not found", result.stderr)

    @patch("subprocess.run")
    def test_run_command_timeout(self, mock_run):
        mock_run.side_effect = subprocess.TimeoutExpired(cmd=["sleep", "10"], timeout=1.0)
        with patch("droidbridge.utils.command_runner.find_executable", return_value="/bin/sleep"):
            result = run_command(["sleep", "10"], timeout=1.0)
            self.assertFalse(result.success)
            self.assertEqual(result.returncode, 124)
            self.assertIn("timed out after 1.0", result.stderr)

    def test_invalid_argument_type(self):
        with self.assertRaises(ValueError):
            run_command([])  # empty list
        with self.assertRaises(ValueError):
            run_command("string_command")  # not a list


if __name__ == "__main__":
    unittest.main()
