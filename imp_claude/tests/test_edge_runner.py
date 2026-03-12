# Validates: REQ-F-DISPATCH-001
# Validates: REQ-F-RUNTIME-001
"""Tests for EDGE_RUNNER — run_edge() composing F_D → F_P → F_H.

Covers:
- F_D delta=0 → converged immediately (no F_P needed)
- F_D delta>0 → fp_intent manifest written
- F_P result exists → re-evaluate F_D
- Budget exhausted → fh_required
- Events emitted correctly at each phase
- run_id uniqueness
- edge_started carries intent_id (idempotency marker)
"""

import json
import pathlib
import sys

import pytest
import yaml

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))
from genesis.outcome_types import FdError, FdFailed, FdPassed, FpFailed, FpPending, FpReturned, FpSkipped

from genesis.edge_runner import (
    DEFAULT_BUDGET_USD,
    MAX_FP_ITERATIONS,
    EdgeRunResult,
    _check_fp_result,
    _write_fp_manifest,
    run_edge,
)
from genesis.intent_observer import DispatchTarget


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_target(
    intent_id: str = "INT-001",
    feature_id: str = "REQ-F-TEST-001",
    edge: str = "code↔unit_tests",
    feature_vector: dict | None = None,
    intent_events: list | None = None,
) -> DispatchTarget:
    return DispatchTarget(
        intent_id=intent_id,
        feature_id=feature_id,
        edge=edge,
        intent_events=intent_events if intent_events is not None else [{"intent_id": intent_id}],
        feature_vector=feature_vector or {
            "feature": feature_id,
            "profile": "standard",
            "trajectory": {},
        },
    )


def _read_events(events_path: pathlib.Path) -> list[dict]:
    if not events_path.exists():
        return []
    from genesis.ol_event import normalize_event
    events = []
    for line in events_path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(normalize_event(json.loads(line)))
        except Exception:
            continue
    return events


def _get_event_types(events: list[dict]) -> list[str]:
    return [ev.get("event_type", "") for ev in events]


def _make_events_path(tmp_path: pathlib.Path) -> pathlib.Path:
    ep = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
    ep.parent.mkdir(parents=True, exist_ok=True)
    return ep


# ── Tests: F_D delta=0 → converged ────────────────────────────────────────────


class TestEdgeRunnerConverged:
    """Tests where F_D reports delta=0 immediately."""

    def test_fd_converged_returns_converged_status(self, tmp_path, monkeypatch):
        """When F_D delta=0, status='converged' is returned."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        # Patch _run_fd_evaluation to return delta=0
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result = run_edge(target, tmp_path, events_path)
        assert result.status == "converged"
        assert result.delta == 0

    def test_fd_converged_emits_edge_started(self, tmp_path, monkeypatch):
        """EdgeStarted is always emitted first."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        types = _get_event_types(events)
        assert "edge_started" in types

    def test_fd_converged_emits_edge_converged(self, tmp_path, monkeypatch):
        """EdgeConverged is emitted when F_D delta=0."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        types = _get_event_types(events)
        assert "edge_converged" in types

    def test_fd_converged_emits_iteration_completed(self, tmp_path, monkeypatch):
        """IterationCompleted is emitted after F_D evaluation."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        types = _get_event_types(events)
        assert "iteration_completed" in types

    def test_fd_converged_no_fp_manifest_written(self, tmp_path, monkeypatch):
        """No fp_intent manifest is written when F_D converges immediately."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result = run_edge(target, tmp_path, events_path)
        assert result.fp_manifest_path == ""

    def test_fd_converged_iterations_is_one(self, tmp_path, monkeypatch):
        """Single F_D pass → iterations=1."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result = run_edge(target, tmp_path, events_path)
        assert result.iterations == 1


# ── Tests: F_D delta>0 → F_P dispatched ───────────────────────────────────────


class TestEdgeRunnerFpDispatched:
    """Tests where F_D delta>0 triggers F_P dispatch."""

    def test_fd_delta_triggers_fp_dispatch(self, tmp_path, monkeypatch):
        """F_D delta>0 with no existing fp_result → fp_dispatched."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=2, failures=["check_a"]))
        # No fp_result exists (default _check_fp_result returns None)

        result = run_edge(target, tmp_path, events_path)
        assert result.status == "fp_dispatched"

    def test_fp_manifest_is_written(self, tmp_path, monkeypatch):
        """fp_intent manifest file is written when F_P is dispatched."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=2, failures=["check_a"]))

        result = run_edge(target, tmp_path, events_path)
        assert result.fp_manifest_path != ""
        assert pathlib.Path(result.fp_manifest_path).exists()

    def test_fp_manifest_contains_correct_fields(self, tmp_path, monkeypatch):
        """fp_intent manifest contains required fields."""
        events_path = _make_events_path(tmp_path)
        target = _make_target(feature_id="REQ-F-DISP-001", edge="design→code")

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=1, failures=["fd_check"]))

        result = run_edge(target, tmp_path, events_path)
        manifest = json.loads(pathlib.Path(result.fp_manifest_path).read_text())

        assert manifest["edge"] == "design→code"
        assert manifest["feature"] == "REQ-F-DISP-001"
        assert manifest["intent_id"] == "INT-001"
        assert "run_id" in manifest
        assert "result_path" in manifest
        assert manifest["status"] == "pending"

    def test_fp_dispatched_delta_is_nonzero(self, tmp_path, monkeypatch):
        """fp_dispatched result carries the F_D delta."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=3, failures=["a", "b", "c"]))

        result = run_edge(target, tmp_path, events_path)
        assert result.delta == 3


# ── Tests: F_P result exists → re-evaluate ────────────────────────────────────


class TestEdgeRunnerFpResult:
    """Tests where fold-back result exists from prior F_P run."""

    def _write_fp_result(self, agents_dir: pathlib.Path, run_id: str, converged: bool = True, delta: int = 0):
        agents_dir.mkdir(parents=True, exist_ok=True)
        result = {
            "converged": converged,
            "delta": delta,
            "cost_usd": 0.10,
            "artifacts": [],
            "spawns": [],
        }
        (agents_dir / f"fp_result_{run_id}.json").write_text(json.dumps(result))

    def test_fp_result_with_delta_zero_returns_converged(self, tmp_path, monkeypatch):
        """Fold-back result + F_D re-eval delta=0 → converged."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er

        call_count = [0]

        def mock_fd(t, ws, run_id, project):
            call_count[0] += 1
            # First call: delta=1 (trigger F_P)
            # Subsequent calls: delta=0 (F_P fixed it)
            return FdFailed(delta=1, failures=["check_a"]) if call_count[0] == 1 else FdPassed()

        monkeypatch.setattr(er, "_run_fd_evaluation", mock_fd)

        # Pre-write a fold-back result so _check_fp_result finds it
        agents_dir = tmp_path / ".ai-workspace" / "agents"
        # We need to know the run_id ahead of time — instead, patch _check_fp_result
        monkeypatch.setattr(
            er, "_check_fp_result",
            lambda ws, rid: {"converged": True, "delta": 0, "cost_usd": 0.1, "artifacts": [], "spawns": []},
        )

        result = run_edge(target, tmp_path, events_path)
        assert result.status == "converged"

    def test_fp_result_with_remaining_delta_continues(self, tmp_path, monkeypatch):
        """Fold-back result exists but F_D still fails → fp_dispatched on next iteration."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er

        call_count = [0]

        def mock_fd(t, ws, run_id, project):
            call_count[0] += 1
            # Always returns delta=1 (F_P not sufficient)
            return FdFailed(delta=1, failures=["check_a"])

        monkeypatch.setattr(er, "_run_fd_evaluation", mock_fd)

        # First fp_result exists (from iteration 1), second doesn't
        results_given = [
            {"converged": False, "delta": 1, "cost_usd": 0.1, "artifacts": [], "spawns": []},
            None,  # second fp attempt: no result
        ]
        result_idx = [0]

        def mock_check_fp(ws, rid):
            idx = result_idx[0]
            result_idx[0] += 1
            return results_given[idx] if idx < len(results_given) else None

        monkeypatch.setattr(er, "_check_fp_result", mock_check_fp)

        result = run_edge(target, tmp_path, events_path, max_fp_iterations=3)
        # Second fp attempt has no result → fp_dispatched
        assert result.status == "fp_dispatched"


# ── Tests: budget exhaustion and F_H escalation ────────────────────────────────


class TestEdgeRunnerFhEscalation:
    """Tests for F_H escalation when F_P is exhausted."""

    def test_budget_exhaustion_causes_fh_required(self, tmp_path, monkeypatch):
        """Budget exhausted → fh_required."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er

        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=1, failures=["check_a"]))
        # fp_result always converges but F_D still fails (shouldn't happen in real life but covers budget path)
        monkeypatch.setattr(
            er, "_check_fp_result",
            lambda ws, rid: {"converged": True, "delta": 0, "cost_usd": 1.0, "artifacts": [], "spawns": []},
        )

        # Set very tight budget — after first F_P iteration cost exceeds budget
        result = run_edge(target, tmp_path, events_path, budget_usd=0.05)
        # budget_usd=0.05 < COST_PER_FP_ITERATION=0.15 → loop exits before any F_P
        assert result.status in ("fh_required", "stuck")

    def test_max_fp_iterations_causes_fh_required(self, tmp_path, monkeypatch):
        """All F_P iterations exhausted with no convergence → fh_required."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er

        # Always delta=1 from F_D
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=1, failures=["check_a"]))
        # fp_result always exists but with delta>0 still
        monkeypatch.setattr(
            er, "_check_fp_result",
            lambda ws, rid: {"converged": False, "delta": 1, "cost_usd": 0.05, "artifacts": [], "spawns": []},
        )

        result = run_edge(target, tmp_path, events_path, max_fp_iterations=2)
        assert result.status == "fh_required"

    def test_fh_escalation_emits_intent_raised_with_human_gate(self, tmp_path, monkeypatch):
        """F_H escalation emits an intent_raised with signal_source='human_gate_required'."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er

        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=1, failures=["check_a"]))
        monkeypatch.setattr(
            er, "_check_fp_result",
            lambda ws, rid: {"converged": False, "delta": 1, "cost_usd": 0.05, "artifacts": [], "spawns": []},
        )

        run_edge(target, tmp_path, events_path, max_fp_iterations=1)
        events = _read_events(events_path)
        human_gate_events = [
            ev for ev in events
            if ev.get("signal_source") == "human_gate_required"
            or ev.get("event_type") == "intent_raised"
        ]
        assert len(human_gate_events) > 0


# ── Tests: event emission ──────────────────────────────────────────────────────


class TestEdgeRunnerEvents:
    """Tests for correct event emission at each phase."""

    def test_edge_started_carries_intent_id(self, tmp_path, monkeypatch):
        """EdgeStarted event carries intent_id for idempotency."""
        events_path = _make_events_path(tmp_path)
        target = _make_target(intent_id="INT-TRACK-001")

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        started = [ev for ev in events if ev.get("event_type") == "edge_started"]
        assert len(started) >= 1
        assert any(ev.get("intent_id") == "INT-TRACK-001" for ev in started)

    def test_all_phases_have_events(self, tmp_path, monkeypatch):
        """edge_started + iteration_completed always emitted."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result = run_edge(target, tmp_path, events_path)
        assert "EdgeStarted" in result.events_emitted
        assert "IterationCompleted" in result.events_emitted

    def test_run_id_is_unique_per_invocation(self, tmp_path, monkeypatch):
        """Each run_edge() call produces a unique run_id."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result1 = run_edge(target, tmp_path, events_path)
        result2 = run_edge(target, tmp_path, events_path)
        assert result1.run_id != result2.run_id

    def test_result_fields_populated(self, tmp_path, monkeypatch):
        """EdgeRunResult has all required fields populated."""
        events_path = _make_events_path(tmp_path)
        target = _make_target(feature_id="REQ-F-DISP-001", edge="design→code")

        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())

        result = run_edge(target, tmp_path, events_path)
        assert result.run_id  # non-empty
        assert result.feature_id == "REQ-F-DISP-001"
        assert result.edge == "design→code"
        assert result.status == "converged"
        assert result.iterations >= 1
        assert result.cost_usd >= 0.0
        assert isinstance(result.events_emitted, list)


# ── Tests: _write_fp_manifest helper ──────────────────────────────────────────


class TestWriteFpManifest:
    """Tests for _write_fp_manifest() utility."""

    def test_manifest_written_to_agents_dir(self, tmp_path):
        """Manifest is written to .ai-workspace/agents/."""
        target = _make_target()
        path = _write_fp_manifest(target, tmp_path, "run-123", 1, 0.5, ["check_a"])
        assert path.exists()
        assert path.parent == tmp_path / ".ai-workspace" / "agents"

    def test_manifest_filename_includes_run_id(self, tmp_path):
        """Manifest filename is fp_intent_{run_id}.json."""
        target = _make_target()
        path = _write_fp_manifest(target, tmp_path, "my-run-id", 1, 0.5, [])
        assert path.name == "fp_intent_my-run-id.json"

    def test_manifest_json_is_valid(self, tmp_path):
        """Written manifest is valid JSON with required fields."""
        target = _make_target(feature_id="REQ-F-X-001", edge="design→code")
        path = _write_fp_manifest(target, tmp_path, "run-456", 2, 1.0, ["f1", "f2"])
        data = json.loads(path.read_text())
        assert data["run_id"] == "run-456"
        assert data["edge"] == "design→code"
        assert data["feature"] == "REQ-F-X-001"
        assert data["iteration"] == 2
        assert data["failures"] == ["f1", "f2"]
        assert "result_path" in data


# ── Tests: REQ-F-RUNTIME-001 new behaviour ─────────────────────────────────────


class TestEvaluatorError:
    """Gap 1: FdError path — evaluator infrastructure failure is NOT a domain delta."""

    def test_evaluator_error_returns_evaluator_error_status(self, tmp_path, monkeypatch):
        """FdError from _run_fd_evaluation → result.status == 'evaluator_error'."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdError(error="engine crashed"))
        result = run_edge(target, tmp_path, events_path)
        assert result.status == "evaluator_error"

    def test_evaluator_error_sets_evaluator_error_field(self, tmp_path, monkeypatch):
        """FdError → result.evaluator_error is non-empty."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdError(error="ImportError: no module"))
        result = run_edge(target, tmp_path, events_path)
        assert "ImportError" in result.evaluator_error

    def test_evaluator_error_does_not_drive_fp_iteration(self, tmp_path, monkeypatch):
        """FdError returns immediately — no F_P manifest written."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdError(error="oops"))
        result = run_edge(target, tmp_path, events_path)
        # Only 1 iteration, no manifest
        assert result.iterations == 1
        assert result.fp_manifest_path == ""

    def test_evaluator_error_emits_iteration_completed_with_null_delta(self, tmp_path, monkeypatch):
        """FdError path emits IterationCompleted with delta=None (replay-visible)."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdError(error="broken"))
        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        iter_events = [e for e in events if e.get("event_type") == "iteration_completed"]
        assert len(iter_events) == 1
        assert iter_events[0].get("status") == "evaluator_error"
        # delta must be None — not 0 (converged) and not 1 (needs work)
        assert iter_events[0].get("delta") is None

    def test_evaluator_error_event_has_error_class_infrastructure(self, tmp_path, monkeypatch):
        """IterationCompleted{status:evaluator_error} carries error_class='infrastructure'."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdError(error="config missing"))
        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        err_events = [e for e in events if e.get("status") == "evaluator_error"]
        assert err_events
        assert err_events[0].get("error_class") == "infrastructure"


class TestFHSingleEvent:
    """Gap 3: F_H escalation emits exactly one IterationCompleted (no duplicate)."""

    def test_fh_path_emits_one_iteration_completed(self, tmp_path, monkeypatch):
        """F_H escalation → single IterationCompleted + single intent_raised; no duplicate."""
        events_path = _make_events_path(tmp_path)
        target = _make_target()
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdFailed(delta=1, failures=["x"]))
        # Fold-back result always returns but delta still > 0 → F_P exhausted → F_H
        fp_result = {"converged": False, "delta": 1, "cost_usd": 0.05, "artifacts": [], "spawns": []}
        monkeypatch.setattr(er, "_check_fp_result", lambda *a, **kw: fp_result)
        result = run_edge(target, tmp_path, events_path, max_fp_iterations=1)
        assert result.status in ("fh_required", "stuck")
        events = _read_events(events_path)
        iter_events = [e for e in events if e.get("event_type") == "iteration_completed"]
        fh_iter = [e for e in iter_events if e.get("status") == "fh_required"]
        assert len(fh_iter) == 1
        # The F_H IterationCompleted must NOT contain signal_source (pure observation)
        assert "signal_source" not in fh_iter[0]


class TestMultiIntentIdempotency:
    """Gap 4: dedup accumulates intent_events; edge_started closes all intent_ids."""

    def test_two_intents_same_edge_merged_into_one_target(self, tmp_path):
        """Two intent_raised for same (feature, edge) → one DispatchTarget with both events."""
        import yaml
        from genesis.intent_observer import get_pending_dispatches

        workspace = tmp_path
        fv = {
            "feature": "REQ-F-TEST-001",
            "profile": "standard",
            "status": "in_progress",
            "trajectory": {},
        }
        fv_path = workspace / ".ai-workspace" / "features" / "active" / "REQ-F-TEST-001.yml"
        fv_path.parent.mkdir(parents=True, exist_ok=True)
        fv_path.write_text(yaml.dump(fv))

        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        # Two intents targeting the same feature
        events_path.write_text(
            '{"event_type":"intent_raised","timestamp":"2026-01-01T00:00:00Z","project":"test","data":{"intent_id":"INT-001","affected_features":["REQ-F-TEST-001"],"signal_source":"gap"}}\n'
            '{"event_type":"intent_raised","timestamp":"2026-01-01T00:01:00Z","project":"test","data":{"intent_id":"INT-002","affected_features":["REQ-F-TEST-001"],"signal_source":"gap"}}\n'
        )
        targets = get_pending_dispatches(workspace)
        assert len(targets) == 1
        assert len(targets[0].intent_events) == 2

    def test_edge_started_carries_handled_intent_ids(self, tmp_path, monkeypatch):
        """edge_started payload contains handled_intent_ids list."""
        events_path = _make_events_path(tmp_path)
        target = _make_target(intent_events=[
            {"intent_id": "INT-001"},
            {"intent_id": "INT-002"},
        ])
        import genesis.edge_runner as er
        monkeypatch.setattr(er, "_run_fd_evaluation", lambda *a, **kw: FdPassed())
        run_edge(target, tmp_path, events_path)
        events = _read_events(events_path)
        started = [e for e in events if e.get("event_type") == "edge_started"]
        assert started
        handled = started[0].get("handled_intent_ids") or []
        assert "INT-001" in handled
        assert "INT-002" in handled

    def test_second_pass_sees_no_unhandled_after_edge_started_closes_all(self, tmp_path, monkeypatch):
        """After edge_started with handled_intent_ids, none of the intents appear unhandled."""
        import yaml
        from genesis.intent_observer import find_unhandled_intents

        workspace = tmp_path
        fv = {"feature": "REQ-F-TEST-001", "profile": "standard", "status": "in_progress", "trajectory": {}}
        fv_path = workspace / ".ai-workspace" / "features" / "active" / "REQ-F-TEST-001.yml"
        fv_path.parent.mkdir(parents=True, exist_ok=True)
        fv_path.write_text(yaml.dump(fv))

        events_path = workspace / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        # Two intents + edge_started that closes both
        events_path.write_text(
            '{"event_type":"intent_raised","timestamp":"2026-01-01T00:00:00Z","project":"test","data":{"intent_id":"INT-A","affected_features":["REQ-F-TEST-001"],"signal_source":"gap"}}\n'
            '{"event_type":"intent_raised","timestamp":"2026-01-01T00:01:00Z","project":"test","data":{"intent_id":"INT-B","affected_features":["REQ-F-TEST-001"],"signal_source":"gap"}}\n'
            '{"event_type":"edge_started","timestamp":"2026-01-01T00:02:00Z","project":"test","intent_id":"INT-A","data":{"intent_id":"INT-A","handled_intent_ids":["INT-A","INT-B"]}}\n'
        )
        unhandled = find_unhandled_intents(events_path)
        assert len(unhandled) == 0


class TestQuiescence:
    """Gap 5: _compute_quiescence checks three workspace states."""

    def test_quiescence_false_with_pending_dispatches(self, tmp_path, monkeypatch):
        """Pending dispatches → not quiescent."""
        import genesis.dispatch_loop as dl
        target = _make_target()
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [target])
        assert dl._compute_quiescence(tmp_path) is False

    def test_quiescence_false_with_parked_fp_manifest(self, tmp_path, monkeypatch):
        """Active fp_intent manifest (status=dispatched) → not quiescent."""
        import genesis.dispatch_loop as dl
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [])
        agents_dir = tmp_path / ".ai-workspace" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "fp_intent_test-run.json").write_text('{"status":"dispatched"}')
        assert dl._compute_quiescence(tmp_path) is False

    def test_quiescence_false_with_pending_fp_manifest(self, tmp_path, monkeypatch):
        """Active fp_intent manifest (status=pending) → not quiescent."""
        import genesis.dispatch_loop as dl
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [])
        agents_dir = tmp_path / ".ai-workspace" / "agents"
        agents_dir.mkdir(parents=True, exist_ok=True)
        (agents_dir / "fp_intent_run2.json").write_text('{"status":"pending"}')
        assert dl._compute_quiescence(tmp_path) is False

    def test_quiescence_false_with_unresolved_fh_gate(self, tmp_path, monkeypatch):
        """Unresolved fh_required intent → not quiescent."""
        import genesis.dispatch_loop as dl
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [])
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            '{"event_type":"intent_raised","project":"t","data":{"signal_source":"human_gate_required","affected_features":["REQ-F-X-001"],"feature":"REQ-F-X-001","edge":"code↔unit_tests"}}\n'
        )
        assert dl._compute_quiescence(tmp_path) is False

    def test_quiescence_true_when_all_clear(self, tmp_path, monkeypatch):
        """No pending dispatches, no parked manifests, no fh gates → quiescent."""
        import genesis.dispatch_loop as dl
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [])
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text("")
        assert dl._compute_quiescence(tmp_path) is True

    def test_quiescence_true_when_fh_gate_resolved(self, tmp_path, monkeypatch):
        """fh_required gate closed by edge_converged → quiescent."""
        import genesis.dispatch_loop as dl
        monkeypatch.setattr(dl, "get_pending_dispatches", lambda root: [])
        events_path = tmp_path / ".ai-workspace" / "events" / "events.jsonl"
        events_path.parent.mkdir(parents=True, exist_ok=True)
        events_path.write_text(
            '{"event_type":"intent_raised","project":"t","data":{"signal_source":"human_gate_required","affected_features":["REQ-F-X-001"],"feature":"REQ-F-X-001","edge":"code↔unit_tests"}}\n'
            '{"event_type":"edge_converged","project":"t","data":{"feature":"REQ-F-X-001","edge":"code↔unit_tests"}}\n'
        )
        assert dl._compute_quiescence(tmp_path) is True


class TestIntentEventTypedBoundary:
    """Gap 6: IntentEvent typed projection from raw dict."""

    def test_from_dict_flat_format(self):
        """IntentEvent.from_dict handles flat format (fields at top level)."""
        from genesis.outcome_types import IntentEvent
        event = {
            "event_type": "intent_raised",
            "intent_id": "INT-001",
            "feature": "REQ-F-A-001",
            "signal_source": "gap",
            "timestamp": "2026-01-01T00:00:00Z",
        }
        ie = IntentEvent.from_dict(event)
        assert ie.intent_id == "INT-001"
        assert ie.feature_id == "REQ-F-A-001"
        assert ie.signal_source == "gap"

    def test_from_dict_nested_data_format(self):
        """IntentEvent.from_dict handles nested data sub-dict."""
        from genesis.outcome_types import IntentEvent
        event = {
            "event_type": "intent_raised",
            "timestamp": "2026-01-01T00:00:00Z",
            "data": {
                "intent_id": "INT-002",
                "affected_features": ["REQ-F-B-001"],
                "signal_source": "test_failure",
            },
        }
        ie = IntentEvent.from_dict(event)
        assert ie.intent_id == "INT-002"
        assert ie.feature_id == "REQ-F-B-001"
        assert ie.signal_source == "test_failure"

    def test_from_dict_affected_features_takes_precedence(self):
        """affected_features[0] is preferred over top-level feature field."""
        from genesis.outcome_types import IntentEvent
        event = {
            "feature": "WRONG",
            "data": {
                "intent_id": "INT-003",
                "affected_features": ["REQ-F-CORRECT-001"],
                "signal_source": "gap",
            },
        }
        ie = IntentEvent.from_dict(event)
        assert ie.feature_id == "REQ-F-CORRECT-001"
