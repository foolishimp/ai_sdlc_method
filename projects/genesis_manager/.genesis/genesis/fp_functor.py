# Implements: REQ-ROBUST-001 (Actor Isolation), REQ-ROBUST-002 (Supervisor Pattern for F_P Calls), REQ-ITER-001 (Universal Iteration)
# Implements: REQ-F-RUNTIME-001
# Design ADRs: ADR-019 (F_D-only evaluation path — skipped=True is valid mode, not degraded), ADR-023 (no subprocess / no claude -p), ADR-024 (recursive actor model — fold-back file is the transport contract)
"""ADR-024 F_P functor — invoke actor via MCP with constrained Intent.

MCP unavailable → return StepResult(skipped=True). F_D-only mode, not an error.
MCP available but no result → raise FpActorResultMissing. Observable failure.
No subprocess fallback. No claude -p. Ever.

The actor:
  1. Receives the Intent (edge, feature, failures, constraints, budget_usd)
  2. Runs iterate() autonomously at grain="iteration"
  3. Uses full tool access to read files, modify code, run tests, verify output
  4. Self-evaluates against edge criteria
  5. Returns StepResult via fold-back to the engine

The engine's role after actor invocation: run F_D checks only.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

from .contracts import (
    FpActorResultMissing,
    Intent,
    SpawnRecord,
    StepAudit,
    StepResult,
    VersionedArtifact,
)
from .functor import mcp_available
from .outcome_types import FpFailed, FpOutcome, FpPending, FpReturned, FpSkipped


class FpFunctor:
    """F_P functor implementation — MCP actor invocation."""

    def invoke(self, intent: Intent, state: Path) -> FpOutcome:
        """Invoke the F_P actor via MCP. Returns FpOutcome (never raises).

        FpSkipped  — MCP unavailable; F_D-only mode (ADR-019, not an error)
        FpPending  — manifest written; actor not yet invoked
        FpReturned — actor completed; fold-back result available
        FpFailed   — actor invocation or result-parse failed (observable)
        """
        if not mcp_available():
            return FpSkipped(reason="MCP unavailable — F_D-only mode (ADR-019)")

        prompt = _build_actor_prompt(intent, state)
        t0 = time.monotonic()

        try:
            raw = _mcp_invoke(prompt, state, intent)
        except FpActorResultMissing as exc:
            # Manifest written but no fold-back result yet — pending, not failed
            agents_dir = state / ".ai-workspace" / "agents"
            manifest_path = agents_dir / f"fp_intent_{intent.run_id}.json"
            return FpPending(manifest_path=manifest_path)
        except Exception as exc:
            import traceback as _tb
            return FpFailed(error=str(exc), traceback=_tb.format_exc())

        duration_ms = int((time.monotonic() - t0) * 1000)
        try:
            step_result = _parse_actor_result(intent, raw, duration_ms, state)
            return FpReturned(result={
                "converged": step_result.converged,
                "delta": step_result.delta,
                "cost_usd": step_result.cost_usd,
                "artifacts": [
                    {"path": a.path, "content_hash": a.content_hash, "previous_hash": a.previous_hash}
                    for a in step_result.artifacts
                ],
                "spawns": [
                    {"child_run_id": s.child_run_id, "feature": s.feature, "edge": s.edge, "reason": s.reason}
                    for s in step_result.spawns
                ],
                "audit": {
                    "transport": step_result.audit.transport if step_result.audit else "mcp",
                    "skipped": False,
                    "budget_capped": step_result.audit.budget_capped if step_result.audit else False,
                },
            })
        except Exception as exc:
            import traceback as _tb
            return FpFailed(error=f"result parse failed: {exc}", traceback=_tb.format_exc())


# ── Internal helpers ──────────────────────────────────────────────────────────


def _build_actor_prompt(intent: Intent, workspace: Path) -> str:
    """Build the mandate delivered to the actor."""
    failures_section = ""
    if intent.failures:
        failures_section = "\n\n## Prior F_D Failures\n" + "\n".join(
            f"- {f}" for f in intent.failures
        )

    constraints_section = ""
    if intent.constraints:
        constraints_section = "\n\n## Constraints\n" + "\n".join(
            f"- {k}: {v}" for k, v in intent.constraints.items()
        )

    return f"""# Actor Mandate

**Edge**: {intent.edge}
**Feature**: {intent.feature}
**Grain**: {intent.grain}
**Run ID**: {intent.run_id}
**Workspace**: {workspace}
**Budget**: ${intent.budget_usd:.2f}
**Max Depth**: {intent.max_depth}{failures_section}{constraints_section}

## Your Task

You are a recursive actor. Iterate on the above edge until the F_D checklist
passes. Use your full tool access — read files, write code, run tests.

When done, emit a JSON result to stdout:
```json
{{
  "converged": true|false,
  "delta": <int>,
  "cost_usd": <float>,
  "artifacts": [{{"path": "<str>", "content_hash": "<sha256>", "previous_hash": "<sha256>"}}],
  "spawns": []
}}
```
"""


def _mcp_invoke(prompt: str, workspace: Path, intent: Intent) -> dict:
    """Drive the F_P actor via the fold-back protocol.

    Architecture: The Python engine cannot issue MCP tool calls — MCP is the
    LLM layer's capability (ADR-023: no subprocess, no claude -p, ever).
    Instead, the engine uses the fold-back protocol:

    1. ENGINE writes intent manifest → `.ai-workspace/agents/fp_intent_{run_id}.json`
    2. ENGINE checks for fold-back result → `.ai-workspace/agents/fp_result_{run_id}.json`
    3. ACTOR (invoked by gen-iterate via MCP tool call) reads the intent manifest,
       does the work, and writes the fold-back result.

    The fold-back protocol makes the intent durable — if gen-iterate can see the
    workspace (it always can, it owns the session), it can discover pending intents
    and invoke the actor. T-008 implements this handshake.

    Future: when a Python MCP client library is available, this function will issue
    the tool call directly: `mcp_client.call_tool("claude_code", {...})`.
    Until then, the fold-back file IS the actor invocation contract.
    """
    agents_dir = workspace / ".ai-workspace" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Write intent manifest — actor reads this to understand its mandate.
    manifest = {
        "run_id": intent.run_id,
        "edge": intent.edge,
        "feature": intent.feature,
        "grain": intent.grain,
        "budget_usd": intent.budget_usd,
        "max_depth": intent.max_depth,
        "failures": intent.failures,
        "constraints": intent.constraints,
        "prompt": prompt,
        "result_path": str(agents_dir / f"fp_result_{intent.run_id}.json"),
        "status": "pending",
    }
    intent_path = agents_dir / f"fp_intent_{intent.run_id}.json"
    intent_path.write_text(json.dumps(manifest, indent=2))

    # Step 2: Check for fold-back result (actor may have already run in this session).
    result_path = agents_dir / f"fp_result_{intent.run_id}.json"
    if result_path.exists():
        return json.loads(result_path.read_text())

    # No fold-back result found — raise observable failure (not a silent skip).
    # gen-iterate reads the intent manifest and invokes the actor via MCP tool call.
    # The actor writes the result to result_path, then the engine retries on next iteration.
    raise FpActorResultMissing(
        f"Actor not yet invoked (run_id={intent.run_id}). "
        f"Intent written to: {intent_path}"
    )


def _parse_actor_result(
    intent: Intent, raw: dict, duration_ms: int, workspace: Path
) -> StepResult:
    """Parse the actor's fold-back result into a StepResult."""
    artifacts = [
        VersionedArtifact(
            path=a["path"],
            content_hash=a.get("content_hash", ""),
            previous_hash=a.get("previous_hash", ""),
        )
        for a in raw.get("artifacts", [])
    ]
    spawns = [
        SpawnRecord(
            child_run_id=s.get("child_run_id", ""),
            feature=s.get("feature", intent.feature),
            edge=s.get("edge", intent.edge),
            reason=s.get("reason", ""),
        )
        for s in raw.get("spawns", [])
    ]
    return StepResult(
        run_id=intent.run_id,
        converged=raw.get("converged", False),
        delta=raw.get("delta", -1),
        artifacts=artifacts,
        spawns=spawns,
        cost_usd=raw.get("cost_usd", 0.0),
        duration_ms=duration_ms,
        workspace=workspace,
        audit=StepAudit(
            functor_type="F_P",
            transport="mcp",
            skipped=False,
            budget_capped=raw.get("cost_usd", 0.0) >= intent.budget_usd,
        ),
    )
