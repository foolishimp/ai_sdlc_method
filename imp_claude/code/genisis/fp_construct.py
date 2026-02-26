# Implements: REQ-F-FPC-001 (LLM Construct Per Edge), REQ-F-FPC-002 (Batched Evaluate), REQ-F-FPC-006 (Construct Output Schema), REQ-NFR-FPC-003 (Timeout Retry Resilience)
"""F_P construct — LLM-based artifact generation via Claude Code CLI.

Calls `claude -p` once per edge to construct an artifact and batch-evaluate
all agent criteria in a single response. The deterministic wrapper builds
the prompt, calls Claude Code, parses the JSON response, validates the
schema, and returns a ConstructResult. The LLM provides construction and
judgment; everything around it is F_D.

Design reference: ADR-020, FUNCTOR_FRAMEWORK_DESIGN.md Appendix A.
"""

import json
import shutil
import subprocess
import time

from .models import CheckOutcome, CheckResult, ConstructResult, ResolvedCheck

CLAUDE_CMD = "claude"

MAX_RETRIES = 2

_RESPONSE_SCHEMA = json.dumps(
    {
        "type": "object",
        "properties": {
            "artifact": {
                "type": "string",
                "description": "The constructed or modified asset content",
            },
            "evaluations": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "check_name": {"type": "string"},
                        "outcome": {
                            "type": "string",
                            "enum": ["pass", "fail"],
                        },
                        "reason": {"type": "string"},
                    },
                    "required": ["check_name", "outcome", "reason"],
                },
                "description": "Self-evaluation against all agent criteria",
            },
            "traceability": {
                "type": "array",
                "items": {"type": "string"},
                "description": "REQ keys implemented/validated in the artifact",
            },
            "source_findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "classification": {"type": "string"},
                    },
                    "required": ["description", "classification"],
                },
                "description": "Issues found in source asset during construction",
            },
        },
        "required": ["artifact", "evaluations", "traceability"],
    }
)


def run_construct(
    edge: str,
    asset_content: str,
    context: str,
    edge_config: dict,
    constraints: dict | None = None,
    model: str = "sonnet",
    timeout: int = 120,
    claude_cmd: str = CLAUDE_CMD,
) -> ConstructResult:
    """Call claude -p once per edge to construct artifact + batch-evaluate.

    Returns a ConstructResult with the generated artifact and self-evaluations.
    On failure (timeout, malformed response), retries up to MAX_RETRIES times.
    """
    if not shutil.which(claude_cmd):
        return ConstructResult(
            artifact="",
            model=model,
            source_findings=[
                {
                    "description": f"Claude Code CLI not found: {claude_cmd}",
                    "classification": "TOOL_MISSING",
                }
            ],
        )

    agent_checks = _extract_agent_checks(edge_config)
    prompt = _build_prompt(edge, asset_content, context, agent_checks, constraints)

    for attempt in range(1, MAX_RETRIES + 2):  # 1 initial + MAX_RETRIES retries
        start_ms = int(time.time() * 1000)
        result = _call_claude(prompt, model, timeout, claude_cmd)
        duration_ms = int(time.time() * 1000) - start_ms

        if result is None:
            if attempt <= MAX_RETRIES:
                continue
            return ConstructResult(
                artifact="",
                model=model,
                duration_ms=duration_ms,
                retries=attempt - 1,
                source_findings=[
                    {
                        "description": f"Claude Code timed out after {timeout}s",
                        "classification": "TIMEOUT",
                    }
                ],
            )

        parsed = _parse_response(result)
        if parsed is not None:
            parsed.model = model
            parsed.duration_ms = duration_ms
            parsed.retries = attempt - 1
            return parsed

        # Malformed response — retry
        if attempt <= MAX_RETRIES:
            continue

        return ConstructResult(
            artifact="",
            model=model,
            duration_ms=duration_ms,
            retries=attempt - 1,
            source_findings=[
                {
                    "description": f"Malformed JSON response after {attempt} attempts",
                    "classification": "PARSE_ERROR",
                }
            ],
        )

    # Should not reach here, but defensive
    return ConstructResult(artifact="", model=model)


def batched_check_results(
    construct_result: ConstructResult,
    agent_checks: list[ResolvedCheck],
) -> list[CheckResult]:
    """Convert batched evaluations from ConstructResult into CheckResults.

    For each agent check, look for a matching evaluation in the construct
    response. Unmatched checks return None (caller should fall back to
    individual fp_evaluate).
    """
    eval_map = {}
    for ev in construct_result.evaluations:
        name = ev.get("check_name", "")
        if name:
            eval_map[name] = ev

    results = []
    for check in agent_checks:
        ev = eval_map.get(check.name)
        if ev is None:
            # No batched result — caller should use fp_evaluate fallback
            results.append(None)
            continue

        outcome_str = ev.get("outcome", "").lower()
        reason = ev.get("reason", "")

        if outcome_str == "pass":
            outcome = CheckOutcome.PASS
        elif outcome_str == "fail":
            outcome = CheckOutcome.FAIL
        else:
            outcome = CheckOutcome.ERROR
            reason = f"Unexpected outcome '{outcome_str}': {reason}"

        results.append(
            CheckResult(
                name=check.name,
                outcome=outcome,
                required=check.required,
                check_type=check.check_type,
                functional_unit=check.functional_unit,
                message=f"[batched] {reason}",
            )
        )

    return results


def _extract_agent_checks(edge_config: dict) -> list[dict]:
    """Extract agent-type checks from edge config checklist."""
    checklist = edge_config.get("checklist", [])
    return [c for c in checklist if c.get("type") == "agent"]


def _build_prompt(
    edge: str,
    asset_content: str,
    context: str,
    agent_checks: list[dict],
    constraints: dict | None,
) -> str:
    """Build the construct+evaluate prompt. Deterministic — same inputs, same prompt."""
    parts = [
        "You are a software construction agent in the Genesis methodology.",
        f"TASK: Construct an artifact for the [{edge}] edge.",
        "",
        "EDGE CRITERIA (evaluate your output against ALL of these):",
    ]

    for check in agent_checks:
        name = check.get("name", "unnamed")
        criterion = check.get("criterion", "")
        parts.append(f"  - {name}: {criterion}")

    parts.append("")

    if asset_content:
        parts.extend(["CURRENT ASSET:", asset_content, ""])
    else:
        parts.extend(["CURRENT ASSET: (empty — generate from scratch)", ""])

    if context:
        parts.extend(["CONTEXT FROM PRIOR EDGES:", context, ""])

    if constraints:
        # Extract relevant constraint info
        project = constraints.get("project", {})
        dims = constraints.get("constraint_dimensions", {})
        if project or dims:
            parts.append("PROJECT CONSTRAINTS:")
            if project.get("name"):
                parts.append(f"  Project: {project['name']}")
            if project.get("language"):
                parts.append(f"  Language: {project['language']}")
            for dim_name, dim_val in dims.items():
                if dim_val:
                    parts.append(f"  {dim_name}: {dim_val}")
            parts.append("")

    parts.extend(
        [
            "INSTRUCTIONS:",
            "1. Construct the artifact that satisfies the edge criteria",
            "2. Self-evaluate against EVERY criterion listed above",
            "3. Tag the artifact with REQ keys (Implements: REQ-*)",
            "4. Report any issues found in the source material",
            "",
            "Respond as JSON matching the provided schema.",
        ]
    )

    return "\n".join(parts)


def _call_claude(
    prompt: str,
    model: str,
    timeout: int,
    claude_cmd: str,
) -> str | None:
    """Call claude -p and return stdout, or None on failure."""
    try:
        result = subprocess.run(
            [
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
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except subprocess.TimeoutExpired:
        return None
    except OSError:
        return None


def _parse_response(stdout: str) -> ConstructResult | None:
    """Parse Claude Code JSON response into ConstructResult. Returns None on failure."""
    try:
        outer = json.loads(stdout)

        # claude --output-format json wraps in {"type":"result","result":...}
        if isinstance(outer, dict) and "result" in outer:
            content = outer["result"]
        else:
            content = outer

        if isinstance(content, str):
            content = json.loads(content)

        artifact = content.get("artifact", "")
        if not artifact:
            return None

        evaluations = content.get("evaluations", [])
        traceability = content.get("traceability", [])
        source_findings = content.get("source_findings", [])

        return ConstructResult(
            artifact=artifact,
            evaluations=evaluations,
            traceability=traceability,
            source_findings=source_findings,
        )

    except (json.JSONDecodeError, KeyError, TypeError, AttributeError):
        return None
