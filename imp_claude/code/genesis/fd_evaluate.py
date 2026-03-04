# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-EVAL-002 (Evaluator Composition), REQ-SUPV-001 (Heartbeat Observability)
"""F_D evaluate — run deterministic checks via subprocess.

Actor pattern:
  subprocess  = actor (isolated unit of work)
  engine      = supervisor (liveness monitor + circuit breaker)

Timeout semantics:
  stall_timeout  = kill if no stdout/stderr for N seconds  (DEFAULT: 60s)
                   Detects genuinely hung processes, not slow-but-healthy ones.
  wall_timeout   = absolute ceiling = stall_timeout * WALL_CEILING
                   Safety net for runaway processes with infinite output.

Heartbeat:
  Every HEARTBEAT_INTERVAL seconds, prints to stderr:
    ⏱  [check_name] 42s elapsed  (last output 3s ago)
  Visible during long test runs; JSON result still goes to stdout.
"""

import subprocess
import sys
import threading
import time
from pathlib import Path

from .models import (
    CheckOutcome,
    CheckResult,
    EvaluationResult,
    ResolvedCheck,
)

DEFAULT_TIMEOUT = 60  # stall timeout: kill if no output for N seconds
HEARTBEAT_INTERVAL = 10  # seconds between heartbeat lines on stderr
WALL_CEILING = 20  # wall_timeout = stall_timeout * WALL_CEILING


def run_check(
    check: ResolvedCheck, cwd: Path, timeout: int = DEFAULT_TIMEOUT
) -> CheckResult:
    """Run a single deterministic check with stall detection and heartbeat.

    Args:
        check:   Resolved check config.
        cwd:     Working directory for the subprocess.
        timeout: Stall timeout — kill if no stdout/stderr for this many seconds.
                 NOT a wall-clock timeout. A process producing output will run
                 to completion regardless of total elapsed time.

    Non-deterministic checks (agent, human) are returned as SKIP.
    Checks with unresolved $variables are returned as SKIP.
    """
    if check.check_type != "deterministic":
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.SKIP,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Skipped: {check.check_type} check (not F_D)",
        )

    if check.unresolved:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.SKIP,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Skipped: unresolved variables: {', '.join(check.unresolved)}",
        )

    if not check.command:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.SKIP,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message="Skipped: no command specified",
        )

    wall_timeout = max(timeout * WALL_CEILING, 3600)  # at least 1h ceiling

    try:
        proc = subprocess.Popen(
            check.command,
            shell=True,
            cwd=str(cwd),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            # Binary mode: enables read1() which returns immediately with available bytes.
            # Line-by-line text iteration would block on pytest's dot-output (no newlines),
            # causing false stall detection. read1() solves this at the source.
            start_new_session=True,
        )
    except OSError as e:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=str(e),
            command=check.command,
        )

    stdout_buf: list[bytes] = []
    stderr_buf: list[bytes] = []
    last_output = [time.monotonic()]

    def _reader(pipe, buf: list[bytes]) -> None:
        # read1() returns immediately with whatever bytes are available — no newline wait.
        # This is the key: dot-per-test output (no newlines) still updates last_output.
        while True:
            chunk = pipe.read1(4096)  # type: ignore[attr-defined]
            if not chunk:
                break
            buf.append(chunk)
            last_output[0] = time.monotonic()
        pipe.close()

    t_out = threading.Thread(
        target=_reader, args=(proc.stdout, stdout_buf), daemon=True
    )
    t_err = threading.Thread(
        target=_reader, args=(proc.stderr, stderr_buf), daemon=True
    )
    t_out.start()
    t_err.start()

    start = time.monotonic()
    next_hb = start + HEARTBEAT_INTERVAL
    killed: str | None = None  # "stall" | "wall"

    while proc.poll() is None:
        time.sleep(1)
        now = time.monotonic()
        elapsed = int(now - start)
        stall = now - last_output[0]

        # Supervisor: stall detection (actor has gone silent)
        if stall > timeout:
            _kill(proc)
            killed = "stall"
            break

        # Supervisor: wall ceiling (absolute safety net)
        if now - start > wall_timeout:
            _kill(proc)
            killed = "wall"
            break

        # Heartbeat: supervisor reports liveness to operator
        if now >= next_hb:
            print(
                f"  ⏱  [{check.name}] {elapsed}s elapsed"
                f"  (last output {int(stall)}s ago)",
                file=sys.stderr,
                flush=True,
            )
            next_hb += HEARTBEAT_INTERVAL

    t_out.join(5)
    t_err.join(5)
    try:
        proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        _kill(proc)

    if killed == "stall":
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Stall: no output for {timeout}s — process may be hung",
            command=check.command,
        )
    if killed == "wall":
        elapsed_s = int(time.monotonic() - start)
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Wall ceiling reached after {elapsed_s}s (stall_timeout={timeout}s × {WALL_CEILING})",
            command=check.command,
        )

    stdout = b"".join(stdout_buf).decode("utf-8", errors="replace")
    stderr = b"".join(stderr_buf).decode("utf-8", errors="replace")
    completed = subprocess.CompletedProcess(
        check.command,
        proc.returncode if proc.returncode is not None else -1,
        stdout,
        stderr,
    )
    outcome = _interpret_result(completed, check.pass_criterion)
    return CheckResult(
        name=check.name,
        outcome=outcome,
        required=check.required,
        check_type=check.check_type,
        functional_unit=check.functional_unit,
        message="" if outcome == CheckOutcome.PASS else stderr or stdout,
        command=check.command,
        exit_code=completed.returncode,
        stdout=stdout,
        stderr=stderr,
    )


def evaluate_checklist(
    checks: list[ResolvedCheck],
    cwd: Path,
    edge: str = "",
    timeout: int = DEFAULT_TIMEOUT,
) -> EvaluationResult:
    """Evaluate all checks in a checklist. Returns aggregate result with delta."""
    results = []
    escalations = []

    for check in checks:
        cr = run_check(check, cwd, timeout=timeout)
        results.append(cr)

        # η detection: deterministic check fails → candidate for escalation to F_P
        if (
            cr.check_type == "deterministic"
            and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
            and cr.required
        ):
            escalations.append(f"η_D→P: {cr.name} — deterministic failure")

    delta = sum(
        1
        for cr in results
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )

    return EvaluationResult(
        edge=edge,
        checks=results,
        delta=delta,
        converged=(delta == 0),
        escalations=escalations,
    )


def _kill(proc: subprocess.Popen) -> None:
    """Kill subprocess and its process group."""
    import os
    import signal

    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        time.sleep(0.5)
        if proc.poll() is None:
            os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


def _interpret_result(
    result: subprocess.CompletedProcess, pass_criterion: str | None
) -> CheckOutcome:
    """Interpret subprocess result against pass criterion."""
    if not pass_criterion or "exit code 0" in pass_criterion.lower():
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    criterion_lower = pass_criterion.lower()

    # "coverage percentage >= N" — parse number from stdout
    if "coverage" in criterion_lower and ">=" in criterion_lower:
        import re

        threshold_match = re.search(r">=\s*([\d.]+)", pass_criterion)
        if not threshold_match:
            return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
        threshold = float(threshold_match.group(1))

        combined = result.stdout + result.stderr
        total_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%", combined)
        if not total_match:
            total_match = re.search(r"Total coverage:\s*(\d+(?:\.\d+)?)%", combined)
        if total_match:
            actual = float(total_match.group(1)) / 100.0
            return CheckOutcome.PASS if actual >= threshold else CheckOutcome.FAIL

    # "zero violations" / "zero errors"
    if "zero" in criterion_lower:
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    # Default: exit code 0
    return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
