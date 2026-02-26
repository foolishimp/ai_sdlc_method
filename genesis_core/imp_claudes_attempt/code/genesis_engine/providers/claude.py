# Implements: GENESIS_ENGINE_SPEC §6.2 (F_P Binding Point)
"""Claude Code provider — F_P evaluation via `claude -p` CLI.

Uses `claude -p --output-format json --json-schema` for structured output.
The deterministic wrapper builds the prompt, calls Claude Code, parses
the JSON response, and returns a CheckResult.
"""

import json
import shutil
import subprocess

from ..models import CheckOutcome, CheckResult, ResolvedCheck
from .base import FPProvider

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


class ClaudeProvider(FPProvider):
    """F_P provider using Claude Code CLI."""

    def __init__(self, model: str = "sonnet", claude_cmd: str = "claude", **kwargs):
        self._model = model
        self._claude_cmd = claude_cmd

    @property
    def name(self) -> str:
        return "claude"

    def run_check(
        self,
        check: ResolvedCheck,
        asset_content: str,
        context: str = "",
        timeout: int = 120,
    ) -> CheckResult:
        if check.check_type != "agent":
            return CheckResult(
                name=check.name,
                outcome=CheckOutcome.SKIP,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Skipped: {check.check_type} check (not F_P)",
            )

        if not shutil.which(self._claude_cmd):
            return CheckResult(
                name=check.name,
                outcome=CheckOutcome.ERROR,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Claude Code CLI not found: {self._claude_cmd}",
            )

        prompt = self._build_prompt(check, asset_content, context)

        try:
            result = subprocess.run(
                [
                    self._claude_cmd,
                    "-p",
                    "--output-format",
                    "json",
                    "--json-schema",
                    _RESPONSE_SCHEMA,
                    "--model",
                    self._model,
                    "--no-session-persistence",
                    prompt,
                ],
                capture_output=True,
                text=True,
                timeout=timeout,
            )

            if result.returncode != 0:
                return CheckResult(
                    name=check.name,
                    outcome=CheckOutcome.ERROR,
                    required=check.required,
                    check_type=check.check_type,
                    functional_unit=check.functional_unit,
                    message=f"Claude exited {result.returncode}: {result.stderr[:200]}",
                    stdout=result.stdout,
                    stderr=result.stderr,
                )

            return self._parse_response(result.stdout, check)

        except subprocess.TimeoutExpired:
            return CheckResult(
                name=check.name,
                outcome=CheckOutcome.ERROR,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Claude timed out after {timeout}s",
            )
        except OSError as e:
            return CheckResult(
                name=check.name,
                outcome=CheckOutcome.ERROR,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"Failed to invoke Claude Code: {e}",
            )

    def _build_prompt(
        self, check: ResolvedCheck, asset_content: str, context: str
    ) -> str:
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

    def _parse_response(self, stdout: str, check: ResolvedCheck) -> CheckResult:
        try:
            outer = json.loads(stdout)
            if isinstance(outer, dict) and "result" in outer:
                content = outer["result"]
            else:
                content = outer

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
                message=f"Failed to parse Claude response: {e}",
                stdout=stdout,
            )
