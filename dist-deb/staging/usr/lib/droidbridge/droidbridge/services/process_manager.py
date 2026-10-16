"""
Dedicated subprocess supervisor for scrcpy lifecycle, stderr monitoring, and clean reaping.
"""

import atexit
import logging
import os
import signal
import subprocess
import threading
import time
from typing import Callable, List, Optional

from droidbridge.constants import ConnectionState
from droidbridge.utils.errors import ScrcpyExecutionError

logger = logging.getLogger(__name__)


class ProcessManager:
    """Supervises active scrcpy subprocesses without blocking the GUI main loop."""

    def __init__(self):
        self._process: Optional[subprocess.Popen] = None
        self._active_serial: Optional[str] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stderr_thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._is_terminating = False
        self._start_time: float = 0.0

        # Callbacks
        self.on_state_changed: Optional[Callable[[ConnectionState, str], None]] = None
        self.on_stderr_line: Optional[Callable[[str], None]] = None
        self.on_audio_failure: Optional[Callable[[str], None]] = None

        # Register cleanup on program exit
        atexit.register(self.cleanup_all)

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._process is not None and self._process.poll() is None

    @property
    def active_serial(self) -> Optional[str]:
        return self._active_serial

    @property
    def uptime_seconds(self) -> float:
        if self.is_running and self._start_time > 0:
            return time.time() - self._start_time
        return 0.0

    def start_session(self, cmd_args: List[str], serial: str) -> bool:
        """
        Launches scrcpy in a non-blocking background process.
        Prevents duplicate sessions.
        """
        with self._lock:
            if self._process is not None and self._process.poll() is None:
                logger.warning("A mirroring session is already active. Stop it first.")
                return False

            self._is_terminating = False
            self._active_serial = serial
            self._start_time = time.time()

            try:
                logger.info(f"Launching scrcpy subprocess: {' '.join(cmd_args)}")
                self._process = subprocess.Popen(
                    cmd_args,
                    shell=False,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1,  # Line-buffered
                    preexec_fn=os.setsid,  # New process group for clean group termination
                )
            except Exception as exc:
                logger.exception(f"Failed to spawn scrcpy process: {exc}")
                if self.on_state_changed:
                    self.on_state_changed(ConnectionState.RECOVERABLE_ERROR, f"Failed to start scrcpy: {exc}")
                return False

        # Start background threads to drain pipes and monitor exit
        self._stderr_thread = threading.Thread(
            target=self._drain_stderr,
            args=(self._process,),
            daemon=True,
            name="ScrcpyStderrReader",
        )
        self._stderr_thread.start()

        self._monitor_thread = threading.Thread(
            target=self._monitor_lifecycle,
            args=(self._process,),
            daemon=True,
            name="ScrcpyProcessMonitor",
        )
        self._monitor_thread.start()

        if self.on_state_changed:
            self.on_state_changed(ConnectionState.MIRRORING_ACTIVE, "Mirroring active in separate window.")

        return True

    def _drain_stderr(self, proc: subprocess.Popen) -> None:
        """Reads stderr line-by-line in real time to prevent pipe buffer deadlocks."""
        try:
            if not proc.stderr:
                return

            for line in iter(proc.stderr.readline, ""):
                line_str = line.strip()
                if not line_str:
                    continue

                logger.debug(f"[scrcpy stderr] {line_str}")
                if self.on_stderr_line:
                    self.on_stderr_line(line_str)

                # Detect audio forwarding cues
                lower = line_str.lower()
                if "audio disabled" in lower or "audio: false" in lower:
                    logger.info("scrcpy indicated audio is disabled for this session.")
                elif "audio capture failed" in lower or "could not start audio capture" in lower:
                    logger.warning(f"Audio capture failure detected: {line_str}")
                    if self.on_audio_failure:
                        self.on_audio_failure(line_str)
                elif "device disconnected" in lower or "connection reset" in lower:
                    logger.warning("Device disconnected event detected in scrcpy stream.")

        except Exception as exc:
            logger.debug(f"Stderr reader terminated: {exc}")
        finally:
            if proc.stderr:
                proc.stderr.close()

    def _monitor_lifecycle(self, proc: subprocess.Popen) -> None:
        """Monitors process exit and triggers state transitions."""
        returncode = proc.wait()
        logger.info(f"scrcpy process (PID {proc.pid}) exited with code {returncode}")

        with self._lock:
            was_terminating = self._is_terminating
            self._process = None
            self._active_serial = None
            self._start_time = 0.0

        if was_terminating:
            if self.on_state_changed:
                self.on_state_changed(ConnectionState.SESSION_STOPPED, "Mirroring session stopped.")
        elif returncode == 0:
            if self.on_state_changed:
                self.on_state_changed(ConnectionState.SESSION_STOPPED, "Mirroring window closed.")
        else:
            if self.on_state_changed:
                self.on_state_changed(
                    ConnectionState.RECOVERABLE_ERROR,
                    f"Mirroring exited with error code {returncode}.",
                )

    def stop_session(self, timeout: float = 3.0) -> bool:
        """Gracefully terminates the supervised scrcpy instance."""
        with self._lock:
            if not self._process or self._process.poll() is not None:
                return True

            self._is_terminating = True
            proc = self._process

        logger.info(f"Stopping scrcpy process (PID {proc.pid})...")
        try:
            # Terminate the process group to ensure child threads/helpers exit
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        except ProcessLookupError:
            return True
        except Exception as exc:
            logger.debug(f"SIGTERM via killpg failed: {exc}, sending SIGTERM directly.")
            try:
                proc.terminate()
            except Exception:
                pass

        # Wait gracefully
        try:
            proc.wait(timeout=timeout)
            logger.info("scrcpy process terminated gracefully.")
            return True
        except subprocess.TimeoutExpired:
            logger.warning(f"scrcpy did not terminate within {timeout}s; sending SIGKILL...")
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception:
                proc.kill()
            return True

    def cleanup_all(self) -> None:
        """Atexit handler to ensure no zombie or orphan processes remain."""
        if self.is_running:
            logger.info("Cleaning up running scrcpy session on exit...")
            self.stop_session(timeout=1.5)
