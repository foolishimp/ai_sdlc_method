# Implements: GENESIS_ENGINE_SPEC §6.1 (F_D Binding)
"""F_D evaluate — run deterministic checks via subprocess."""

import re
import subprocess
from pathlib import Path

from .models import CheckOutcome, CheckResult, ResolvedCheck

DEFAULT_TIMEOUT = 30


def run_check(
    check: ResolvedCheck, cwd: Path, timeout: int = DEFAULT_TIMEOUT
) -> CheckResult:
    """Run a single deterministic check via subprocess."""
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
            message=""
            if outcome == CheckOutcome.PASS
            else result.stderr or result.stdout,
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


def _interpret_result(
    result: subprocess.CompletedProcess, pass_criterion: str | None
) -> CheckOutcome:
    """Interpret subprocess result against pass criterion."""
    if not pass_criterion or "exit code 0" in pass_criterion.lower():
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    criterion_lower = pass_criterion.lower()

    if "coverage" in criterion_lower and ">=" in criterion_lower:
        threshold_match = re.search(r">=\s*([\d.]+)", pass_criterion)
        if not threshold_match:
            return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
        threshold = float(threshold_match.group(1))

        combined = result.stdout + result.stderr
        total_match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+(?:\.\d+)?)%", combined)
        if not total_match:
            total_match = re.search(
                r"Total coverage:\s*(\d+(?:\.\d+)?)%", combined
            )
        if total_match:
            actual = float(total_match.group(1)) / 100.0
            return CheckOutcome.PASS if actual >= threshold else CheckOutcome.FAIL

    if "zero" in criterion_lower:
        return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL

    return CheckOutcome.PASS if result.returncode == 0 else CheckOutcome.FAIL
