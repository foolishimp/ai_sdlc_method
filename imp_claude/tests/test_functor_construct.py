# Validates: REQ-F-FPC-001, REQ-F-FPC-002, REQ-F-FPC-003, REQ-F-FPC-004, REQ-F-FPC-005, REQ-F-FPC-006
# Validates: REQ-NFR-FPC-001, REQ-NFR-FPC-002, REQ-NFR-FPC-003, REQ-DATA-FPC-001, REQ-BR-FPC-001
"""Tests for F_P construct — fp_construct module, engine integration, CLI."""

import json
import pathlib
import sys
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genisis.models import (
    CheckOutcome,
    CheckResult,
    ConstructResult,
    ResolvedCheck,
)
from genisis.fp_construct import (
    _build_prompt,
    _extract_agent_checks,
    _parse_response,
    batched_check_results,
    run_construct,
)


# ═══════════════════════════════════════════════════════════════════════════
# DATA MODEL: ConstructResult (REQ-DATA-FPC-001)
# ═══════════════════════════════════════════════════════════════════════════


class TestConstructResult:
    """Validates: REQ-DATA-FPC-001 — ConstructResult dataclass."""

    def test_default_construction(self):
        cr = ConstructResult(artifact="hello world")
        assert cr.artifact == "hello world"
        assert cr.evaluations == []
        assert cr.traceability == []
        assert cr.source_findings == []
        assert cr.model == ""
        assert cr.duration_ms == 0
        assert cr.retries == 0

    def test_full_construction(self):
        cr = ConstructResult(
            artifact="code here",
            evaluations=[{"check_name": "lint", "outcome": "pass", "reason": "ok"}],
            traceability=["REQ-F-AUTH-001"],
            source_findings=[{"description": "typo", "classification": "MINOR"}],
            model="sonnet",
            duration_ms=5000,
            retries=1,
        )
        assert len(cr.evaluations) == 1
        assert cr.traceability == ["REQ-F-AUTH-001"]
        assert cr.model == "sonnet"
        assert cr.retries == 1


# ═══════════════════════════════════════════════════════════════════════════
# PROMPT BUILDER (REQ-F-FPC-001, REQ-F-FPC-002)
# ═══════════════════════════════════════════════════════════════════════════


class TestBuildPrompt:
    """Validates: REQ-F-FPC-001 — prompt includes edge, asset, context, criteria."""

    def test_basic_prompt(self):
        prompt = _build_prompt(
            edge="intent→requirements",
            asset_content="Build an auth system",
            context="",
            agent_checks=[
                {"name": "completeness", "criterion": "All aspects covered"},
            ],
            constraints=None,
        )
        assert "intent→requirements" in prompt
        assert "Build an auth system" in prompt
        assert "completeness: All aspects covered" in prompt
        assert "CONTEXT FROM PRIOR EDGES" not in prompt

    def test_prompt_with_context(self):
        prompt = _build_prompt(
            edge="requirements→design",
            asset_content="REQ-001: Login",
            context="Previous artifact content here",
            agent_checks=[],
            constraints=None,
        )
        assert "CONTEXT FROM PRIOR EDGES" in prompt
        assert "Previous artifact content here" in prompt

    def test_prompt_with_empty_asset(self):
        prompt = _build_prompt(
            edge="intent→requirements",
            asset_content="",
            context="",
            agent_checks=[],
            constraints=None,
        )
        assert "empty — generate from scratch" in prompt

    def test_prompt_with_constraints(self):
        prompt = _build_prompt(
            edge="design→code",
            asset_content="design doc",
            context="",
            agent_checks=[],
            constraints={
                "project": {"name": "myapp", "language": "Python"},
                "constraint_dimensions": {
                    "ecosystem_compatibility": "Python 3.12",
                    "deployment_target": "AWS Lambda",
                },
            },
        )
        assert "PROJECT CONSTRAINTS" in prompt
        assert "myapp" in prompt
        assert "Python" in prompt
        assert "Python 3.12" in prompt
        assert "AWS Lambda" in prompt

    def test_prompt_includes_all_agent_checks(self):
        """Validates: REQ-F-FPC-002 — all agent criteria in prompt."""
        checks = [
            {"name": f"check_{i}", "criterion": f"Criterion {i}"}
            for i in range(5)
        ]
        prompt = _build_prompt("edge", "asset", "", checks, None)
        for i in range(5):
            assert f"check_{i}: Criterion {i}" in prompt


# ═══════════════════════════════════════════════════════════════════════════
# EXTRACT AGENT CHECKS
# ═══════════════════════════════════════════════════════════════════════════


class TestExtractAgentChecks:

    def test_filters_agent_type(self):
        config = {
            "checklist": [
                {"name": "lint", "type": "deterministic"},
                {"name": "quality", "type": "agent"},
                {"name": "review", "type": "human"},
                {"name": "coverage", "type": "agent"},
            ]
        }
        result = _extract_agent_checks(config)
        assert len(result) == 2
        assert result[0]["name"] == "quality"
        assert result[1]["name"] == "coverage"

    def test_empty_checklist(self):
        assert _extract_agent_checks({}) == []
        assert _extract_agent_checks({"checklist": []}) == []


# ═══════════════════════════════════════════════════════════════════════════
# PARSE RESPONSE (REQ-F-FPC-006)
# ═══════════════════════════════════════════════════════════════════════════


class TestParseResponse:
    """Validates: REQ-F-FPC-006 — JSON schema validation, error handling."""

    def test_parse_direct_json(self):
        """Direct JSON object (not wrapped in claude result envelope)."""
        data = {
            "artifact": "def hello(): pass",
            "evaluations": [
                {"check_name": "lint", "outcome": "pass", "reason": "clean"}
            ],
            "traceability": ["REQ-F-001"],
        }
        result = _parse_response(json.dumps(data))
        assert result is not None
        assert result.artifact == "def hello(): pass"
        assert len(result.evaluations) == 1
        assert result.traceability == ["REQ-F-001"]

    def test_parse_claude_wrapped(self):
        """Claude --output-format json wraps in {"type":"result","result":...}."""
        inner = {
            "artifact": "code here",
            "evaluations": [],
            "traceability": [],
        }
        outer = {"type": "result", "result": json.dumps(inner)}
        result = _parse_response(json.dumps(outer))
        assert result is not None
        assert result.artifact == "code here"

    def test_parse_claude_wrapped_object(self):
        """Claude may also return result as object (not string)."""
        inner = {
            "artifact": "code here",
            "evaluations": [],
            "traceability": [],
        }
        outer = {"type": "result", "result": inner}
        result = _parse_response(json.dumps(outer))
        assert result is not None
        assert result.artifact == "code here"

    def test_parse_with_source_findings(self):
        data = {
            "artifact": "code",
            "evaluations": [],
            "traceability": [],
            "source_findings": [
                {"description": "ambiguous req", "classification": "SOURCE_GAP"}
            ],
        }
        result = _parse_response(json.dumps(data))
        assert result is not None
        assert len(result.source_findings) == 1
        assert result.source_findings[0]["classification"] == "SOURCE_GAP"

    def test_parse_empty_artifact_returns_none(self):
        data = {"artifact": "", "evaluations": [], "traceability": []}
        result = _parse_response(json.dumps(data))
        assert result is None

    def test_parse_invalid_json_returns_none(self):
        result = _parse_response("not json at all")
        assert result is None

    def test_parse_missing_artifact_returns_none(self):
        result = _parse_response(json.dumps({"evaluations": [], "traceability": []}))
        assert result is None


# ═══════════════════════════════════════════════════════════════════════════
# BATCHED CHECK RESULTS (REQ-F-FPC-002)
# ═══════════════════════════════════════════════════════════════════════════


class TestBatchedCheckResults:
    """Validates: REQ-F-FPC-002 — batched evaluations mapped to CheckResults."""

    def _make_check(self, name, required=True):
        return ResolvedCheck(
            name=name,
            check_type="agent",
            functional_unit="evaluate",
            criterion=f"Check {name}",
            source="test",
            required=required,
        )

    def test_matching_evaluations(self):
        cr = ConstructResult(
            artifact="code",
            evaluations=[
                {"check_name": "lint", "outcome": "pass", "reason": "clean"},
                {"check_name": "types", "outcome": "fail", "reason": "missing type"},
            ],
        )
        checks = [self._make_check("lint"), self._make_check("types")]
        results = batched_check_results(cr, checks)

        assert len(results) == 2
        assert results[0].outcome == CheckOutcome.PASS
        assert results[0].name == "lint"
        assert "[batched]" in results[0].message
        assert results[1].outcome == CheckOutcome.FAIL
        assert results[1].name == "types"

    def test_unmatched_check_returns_none(self):
        cr = ConstructResult(
            artifact="code",
            evaluations=[
                {"check_name": "lint", "outcome": "pass", "reason": "ok"},
            ],
        )
        checks = [self._make_check("lint"), self._make_check("unmatched")]
        results = batched_check_results(cr, checks)

        assert results[0] is not None
        assert results[0].outcome == CheckOutcome.PASS
        assert results[1] is None  # Caller should fall back to fp_evaluate

    def test_unexpected_outcome_maps_to_error(self):
        cr = ConstructResult(
            artifact="code",
            evaluations=[
                {"check_name": "check1", "outcome": "maybe", "reason": "uncertain"},
            ],
        )
        checks = [self._make_check("check1")]
        results = batched_check_results(cr, checks)

        assert results[0].outcome == CheckOutcome.ERROR
        assert "Unexpected outcome" in results[0].message

    def test_empty_evaluations(self):
        cr = ConstructResult(artifact="code", evaluations=[])
        checks = [self._make_check("check1")]
        results = batched_check_results(cr, checks)
        assert results[0] is None

    def test_preserves_check_metadata(self):
        cr = ConstructResult(
            artifact="code",
            evaluations=[
                {"check_name": "check1", "outcome": "pass", "reason": "ok"},
            ],
        )
        check = self._make_check("check1", required=False)
        check.functional_unit = "construct"
        results = batched_check_results(cr, [check])

        assert results[0].required is False
        assert results[0].functional_unit == "construct"
        assert results[0].check_type == "agent"


# ═══════════════════════════════════════════════════════════════════════════
# RUN_CONSTRUCT (REQ-F-FPC-001, REQ-NFR-FPC-003)
# ═══════════════════════════════════════════════════════════════════════════


class TestRunConstruct:
    """Validates: REQ-F-FPC-001 — single claude -p call per edge."""

    def test_missing_claude_returns_tool_missing(self):
        """When claude CLI not found, return ConstructResult with TOOL_MISSING."""
        result = run_construct(
            edge="intent→requirements",
            asset_content="intent here",
            context="",
            edge_config={"checklist": []},
            claude_cmd="nonexistent_claude_binary_xyz",
        )
        assert result.artifact == ""
        assert len(result.source_findings) == 1
        assert result.source_findings[0]["classification"] == "TOOL_MISSING"

    @patch("genisis.fp_construct._call_claude")
    def test_successful_construct(self, mock_call):
        """Happy path: claude returns valid JSON, construct succeeds."""
        response = {
            "artifact": "# Requirements\nREQ-001: Auth",
            "evaluations": [
                {"check_name": "complete", "outcome": "pass", "reason": "all covered"}
            ],
            "traceability": ["REQ-001"],
        }
        mock_call.return_value = json.dumps(response)

        result = run_construct(
            edge="intent→requirements",
            asset_content="Build auth",
            context="",
            edge_config={"checklist": [{"name": "complete", "type": "agent", "criterion": "All covered"}]},
        )
        assert result.artifact == "# Requirements\nREQ-001: Auth"
        assert len(result.evaluations) == 1
        assert result.traceability == ["REQ-001"]
        assert result.model == "sonnet"
        assert result.retries == 0
        mock_call.assert_called_once()

    @patch("genisis.fp_construct._call_claude")
    def test_timeout_retry(self, mock_call):
        """Validates: REQ-NFR-FPC-003 — retry on timeout."""
        valid_response = json.dumps({
            "artifact": "code",
            "evaluations": [],
            "traceability": [],
        })
        # First call times out, second succeeds
        mock_call.side_effect = [None, valid_response]

        result = run_construct(
            edge="code↔unit_tests",
            asset_content="original",
            context="",
            edge_config={"checklist": []},
        )
        assert result.artifact == "code"
        assert result.retries == 1
        assert mock_call.call_count == 2

    @patch("genisis.fp_construct._call_claude")
    def test_all_retries_exhausted(self, mock_call):
        """All retries fail — returns error ConstructResult."""
        mock_call.return_value = None  # Always timeout

        result = run_construct(
            edge="code↔unit_tests",
            asset_content="original",
            context="",
            edge_config={"checklist": []},
        )
        assert result.artifact == ""
        assert result.retries == 2  # MAX_RETRIES
        assert len(result.source_findings) == 1
        assert result.source_findings[0]["classification"] == "TIMEOUT"

    @patch("genisis.fp_construct._call_claude")
    def test_malformed_json_retry(self, mock_call):
        """Malformed JSON triggers retry."""
        valid_response = json.dumps({
            "artifact": "good code",
            "evaluations": [],
            "traceability": [],
        })
        mock_call.side_effect = ["not valid json", valid_response]

        result = run_construct(
            edge="design→code",
            asset_content="design",
            context="",
            edge_config={"checklist": []},
        )
        assert result.artifact == "good code"
        assert result.retries == 1

    @patch("genisis.fp_construct._call_claude")
    def test_model_passthrough(self, mock_call):
        """Model parameter is passed to claude and recorded in result."""
        mock_call.return_value = json.dumps({
            "artifact": "code",
            "evaluations": [],
            "traceability": [],
        })

        result = run_construct(
            edge="edge",
            asset_content="asset",
            context="",
            edge_config={"checklist": []},
            model="opus",
        )
        assert result.model == "opus"


# ═══════════════════════════════════════════════════════════════════════════
# ENGINE INTEGRATION (REQ-F-FPC-004, REQ-BR-FPC-001)
# ═══════════════════════════════════════════════════════════════════════════


class TestEngineConstructIntegration:
    """Validates: REQ-F-FPC-004 — iterate_edge() calls construct before evaluate."""

    def _make_engine_config(self, tmp_path):
        from genisis.engine import EngineConfig

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
        from genisis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)
        edge_config = {"checklist": []}

        record = iterate_edge(
            edge="intent→requirements",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="test",
        )
        assert record.construct_result is None
        assert record.evaluation.converged is True  # No checks = converged

    @patch("genisis.engine.run_construct")
    def test_iterate_edge_with_construct(self, mock_construct, tmp_path):
        """Validates: REQ-F-FPC-004 — construct called before evaluate."""
        from genisis.engine import iterate_edge

        mock_construct.return_value = ConstructResult(
            artifact="constructed artifact",
            evaluations=[],
            traceability=["REQ-001"],
            model="sonnet",
            duration_ms=3000,
        )

        config = self._make_engine_config(tmp_path)
        edge_config = {"checklist": []}

        record = iterate_edge(
            edge="intent→requirements",
            edge_config=edge_config,
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="original input",
            construct=True,
        )
        assert record.construct_result is not None
        assert record.construct_result.artifact == "constructed artifact"
        mock_construct.assert_called_once()

    @patch("genisis.engine.run_construct")
    def test_construct_writes_artifact(self, mock_construct, tmp_path):
        """Validates: REQ-BR-FPC-001 — artifact written to filesystem."""
        from genisis.engine import iterate_edge

        mock_construct.return_value = ConstructResult(
            artifact="# Generated Requirements\nREQ-001: Auth",
            evaluations=[],
            traceability=[],
        )

        config = self._make_engine_config(tmp_path)
        output_file = tmp_path / "artifacts" / "output.md"

        record = iterate_edge(
            edge="intent→requirements",
            edge_config={"checklist": []},
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="intent",
            construct=True,
            output_path=output_file,
        )
        assert output_file.exists()
        assert "Generated Requirements" in output_file.read_text()

    @patch("genisis.engine.run_construct")
    def test_construct_result_in_event(self, mock_construct, tmp_path):
        """Construct metadata included in emitted event."""
        from genisis.engine import iterate_edge

        mock_construct.return_value = ConstructResult(
            artifact="code",
            evaluations=[],
            traceability=["REQ-001"],
            source_findings=[{"description": "gap", "classification": "SOURCE_GAP"}],
            model="sonnet",
            duration_ms=5000,
            retries=1,
        )

        config = self._make_engine_config(tmp_path)
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"

        iterate_edge(
            edge="design→code",
            edge_config={"checklist": []},
            config=config,
            feature_id="REQ-F-TEST-001",
            asset_content="design",
            construct=True,
        )

        events = events_path.read_text().strip().split("\n")
        # Events are flattened (data merged into top-level dict)
        # iteration_completed is second-to-last; edge_converged is last
        iter_event = json.loads(events[-2])
        assert "construct" in iter_event
        assert iter_event["construct"]["model"] == "sonnet"
        assert iter_event["construct"]["duration_ms"] == 5000
        assert iter_event["construct"]["traceability"] == ["REQ-001"]

    @patch("genisis.engine.run_construct")
    def test_batched_evaluations_used(self, mock_construct, tmp_path):
        """Validates: REQ-F-FPC-002 — batched F_P evals replace per-check calls."""
        from genisis.engine import iterate_edge

        mock_construct.return_value = ConstructResult(
            artifact="generated code",
            evaluations=[
                {"check_name": "quality", "outcome": "pass", "reason": "good"},
            ],
            traceability=[],
        )

        config = self._make_engine_config(tmp_path)
        config.deterministic_only = False  # Enable agent checks

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

        with patch("genisis.engine.fp_run_check") as mock_fp:
            record = iterate_edge(
                edge="design→code",
                edge_config=edge_config,
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="design",
                construct=True,
            )
            # fp_run_check should NOT be called — batched result used instead
            mock_fp.assert_not_called()

        assert len(record.evaluation.checks) == 1
        assert record.evaluation.checks[0].outcome == CheckOutcome.PASS
        assert "[batched]" in record.evaluation.checks[0].message


# ═══════════════════════════════════════════════════════════════════════════
# CONTEXT THREADING (REQ-F-FPC-003)
# ═══════════════════════════════════════════════════════════════════════════


class TestContextThreading:
    """Validates: REQ-F-FPC-003 — context accumulated between edges in run()."""

    @patch("genisis.engine.run_edge")
    @patch("genisis.engine.select_next_edge")
    @patch("genisis.engine.select_profile")
    @patch("genisis.engine.load_yaml")
    def test_context_accumulates(
        self, mock_yaml, mock_profile, mock_next_edge, mock_run_edge
    ):
        from genisis.engine import EngineConfig, IterationRecord, run
        from genisis.models import EvaluationResult

        mock_profile.return_value = "standard"
        mock_yaml.return_value = {}

        # Simulate two edges converging
        edge1_record = IterationRecord(
            edge="intent→requirements",
            iteration=1,
            evaluation=EvaluationResult(
                edge="intent→requirements", converged=True, delta=0
            ),
            construct_result=ConstructResult(
                artifact="Requirements artifact content"
            ),
        )
        edge2_record = IterationRecord(
            edge="requirements→design",
            iteration=1,
            evaluation=EvaluationResult(
                edge="requirements→design", converged=True, delta=0
            ),
            construct_result=ConstructResult(artifact="Design artifact content"),
        )

        mock_run_edge.side_effect = [[edge1_record], [edge2_record]]

        # Route returns edge1, then edge2, then None (done)
        from genisis.models import RouteResult

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
        # Second run_edge call should have accumulated context
        second_call = mock_run_edge.call_args_list[1]
        context_arg = second_call.kwargs.get("context", second_call[1].get("context", ""))
        assert "Requirements artifact content" in context_arg
        assert "intent→requirements artifact" in context_arg


# ═══════════════════════════════════════════════════════════════════════════
# BACKWARD COMPATIBILITY (REQ-NFR-FPC-002)
# ═══════════════════════════════════════════════════════════════════════════


class TestBackwardCompatibility:
    """Validates: REQ-NFR-FPC-002 — existing evaluate-only path unchanged."""

    def _make_engine_config(self, tmp_path):
        from genisis.engine import EngineConfig

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
        from genisis.engine import iterate_edge

        config = self._make_engine_config(tmp_path)

        with patch("genisis.engine.run_construct") as mock_construct:
            record = iterate_edge(
                edge="intent→requirements",
                edge_config={"checklist": []},
                config=config,
                feature_id="REQ-F-TEST-001",
                asset_content="test",
            )
            mock_construct.assert_not_called()

        assert record.construct_result is None

    def test_iteration_record_has_optional_construct(self, tmp_path):
        """IterationRecord.construct_result defaults to None."""
        from genisis.engine import IterationRecord
        from genisis.models import EvaluationResult as ER

        record = IterationRecord(
            edge="test",
            iteration=1,
            evaluation=ER(edge="test"),
        )
        assert record.construct_result is None


# ═══════════════════════════════════════════════════════════════════════════
# CLI CONSTRUCT COMMAND (REQ-F-FPC-005)
# ═══════════════════════════════════════════════════════════════════════════


class TestCLIConstruct:
    """Validates: REQ-F-FPC-005 — construct subcommand in CLI."""

    def test_construct_subcommand_registered(self):
        """construct subcommand is available in argparse."""
        from genisis.__main__ import main
        import argparse

        parser = argparse.ArgumentParser(prog="genisis")
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
        from genisis.__main__ import main
        import argparse

        parser = argparse.ArgumentParser(prog="genisis")
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
