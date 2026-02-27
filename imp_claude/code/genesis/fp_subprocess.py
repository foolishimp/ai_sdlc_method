# Implements: REQ-ROBUST-001 (Actor Isolation), REQ-ROBUST-002 (Supervisor Pattern), REQ-SUPV-003 (Failure Observability)
"""Isolated F_P process manager — wraps all `claude -p` calls.

Every F_P subprocess call runs in its own process group with:
- Environment sanitization (strip nesting guards)
- Watchdog thread with wall timeout + stall detection
- Process group kill (SIGTERM → SIGKILL) on timeout
- Structured result with duration, timeout status, and error classification

Patterns extracted from imp_claude/tests/e2e/conftest.py (proven in E2E runs).
"""

import os
import signal
import subprocess
import threading
import time
from dataclasses import dataclass


@dataclass
class SubprocessResult:
    """Result of an isolated F_P subprocess call."""

    stdout: str = ""
    stderr: str = ""
    returncode: int = -1
    timed_out: bool = False
    stall_killed: bool = False
    duration_ms: int = 0
    error: str = ""
    pid: int = 0


# ── Environment Sanitization ─────────────────────────────────────────

# Nesting guard variables that Claude CLI checks before starting.
# When engine runs inside a Claude Code session, these must be stripped.
_NESTING_GUARD_VARS = frozenset(
    ["CLAUDECODE", "CLAUDE_CODE_SSE_PORT", "CLAUDE_CODE_ENTRYPOINT"]
)


def clean_env() -> dict[str, str]:
    """Return env dict with Claude nesting guards removed.

    Extracted from imp_claude/tests/e2e/conftest.py:442-452.
    """
    env = os.environ.copy()
    for key in _NESTING_GUARD_VARS:
        env.pop(key, None)
    return env


# ── Process Group Kill ────────────────────────────────────────────────


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Kill an entire process group (parent + all children).

    Uses SIGTERM first (graceful), then SIGKILL after 5s if still alive.
    Falls back to proc.kill() if process group operations fail.

    Extracted from imp_claude/tests/e2e/conftest.py:546-568.
    """
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        for _ in range(50):
            if proc.poll() is not None:
                return
            time.sleep(0.1)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


# ── Isolated Runner ──────────────────────────────────────────────────


def run_claude_isolated(
    cmd: list[str],
    *,
    timeout: int = 120,
    stall_timeout: int = 60,
    sanitize_env: bool = True,
    cwd: str | None = None,
) -> SubprocessResult:
    """Run a claude -p command in an isolated process group.

    Args:
        cmd: Full command list (e.g., ["claude", "-p", ...]).
        timeout: Wall-clock timeout in seconds.
        stall_timeout: Kill if no stdout/stderr growth for this many seconds.
            Set to 0 to disable stall detection.
        sanitize_env: Strip Claude nesting guard env vars.
        cwd: Working directory for the subprocess.

    Returns:
        SubprocessResult with stdout, stderr, timing, and status flags.
    """
    env = clean_env() if sanitize_env else None
    start = time.time()
    timed_out = False
    stall_killed = False

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=cwd,
            start_new_session=True,
        )
    except OSError as e:
        duration_ms = int((time.time() - start) * 1000)
        return SubprocessResult(
            error=f"Failed to start subprocess: {e}",
            duration_ms=duration_ms,
        )

    pid = proc.pid

    def watchdog():
        nonlocal timed_out, stall_killed
        last_activity = time.time()

        while proc.poll() is None:
            time.sleep(2)
            now = time.time()

            # Wall timeout
            if now - start > timeout:
                timed_out = True
                _kill_process_group(proc)
                return

            # Stall detection (if enabled)
            if stall_timeout > 0 and now - last_activity > stall_timeout:
                stall_killed = True
                timed_out = True
                _kill_process_group(proc)
                return

            # Reset activity timer on any poll cycle where process is active
            last_activity = now

    watcher = threading.Thread(target=watchdog, daemon=True)
    watcher.start()

    try:
        stdout, stderr = proc.communicate()
    except Exception:
        stdout, stderr = "", ""
        if proc.poll() is None:
            _kill_process_group(proc)

    watcher.join(timeout=5)
    duration_ms = int((time.time() - start) * 1000)

    error = ""
    if timed_out and stall_killed:
        error = f"Stall detected — no activity for {stall_timeout}s"
    elif timed_out:
        error = f"Wall timeout after {timeout}s"
    elif proc.returncode != 0:
        error = f"Exited with code {proc.returncode}"

    return SubprocessResult(
        stdout=stdout or "",
        stderr=stderr or "",
        returncode=proc.returncode if proc.returncode is not None else -1,
        timed_out=timed_out,
        stall_killed=stall_killed,
        duration_ms=duration_ms,
        error=error,
        pid=pid,
    )
