# Implements: REQ-ROBUST-001 (Actor Isolation), REQ-ROBUST-002 (Supervisor Pattern), REQ-SUPV-003 (Failure Observability)
"""F_P subprocess runner — wraps all claude -p / claude --print calls.

Thin adapter: builds the cleaned environment, calls run_bounded(), and
returns SubprocessResult (the shape callers expect).

All timeout and kill logic lives in proc.run_bounded() — one auditable path
for every external process in the engine.
"""

import os
from dataclasses import dataclass

from .proc import BoundedResult, run_bounded


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


# ── Environment sanitization ──────────────────────────────────────────────────

# Claude CLI nesting guards — must be stripped when engine runs inside a session
_NESTING_GUARD_VARS = frozenset(
    ["CLAUDECODE", "CLAUDE_CODE_SSE_PORT", "CLAUDE_CODE_ENTRYPOINT"]
)


def clean_env() -> dict[str, str]:
    """Return env dict with Claude nesting guard vars removed."""
    env = os.environ.copy()
    for key in _NESTING_GUARD_VARS:
        env.pop(key, None)
    return env


# ── Isolated runner ───────────────────────────────────────────────────────────


def run_claude_isolated(
    cmd: list[str],
    *,
    timeout: int = 300,
    stall_timeout: int = 60,
    sanitize_env: bool = True,
    cwd: str | None = None,
) -> SubprocessResult:
    """Run a claude command in an isolated process group.

    Total-function guarantee: returns within timeout + 10 seconds, always.
    Delegates all subprocess management to proc.run_bounded().

    Args:
        cmd:          Full command list (e.g., ["claude", "--print", ...]).
        timeout:      Wall-clock timeout in seconds (hard ceiling).
        stall_timeout: Kill if no stdout/stderr bytes for this many seconds.
                       Set to 0 to disable (wall timeout still enforced).
        sanitize_env: Strip Claude nesting guard env vars.
        cwd:          Working directory.
    """
    env = clean_env() if sanitize_env else None

    r: BoundedResult = run_bounded(
        cmd,
        cwd=cwd,
        env=env,
        shell=False,
        wall_timeout=float(timeout),
        stall_timeout=float(stall_timeout),
        heartbeat_interval=30.0,
        heartbeat_label=cmd[0] if cmd else "claude",
    )

    return SubprocessResult(
        stdout=r.stdout,
        stderr=r.stderr,
        returncode=r.returncode,
        timed_out=r.timed_out,
        stall_killed=r.stall_killed,
        duration_ms=r.duration_ms,
        error=r.error,
        pid=r.pid,
    )
