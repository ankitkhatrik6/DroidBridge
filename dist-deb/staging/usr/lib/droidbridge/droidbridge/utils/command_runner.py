"""
Safe, non-blocking subprocess execution utilities for DroidBridge.
"""

from dataclasses import dataclass
import logging
import shutil
import subprocess
import time
from typing import List, Optional

logger = logging.getLogger(__name__)


@dataclass
class CommandResult:
    args: List[str]
    returncode: int
    stdout: str
    stderr: str
    duration_ms: float

    @property
    def success(self) -> bool:
        return self.returncode == 0


def find_executable(name: str) -> Optional[str]:
    """Finds an executable in the system PATH safely."""
    return shutil.which(name)


def run_command(
    args: List[str],
    timeout: float = 10.0,
    check: bool = False,
    env: Optional[dict] = None,
) -> CommandResult:
    """
    Executes a system command safely with structured arguments.

    Rules:
    - Never uses shell=True.
    - Strictly enforces an explicit timeout.
    - Captures stdout and stderr without blocking the process indefinitely.
    """
    if not args or not isinstance(args, list):
        raise ValueError("Command arguments must be a non-empty list of strings.")

    exe = args[0]
    if not find_executable(exe):
        logger.warning(f"Executable not found on PATH: {exe}")
        return CommandResult(
            args=args,
            returncode=127,
            stdout="",
            stderr=f"Executable not found: {exe}",
            duration_ms=0.0,
        )

    start_time = time.perf_counter()
    try:
        proc = subprocess.run(
            args,
            shell=False,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        result = CommandResult(
            args=args,
            returncode=proc.returncode,
            stdout=proc.stdout or "",
            stderr=proc.stderr or "",
            duration_ms=duration_ms,
        )
        if check and not result.success:
            raise subprocess.CalledProcessError(
                proc.returncode, args, output=proc.stdout, stderr=proc.stderr
            )
        return result

    except subprocess.TimeoutExpired as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.error(f"Command timed out after {timeout}s: {' '.join(args)}")
        return CommandResult(
            args=args,
            returncode=124,
            stdout=exc.stdout or "" if isinstance(exc.stdout, str) else "",
            stderr=f"Command timed out after {timeout} seconds",
            duration_ms=duration_ms,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000.0
        logger.exception(f"Unexpected error executing command: {' '.join(args)}")
        return CommandResult(
            args=args,
            returncode=1,
            stdout="",
            stderr=str(exc),
            duration_ms=duration_ms,
        )
