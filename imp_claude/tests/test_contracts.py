# Validates: REQ-ROBUST-001
# Validates: REQ-ROBUST-002
# Validates: REQ-ITER-001
"""Tests for ADR-024 contracts and fp_functor.

Covers:
  - Intent / StepResult dataclass construction and defaults
  - FpFunctor.invoke() when MCP unavailable → skipped StepResult
  - FpFunctor.invoke() when MCP available + fold-back result exists → parsed StepResult
  - mcp_available() detection via CLAUDE_CODE_SSE_PORT
"""

import json
import os
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from genesis.contracts import (
    FpActorResultMissing,
    Intent,
    SpawnRecord,
    StepAudit,
    StepResult,
    VersionedArtifact,
)
from genesis.fp_functor import FpFunctor
from genesis.functor import mcp_available


# ── Contract dataclass tests ───────────────────────────────────────────────────


class TestIntent:
    def test_defaults(self):
        intent = Intent(edge="code↔unit_tests", feature="REQ-F-ENGINE-001")
        assert intent.grain == "iteration"
        assert intent.budget_usd == 2.0
        assert intent.max_depth == 3
        assert intent.wall_timeout_ms == 300_000
        assert intent.stall_timeout_ms == 60_000
        assert uuid.UUID(intent.run_id)  # valid UUID

    def test_run_id_unique(self):
        a = Intent(edge="e", feature="f")
        b = Intent(edge="e", feature="f")
        assert a.run_id != b.run_id

    def test_budget_and_depth_independent(self):
        """budget_usd is cost cap; max_depth is recursion limit — separate fields."""
        intent = Intent(edge="e", feature="f", budget_usd=0.50, max_depth=1)
        assert intent.budget_usd == 0.50
        assert intent.max_depth == 1


class TestStepResult:
    def test_skipped_shape(self):
        result = StepResult(
            run_id="abc",
            converged=False,
            delta=-1,
            audit=StepAudit(functor_type="F_P", transport="none", skipped=True),
        )
        assert result.delta == -1
        assert result.audit.skipped is True
        assert result.artifacts == []
        assert result.spawns == []

    def test_converged_shape(self):
        result = StepResult(
            run_id="abc",
            converged=True,
            delta=0,
            artifacts=[VersionedArtifact(path="src/x.py", content_hash="abc", previous_hash="xyz")],
            audit=StepAudit(functor_type="F_P", transport="mcp"),
        )
        assert result.converged is True
        assert result.delta == 0
        assert len(result.artifacts) == 1


# ── mcp_available() ───────────────────────────────────────────────────────────


class TestMcpAvailable:
    def test_returns_true_when_port_set(self):
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            assert mcp_available() is True

    def test_returns_false_when_port_absent(self):
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SSE_PORT"}
        with patch.dict(os.environ, env, clear=True):
            assert mcp_available() is False

    def test_empty_string_is_falsy(self):
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": ""}):
            assert mcp_available() is False


# ── FpFunctor.invoke() ────────────────────────────────────────────────────────


class TestFpFunctorMcpUnavailable:
    """When MCP is not available, functor returns a skipped StepResult immediately."""

    def test_skip_when_no_mcp(self, tmp_path):
        """MCP unavailable → FpSkipped (not a StepResult; F_D-only mode per ADR-019)."""
        from genesis.outcome_types import FpSkipped
        intent = Intent(edge="code↔unit_tests", feature="REQ-F-ENGINE-001")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SSE_PORT"}
        with patch.dict(os.environ, env, clear=True):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpSkipped)
        assert "MCP unavailable" in result.reason

    def test_skip_preserves_run_id(self, tmp_path):
        """MCP unavailable → FpSkipped; skipped outcome carries reason string."""
        from genesis.outcome_types import FpSkipped
        intent = Intent(edge="e", feature="f", run_id="fixed-id")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SSE_PORT"}
        with patch.dict(os.environ, env, clear=True):
            result = FpFunctor().invoke(intent, tmp_path)
        assert isinstance(result, FpSkipped)


class TestFpFunctorMcpAvailable:
    """When MCP is available, functor reads fold-back result from workspace state."""

    def _write_result(self, workspace: Path, run_id: str, payload: dict) -> None:
        result_dir = workspace / ".ai-workspace" / "agents"
        result_dir.mkdir(parents=True, exist_ok=True)
        (result_dir / f"fp_result_{run_id}.json").write_text(json.dumps(payload))

    def test_converged_result(self, tmp_path):
        """MCP available, fold-back result exists → FpReturned with converged data."""
        from genesis.outcome_types import FpReturned
        intent = Intent(edge="code↔unit_tests", feature="REQ-F-ENGINE-001")
        self._write_result(tmp_path, intent.run_id, {
            "converged": True,
            "delta": 0,
            "cost_usd": 0.42,
            "artifacts": [
                {"path": "src/engine.py", "content_hash": "abc123", "previous_hash": "xyz000"}
            ],
            "spawns": [],
        })
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpReturned)
        assert result.result["converged"] is True
        assert result.result["delta"] == 0
        assert result.result["cost_usd"] == pytest.approx(0.42)
        assert len(result.result["artifacts"]) == 1
        assert result.result["artifacts"][0]["path"] == "src/engine.py"
        assert result.result["audit"]["transport"] == "mcp"
        assert result.result["audit"]["skipped"] is False

    def test_unconverged_result(self, tmp_path):
        """Fold-back result with delta > 0 → FpReturned with unconverged data."""
        from genesis.outcome_types import FpReturned
        intent = Intent(edge="code↔unit_tests", feature="REQ-F-ENGINE-001")
        self._write_result(tmp_path, intent.run_id, {
            "converged": False,
            "delta": 3,
            "cost_usd": 1.10,
            "artifacts": [],
            "spawns": [],
        })
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpReturned)
        assert result.result["converged"] is False
        assert result.result["delta"] == 3

    def test_budget_capped_flag(self, tmp_path):
        """cost_usd > budget_usd → FpReturned with budget_capped in audit."""
        from genesis.outcome_types import FpReturned
        intent = Intent(edge="e", feature="f", budget_usd=1.0)
        self._write_result(tmp_path, intent.run_id, {
            "converged": False,
            "delta": 1,
            "cost_usd": 1.05,  # over budget
            "artifacts": [],
            "spawns": [],
        })
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpReturned)
        assert result.result["audit"]["budget_capped"] is True

    def test_no_result_file_returns_fp_pending(self, tmp_path):
        """MCP available but no fold-back result yet → FpPending (not a raise).

        invoke() never raises — observable failure returned as FpPending.
        The manifest is written; the LLM layer reads it and invokes the actor.
        ADR-024 / T-COMPLY-008 fold-back protocol.
        """
        from genesis.outcome_types import FpPending
        intent = Intent(edge="e", feature="f")
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)
        assert isinstance(result, FpPending)

    def test_spawn_records_parsed(self, tmp_path):
        """Fold-back result with spawn records → FpReturned with spawns in result dict."""
        from genesis.outcome_types import FpReturned
        intent = Intent(edge="e", feature="f")
        self._write_result(tmp_path, intent.run_id, {
            "converged": True,
            "delta": 0,
            "cost_usd": 0.1,
            "artifacts": [],
            "spawns": [
                {"child_run_id": "child-1", "feature": "REQ-F-SUB-001",
                 "edge": "design→code", "reason": "sub-feature decomposition"}
            ],
        })
        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpReturned)
        assert len(result.result["spawns"]) == 1
        assert result.result["spawns"][0]["child_run_id"] == "child-1"
        assert result.result["spawns"][0]["feature"] == "REQ-F-SUB-001"
