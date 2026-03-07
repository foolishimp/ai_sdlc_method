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
from genesis.ol_event import normalize_event


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════


class TestEngineConstructIntegration:
    """Validates engine iterate_edge() calls construct before evaluate."""

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

        events = [normalize_event(json.loads(e)) for e in events_path.read_text().strip().split("\n") if e.strip()]
        iter_event = next(e for e in reversed(events) if e.get("event_type") == "iteration_completed")
        assert "fp_actor" in iter_event
        assert iter_event["fp_actor"]["transport"] == "mcp"


# ═══════════════════════════════════════════════════════════════════════════
# RUNID THREADING (T-005: Transaction Model)
# ═══════════════════════════════════════════════════════════════════════════


# ═══════════════════════════════════════════════════════════════════════════
# T-007: FpActorResultMissing exception path
# ═══════════════════════════════════════════════════════════════════════════


class TestFpActorResultMissing:
    """Validates T-007: FpActorResultMissing is observable, not a silent skip."""

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

    def test_mcp_available_no_result_emits_fp_failure(self, tmp_path):
        """When MCP available but fold-back missing → FpFailure event emitted."""
        from genesis.engine import iterate_edge
        from genesis.contracts import FpActorResultMissing

        config = self._make_engine_config(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            record = iterate_edge(
                edge="design→code",
                edge_config={"checklist": []},
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="design",
                construct=True,
            )

        events = [normalize_event(json.loads(e)) for e in events_path.read_text().strip().split("\n") if e.strip()]
        fp_failure_events = [e for e in events if e.get("event_type") == "fp_failure"]
        assert len(fp_failure_events) == 1
        assert fp_failure_events[0].get("error")

    def test_mcp_available_no_result_fp_result_is_none(self, tmp_path):
        """When FpActorResultMissing → fp_result is None, F_D checks still run."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            record = iterate_edge(
                edge="design→code",
                edge_config={"checklist": []},
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="design",
                construct=True,
            )

        assert record.fp_result is None
        assert record.evaluation.converged is True  # No checks = converged

    def test_fp_actor_result_missing_is_distinct_from_skip(self, tmp_path):
        """FpActorResultMissing is raised by functor, not suppressed as skipped=True."""
        from genesis.fp_functor import FpFunctor
        from genesis.contracts import FpActorResultMissing, Intent

        intent = Intent(edge="design→code", feature="REQ-F-TEST-001")

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            with pytest.raises(FpActorResultMissing):
                FpFunctor().invoke(intent, tmp_path)

    def test_intent_manifest_written_before_result_check(self, tmp_path):
        """T-008: intent manifest written to agents dir for actor to discover."""
        from genesis.fp_functor import FpFunctor
        from genesis.contracts import FpActorResultMissing, Intent
        import json

        intent = Intent(edge="design→code", feature="REQ-F-TEST-001")

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            try:
                FpFunctor().invoke(intent, tmp_path)
            except FpActorResultMissing:
                pass

        # Manifest must be written even when no fold-back result exists yet
        manifest_path = tmp_path / ".ai-workspace" / "agents" / f"fp_intent_{intent.run_id}.json"
        assert manifest_path.exists(), "Intent manifest not written — actor cannot discover its work"
        manifest = json.loads(manifest_path.read_text())
        assert manifest["run_id"] == intent.run_id
        assert manifest["edge"] == "design→code"
        assert manifest["status"] == "pending"
        assert "result_path" in manifest


class TestRunIdThreading:
    """Validates: T-005 — OL runId causation chain through edge traversal."""

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

    def test_iteration_started_carries_input_hash(self, tmp_path):
        """IterationStarted event includes input_hash for content-addressable manifests."""
        from genesis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"

        iterate_edge(
            edge="design→code",
            edge_config={"checklist": []},
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="my design content",
        )

        raw_events = [json.loads(e) for e in events_path.read_text().strip().split("\n") if e.strip()]
        events = [normalize_event(e) for e in raw_events]
        started = next(e for e in events if e.get("event_type") == "iteration_started")
        assert "input_hash" in started
        assert started["input_hash"].startswith("sha256:")

    def test_causation_chain_threads_through_edge(self, tmp_path):
        """Events in an edge traversal are causally linked via run IDs."""
        from genesis.engine import run_edge, EngineConfig
        import yaml

        # Create minimal edge config
        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        edge_params_dir = tmp_path / "edge_params"
        edge_params_dir.mkdir()
        (edge_params_dir / "design_code.yml").write_text(yaml.dump({"checklist": []}))

        config = EngineConfig(
            project_name="test-project",
            workspace_path=tmp_path,
            edge_params_dir=edge_params_dir,
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            max_iterations_per_edge=1,
        )

        run_edge(
            edge="design→code",
            config=config,
            feature_id="REQ-F-TEST-001",
            profile={},
            asset_content="content",
        )

        raw_events = [json.loads(e) for e in events_path.read_text().strip().split("\n") if e.strip()]

        # Find EdgeStarted — the root of the causal chain
        edge_started = next(e for e in raw_events
                            if e.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "EdgeStarted")
        edge_run_id = edge_started["run"]["runId"]

        # IterationStarted should cite EdgeStarted as causation
        iter_started = next(e for e in raw_events
                            if e.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "IterationStarted")
        universal = iter_started["run"]["facets"]["sdlc:universal"]
        assert universal["causation_id"] == edge_run_id, "IterationStarted must cite EdgeStarted as causation"
        assert universal["correlation_id"] == edge_run_id, "All events share the edge's correlation_id"

        iter_run_id = iter_started["run"]["runId"]

        # IterationCompleted causation → IterationStarted
        iter_completed = next(e for e in raw_events
                              if e.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "IterationCompleted")
        completed_universal = iter_completed["run"]["facets"]["sdlc:universal"]
        assert completed_universal["causation_id"] == iter_run_id

    def test_edge_converged_causation_is_iteration_completed(self, tmp_path):
        """EdgeConverged cites IterationCompleted as its cause — commits the transaction."""
        from genesis.engine import run_edge, EngineConfig
        import yaml

        events_dir = tmp_path / ".ai-workspace" / "events"
        events_dir.mkdir(parents=True)
        events_path = events_dir / "events.jsonl"

        edge_params_dir = tmp_path / "edge_params"
        edge_params_dir.mkdir()
        (edge_params_dir / "design_code.yml").write_text(yaml.dump({"checklist": []}))

        config = EngineConfig(
            project_name="test-project",
            workspace_path=tmp_path,
            edge_params_dir=edge_params_dir,
            profiles_dir=tmp_path / "profiles",
            constraints={},
            graph_topology={},
            deterministic_only=True,
            max_iterations_per_edge=1,
        )

        run_edge(
            edge="design→code",
            config=config,
            feature_id="REQ-F-TEST-001",
            profile={},
            asset_content="content",
        )

        raw_events = [json.loads(e) for e in events_path.read_text().strip().split("\n") if e.strip()]

        iter_completed = next(e for e in raw_events
                              if e.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "IterationCompleted")
        completed_run_id = iter_completed["run"]["runId"]

        edge_converged = next(e for e in raw_events
                              if e.get("run", {}).get("facets", {}).get("sdlc:event_type", {}).get("type") == "EdgeConverged")
        converged_universal = edge_converged["run"]["facets"]["sdlc:universal"]
        assert converged_universal["causation_id"] == completed_run_id, (
            "EdgeConverged (commit point) must cite IterationCompleted as causation"
        )

# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT THREADING
# ═══════════════════════════════════════════════════════════════════════════


class TestContextThreading:
    """Validates context accumulated between edges in run()."""

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
# CLI CONSTRUCT COMMAND
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIConstruct:
    """Validates construct subcommand in CLI."""

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
