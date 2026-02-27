# Implements: REQ-ITER-003 (Functor Encoding Tracking), REQ-EVAL-002 (Evaluator Composition), REQ-ROBUST-001 (Actor Isolation)
"""F_P evaluate — LLM-based evaluation via Claude Code CLI.

Uses `claude -p --output-format json --json-schema` for structured output.
The deterministic wrapper builds the prompt, calls Claude Code, parses
the JSON response, and returns a CheckResult. The LLM provides judgment;
everything around it is F_D.
"""

import json
import shutil

from .fp_subprocess import run_claude_isolated
from .models import CheckOutcome, CheckResult, ResolvedCheck

CLAUDE_CMD = "claude"

_RESPONSE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "outcome": {
                "type": "string",
                "enum": ["pass", "fail"],
                "description": "Whether the asset passes the criterion",
            },
            "reason": {
                "type": "string",
                "description": "Brief explanation of the judgment",
            },
        },
        "required": ["outcome", "reason"],
    }
)


def run_check(
    check: ResolvedCheck,
    asset_content: str,
    context: str = "",
    model: str = "sonnet",
    timeout: int = 120,
    claude_cmd: str = CLAUDE_CMD,
) -> CheckResult:
    """Evaluate a single agent check by calling Claude Code.

    Deterministic checks are returned as SKIP (use fd_evaluate for those).
    """
    if check.check_type != "agent":
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.SKIP,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Skipped: {check.check_type} check (not F_P)",
        )

    # Verify claude is available
    if not shutil.which(claude_cmd):
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Claude Code CLI not found: {claude_cmd}",
        )

    prompt = _build_prompt(check, asset_content, context)

    cmd = [
        claude_cmd,
        "-p",
        "--output-format",
        "json",
        "--json-schema",
        _RESPONSE_SCHEMA,
        "--model",
        model,
        "--no-session-persistence",
        prompt,
    ]
    result = run_claude_isolated(cmd, timeout=timeout)

    if result.timed_out:
        detail = "stall detected" if result.stall_killed else "wall timeout"
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Claude Code {detail} after {result.duration_ms}ms",
        )

    if result.error:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Claude Code error: {result.error}",
            stdout=result.stdout,
            stderr=result.stderr,
        )

    return _parse_response(result.stdout, check)


def _build_prompt(check: ResolvedCheck, asset_content: str, context: str) -> str:
    """Build the evaluation prompt. Deterministic — same inputs, same prompt."""
    parts = [
        "You are an evaluator in a software methodology framework.",
        "Evaluate the following asset against the criterion below.",
        "",
        f"CHECK NAME: {check.name}",
        f"CRITERION: {check.criterion}",
    ]
    if context:
        parts.extend(["", "CONTEXT:", context])
    parts.extend(
        [
            "",
            "ASSET:",
            asset_content,
            "",
            "Respond with your judgment as JSON matching the schema provided.",
        ]
    )
    return "\n".join(parts)


def _parse_response(stdout: str, check: ResolvedCheck) -> CheckResult:
    """Parse Claude Code JSON response into CheckResult."""
    try:
        # claude --output-format json wraps in {"type":"result","result":...}
        outer = json.loads(stdout)
        # The actual content may be in result field or be the direct response
        if isinstance(outer, dict) and "result" in outer:
            content = outer["result"]
        else:
            content = outer

        # If content is a string, it's the raw text — try to parse as JSON
        if isinstance(content, str):
            content = json.loads(content)

        outcome_str = content.get("outcome", "").lower()
        reason = content.get("reason", "")

        if outcome_str == "pass":
            outcome = CheckOutcome.PASS
        elif outcome_str == "fail":
            outcome = CheckOutcome.FAIL
        else:
            outcome = CheckOutcome.ERROR
            reason = f"Unexpected outcome '{outcome_str}': {reason}"

        return CheckResult(
            name=check.name,
            outcome=outcome,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=reason,
            stdout=stdout,
        )

    except (json.JSONDecodeError, KeyError, TypeError) as e:
        return CheckResult(
            name=check.name,
            outcome=CheckOutcome.ERROR,
            required=check.required,
            check_type=check.check_type,
            functional_unit=check.functional_unit,
            message=f"Failed to parse Claude Code response: {e}",
            stdout=stdout,
        )
