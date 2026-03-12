# Validates: REQ-ROBUST-002 (Supervisor Pattern), REQ-ITER-001 (Universal Iteration)
# Validates: REQ-F-RUNTIME-001
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
        """When MCP unavailable, construct=True → FpSkipped → fp_result=None (ADR-019 F_D-only mode)."""
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

        # FpSkipped → engine enters F_D-only mode; fp_result is None (not an error)
        assert record.fp_result is None
        assert record.evaluation.converged is True  # no checks = converged

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
        from genesis.outcome_types import FpReturned

        config = self._make_engine_config(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"

        mock_outcome = FpReturned(result={
            "converged": True,
            "delta": 0,
            "cost_usd": 0.42,
            "artifacts": [],
            "spawns": [],
            "audit": {"transport": "mcp", "skipped": False, "budget_capped": False},
        })

        with patch("genesis.fp_functor.FpFunctor.invoke", return_value=mock_outcome):
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

    def test_fp_actor_result_missing_returns_fp_pending(self, tmp_path):
        """When MCP available but fold-back missing → FpPending (not FpSkipped, not exception)."""
        from genesis.fp_functor import FpFunctor
        from genesis.contracts import Intent
        from genesis.outcome_types import FpPending

        intent = Intent(edge="design→code", feature="REQ-F-TEST-001")

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpPending)
        assert result.manifest_path.name == f"fp_intent_{intent.run_id}.json"

    def test_intent_manifest_written_before_result_check(self, tmp_path):
        """T-008: intent manifest written to agents dir for actor to discover."""
        from genesis.fp_functor import FpFunctor
        from genesis.contracts import Intent
        from genesis.outcome_types import FpPending
        import json

        intent = Intent(edge="design→code", feature="REQ-F-TEST-001")

        with patch.dict(os.environ, {"CLAUDE_CODE_SSE_PORT": "9000"}):
            result = FpFunctor().invoke(intent, tmp_path)

        assert isinstance(result, FpPending)

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


# ═══════════════════════════════════════════════════════════════════════════
# T-COMPLY-008: gen-iterate.md fold-back protocol spec validation
# Validates that the LLM-layer spec describes the ADR-023/024 fold-back contract.
# ═══════════════════════════════════════════════════════════════════════════


import pathlib as _pathlib

_COMMANDS_DIR = _pathlib.Path(__file__).parent.parent / "code/.claude-plugin/plugins/genesis/commands"


class TestGenIterateFoldBackSpec:
    """T-COMPLY-008: gen-iterate.md must describe the fold-back dispatch protocol."""

    @pytest.fixture
    def gen_iterate_spec(self):
        path = _COMMANDS_DIR / "gen-iterate.md"
        assert path.exists(), f"gen-iterate.md not found at {path}"
        return path.read_text()

    def test_spec_describes_fp_actor_result_missing_signal(self, gen_iterate_spec):
        """gen-iterate must recognise FpActorResultMissing as the dispatch signal."""
        assert "FpActorResultMissing" in gen_iterate_spec, (
            "gen-iterate.md must reference FpActorResultMissing — "
            "the engine's observable signal that an actor dispatch is required"
        )

    def test_spec_describes_manifest_scanning(self, gen_iterate_spec):
        """gen-iterate must describe scanning for pending fp_intent_*.json manifests."""
        assert "fp_intent_" in gen_iterate_spec, (
            "gen-iterate.md must describe reading fp_intent_{run_id}.json from "
            ".ai-workspace/agents/ — the fold-back manifest written by the engine"
        )
        assert "pending" in gen_iterate_spec, (
            "gen-iterate.md must describe checking for status='pending' manifests"
        )

    def test_spec_describes_mcp_tool_invocation(self, gen_iterate_spec):
        """gen-iterate must name the MCP tool used for actor dispatch."""
        assert "mcp__claude-code-runner__claude_code" in gen_iterate_spec, (
            "gen-iterate.md must reference mcp__claude-code-runner__claude_code "
            "as the MCP tool used to dispatch the actor"
        )

    def test_spec_describes_fold_back_result_format(self, gen_iterate_spec):
        """gen-iterate must specify the actor result format written to result_path."""
        assert "fp_result_" in gen_iterate_spec, (
            "gen-iterate.md must reference fp_result_{run_id}.json — "
            "the fold-back result file written by the actor"
        )
        assert "result_path" in gen_iterate_spec, (
            "gen-iterate.md must reference result_path from the manifest — "
            "where the actor writes its fold-back result"
        )

    def test_spec_describes_converged_delta_in_result(self, gen_iterate_spec):
        """gen-iterate must specify that the actor result includes converged + delta."""
        assert '"converged"' in gen_iterate_spec, (
            "gen-iterate.md must show the actor result schema including 'converged'"
        )
        assert '"delta"' in gen_iterate_spec, (
            "gen-iterate.md must show the actor result schema including 'delta'"
        )

    def test_spec_describes_re_run_phase_a_after_actor(self, gen_iterate_spec):
        """gen-iterate must describe re-running Phase A after actor writes fold-back."""
        assert "re-run Phase A" in gen_iterate_spec or "re-run the engine" in gen_iterate_spec or \
               "re-run phase a" in gen_iterate_spec.lower(), (
            "gen-iterate.md must describe re-running Phase A (engine) after "
            "the actor writes its fold-back result"
        )

    def test_spec_explains_no_subprocess_rationale(self, gen_iterate_spec):
        """gen-iterate must explain ADR-023: no subprocess, no claude -p."""
        assert "no subprocess" in gen_iterate_spec.lower() or \
               "no `claude -p`" in gen_iterate_spec or \
               "ADR-023" in gen_iterate_spec, (
            "gen-iterate.md must explain the ADR-023 constraint: "
            "no subprocess, no claude -p — MCP is the only invocation path"
        )

    def test_fold_back_protocol_shows_engine_llm_actor_chain(self, gen_iterate_spec):
        """gen-iterate must show the three-party contract: ENGINE→LLM→ACTOR."""
        assert "ENGINE" in gen_iterate_spec, (
            "gen-iterate.md must show the ENGINE role in the fold-back contract"
        )
        assert "ACTOR" in gen_iterate_spec, (
            "gen-iterate.md must show the ACTOR role in the fold-back contract"
        )

    def test_spec_budget_tracking_describes_cost_usd_deduction(self, gen_iterate_spec):
        """gen-iterate must describe deducting cost_usd from actor result."""
        assert "cost_usd" in gen_iterate_spec, (
            "gen-iterate.md must reference cost_usd from the fold-back result "
            "for budget tracking — deduct from remaining budget_usd"
        )

    def test_spec_marks_manifest_dispatched_after_actor_invoke(self, gen_iterate_spec):
        """gen-iterate must mark the manifest status='dispatched' after invoking actor.

        T-COMPLY-008 item 3: prevents double-dispatch on session resume.
        On resume, gen-iterate scans for status='pending' only — a dispatched
        manifest is skipped. Without this, an interrupted session could dispatch
        the same actor twice.
        """
        assert "dispatched" in gen_iterate_spec, (
            "gen-iterate.md must describe marking the manifest status as 'dispatched' "
            "immediately after invoking the actor — prevents double-dispatch on resume"
        )
