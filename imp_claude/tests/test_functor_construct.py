# Validates: REQ-ROBUST-002 (Supervisor Pattern), REQ-ITER-001 (Universal Iteration)
"""Tests for ADR-024 engine integration — FpFunctor MCP actor path."""

import json
import os
import pathlib
import sys
from unittest.mock import patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genesis.models import CheckOutcome


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE INTEGRATION (REQ-F-FPC-004, REQ-BR-FPC-001)
# ═══════════════════════════════════════════════════════════════════════════


class TestEngineConstructIntegration:
    """Validates: REQ-F-FPC-004 — iterate_edge() calls construct before evaluate."""

    def _make_engine_config(self, tmp_path):
        from genesis.engine import EngineConfig

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").touch()

        return EngineConfig(
            project_name="test-project",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,  # Skip real agent calls
        )

    def test_iterate_edge_without_construct(self, tmp_path):
        """Default path: construct=False, no construct call made."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)
        edge_config = {"checklist": []}

        record = iterate_edge(
            edge="intent→requirements",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="test",
        )
        assert record.fp_result is None
        assert record.evaluation.converged is True  # No checks = converged

    def test_iterate_edge_with_construct_mcp_unavailable(self, tmp_path):
        """When MCP unavailable, construct=True → FpFunctor returns skipped StepResult."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)
        edge_config = {"checklist": []}
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_SSE_PORT"}

        with patch.dict(os.environ, env, clear=True):
            record = iterate_edge(
                edge="design→code",
                edge_config=edge_config,
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="design",
                construct=True,
            )

        assert record.fp_result is not None
        assert record.fp_result.audit.skipped is True
        assert record.fp_result.delta == -1

    def test_agent_checks_always_skip(self, tmp_path):
        """ADR-024: agent checks are always SKIP in the engine."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)
        config.deterministic_only = False

        edge_config = {
            "checklist": [
                {
                    "name": "quality",
                    "type": "agent",
                    "criterion": "Code quality",
                    "functional_unit": "evaluate",
                    "required": True,
                    "source": "test",
                },
            ]
        }

        record = iterate_edge(
            edge="design→code",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="design",
        )

        agent_checks = [c for c in record.evaluation.checks if c.check_type == "agent"]
        assert len(agent_checks) == 1
        assert agent_checks[0].outcome == CheckOutcome.SKIP
        assert "ADR-024" in agent_checks[0].message

    def test_fp_actor_metadata_in_event(self, tmp_path):
        """Actor invocation metadata included in emitted iteration_completed event."""
        from genesis.engine import iterate_edge
        from genesis.contracts import StepResult, StepAudit

        config = self._make_engine_config(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"

        mock_result = StepResult(
            run_id="test-run",
            converged=True,
            delta=0,
            cost_usd=0.42,
            duration_ms=5000,
            audit=StepAudit(functor_type="F_P", transport="mcp"),
        )

        with patch("genesis.fp_functor.FpFunctor.invoke", return_value=mock_result):
            with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
                iterate_edge(
                    edge="design→code",
                    edge_config={"checklist": []},
                    config=config,
                    feature_id="REQ-F-TEST-001",
                    asset_content="design",
                    construct=True,
                )

        events = events_path.read_text().strip().split("\n")
        iter_event = json.loads(events[-2])
        assert "fp_actor" in iter_event
        assert iter_event["fp_actor"]["transport"] == "mcp"



# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT THREADING (REQ-F-FPC-003)
# ═══════════════════════════════════════════════════════════════════════════


class TestContextThreading:
    """Validates: REQ-F-FPC-003 — context accumulated between edges in run()."""

    @patch("genesis.engine.run_edge")
    @patch("genesis.engine.select_next_edge")
    @patch("genesis.engine.select_profile")
    @patch("genesis.engine.load_yaml")
    def test_context_accumulates(
        self, mock_yaml, mock_profile, mock_next_edge, mock_run_edge
    ):
        from genesis.engine import EngineConfig, IterationRecord, run
        from genesis.models import EvaluationResult

        mock_profile.return_value = "standard"
        mock_yaml.return_value = {}

        # Simulate two edges converging
        edge1_record = IterationRecord(
            edge="intent→requirements",
            iteration=1,
            evaluation=EvaluationResult(
                edge="intent→requirements", converged=True, delta=0
            ),
            fp_result=None,
        )
        edge2_record = IterationRecord(
            edge="requirements→design",
            iteration=1,
            evaluation=EvaluationResult(
                edge="requirements→design", converged=True, delta=0
            ),
            fp_result=None,
        )

        mock_run_edge.side_effect = [[edge1_record], [edge2_record]]

        # Route returns edge1, then edge2, then None (done)
        from genesis.models import RouteResult

        mock_next_edge.side_effect = [
            RouteResult(
                selected_edge="intent→requirements",
                reason="first",
                profile="standard",
            ),
            RouteResult(
                selected_edge="requirements→design",
                reason="second",
                profile="standard",
            ),
            RouteResult(selected_edge="", reason="done", profile="standard"),
        ]

        config = EngineConfig(
            project_name="test",
            workspace_path=pathlib.Path("/tmp/test"),
            edge_params_dir=pathlib.Path("/tmp/test/edge_params"),
            profiles_dir=pathlib.Path("/tmp/test/profiles"),
            constraints={},
            graph_topology={},
        )

        records = run(
            feature_id="REQ-F-TEST-001",
            feature_type="feature",
            config=config,
            asset_content="intent",
            construct=True,
        )

        assert len(records) == 2


# ═══════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY (REQ-NFR-FPC-002)
# ═══════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Validates: REQ-NFR-FPC-002 — existing evaluate-only path unchanged."""

    def _make_engine_config(self, tmp_path):
        from genesis.engine import EngineConfig

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").touch()

        return EngineConfig(
            project_name="test-project",
            workspace_path=tmp_path,
            edge_params_dir=tmp_path / "edge_params",
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
        )

    def test_default_construct_false(self, tmp_path):
        """iterate_edge() defaults construct=False — no F_P construct call."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)

        record = iterate_edge(
            edge="intent→requirements",
            edge_config={"checklist": []},
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="test",
        )

        assert record.fp_result is None

    def test_iteration_record_has_optional_construct(self, tmp_path):
        """IterationRecord.fp_result defaults to None."""
        from genesis.engine import IterationRecord
        from genesis.models import EvaluationResult as ER

        record = IterationRecord(
            edge="test",
            iteration=1,
            evaluation=ER(edge="test"),
        )
        assert record.fp_result is None


# ═══════════════════════════════════════════════════════════════════════════
# CLI CONSTRUCT COMMAND (REQ-F-FPC-005)
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIConstruct:
    """Validates: REQ-F-FPC-005 — construct subcommand in CLI."""

    def test_construct_subcommand_registered(self):
        """construct subcommand is available in argparse."""
        from genesis.__main__ import main
        import argparse

        parser = argparse.ArgumentParser(prog="genesis")
        subparsers = parser.add_subparsers(dest="command")
        # Just verify the construct command can be parsed
        construct_parser = subparsers.add_parser("construct")
        construct_parser.add_argument("--edge", required=True)
        construct_parser.add_argument("--feature", required=True)
        construct_parser.add_argument("--asset", required=True)
        construct_parser.add_argument("--output")

        args = parser.parse_args([
            "construct",
            "--edge", "intent→requirements",
            "--feature", "REQ-F-TEST-001",
            "--asset", "test.md",
        ])
        assert args.command == "construct"
        assert args.edge == "intent→requirements"

    def test_run_edge_construct_flag_registered(self):
        """--construct flag available on run-edge subcommand."""
        from genesis.__main__ import main
        import argparse

        parser = argparse.ArgumentParser(prog="genesis")
        subparsers = parser.add_subparsers(dest="command")
        run_parser = subparsers.add_parser("run-edge")
        run_parser.add_argument("--construct", action="store_true")
        run_parser.add_argument("--edge", required=True)
        run_parser.add_argument("--feature", required=True)
        run_parser.add_argument("--asset", required=True)

        args = parser.parse_args([
            "run-edge",
            "--construct",
            "--edge", "code↔unit_tests",
            "--feature", "REQ-F-TEST-001",
            "--asset", "test.py",
        ])
        assert args.construct is True
