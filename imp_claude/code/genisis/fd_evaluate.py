# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-EVAL-002 (Evaluator Composition)
"""F_D evaluate — run deterministic checks via subprocess."""

import subprocess
from pathlib import Path

from .models import (
    CheckOutcome,
    CheckResult,
    EvaluationResult,
    ResolvedCheck,
)

DEFAULT_TIMEOUT = 30


def run_check(check: ResolvedCheck, cwd: Path, timeout: int = DEFAULT_TIMEOUT) -> CheckResult:
    """Run a single deterministic check.

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

    try:
        result = subprocess.run(
            check.command,
            shell=True,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        outcome = _interpret_result(result, check.pass_criterion)
        return CheckResult(
            name=check.name,
            outcome=outcome,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message="" if outcome == CheckOutcome.PASS else result.stderr or result.stdout,
            command=check.command,
            exit_code=result.returncode,
            stdout=result.stdout,
            stderr=result.stderr,
        )
    except subprocess.TimeoutExpired:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Timeout after {timeout}s",
            command=check.command,
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
            escalations.append(f"η_D→P: {cr.name} failed — may need agent investigation")

    delta = sum(
        1 for cr in results
        if cr.required and cr.outcome in (CheckOutcome.FAIL, CheckOutcome.ERROR)
    )

    return EvaluationResult(
        edge=edge,
        checks=results,
        delta=delta,
        converged=(delta == 0),
        escalations=escalations,
    )


def _interpret_result(result: subprocess.CompletedProcess, pass_criterion: str | None) -> CheckOutcome:
    """Interpret subprocess result against pass criterion."""
    if not pass_criterion or "exit code 0" in pass_criterion.lower():
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    criterion_lower = pass_criterion.lower()

    # "coverage percentage >= N" — parse number from stdout
    if "coverage" in criterion_lower and ">=" in criterion_lower:
        import re
        # Extract threshold from criterion
        threshold_match = re.search(r">=\s*([\d.]+)", pass_criterion)
        if not threshold_match:
            return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
        threshold = float(threshold_match.group(1))

        # Extract percentage from output
        pct_match = re.search(r"(\d+(?:\.\d+)?)%", result.stdout)
        if pct_match:
            actual = float(pct_match.group(1)) / 100.0
            return CheckOutcome.PASS if actual >= threshold else CheckOutcome.FAIL

    # "zero violations" / "zero errors"
    if "zero" in criterion_lower:
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    # Default: exit code 0
    return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
