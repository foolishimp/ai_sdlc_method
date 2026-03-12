# Validates: REQ-SENSE-001 (Interoceptive Monitoring — INTRO-008 convergence_evidence_present)
# Validates: REQ-EVENT-002 (Projection Contract — Projection Authority enforcement)
# Validates: REQ-LIFE-006 (Signal Source Classification — convergence_without_evidence)
"""Harnessed tests for workspace_integrity.py — convergence_evidence_present F_D check.

ADR-S-037: a feature vector claiming status: converged on an edge must have a
terminal convergence event (edge_converged / ConvergenceAchieved) in the stream.
IterationCompleted alone is NOT sufficient.

Test structure:
  TestTerminalEventRecognition  — which event types count as terminal convergence
  TestFeatureVectorParsing      — YAML parsing edge cases
  TestEdgeMatching              — event matching logic for feature+edge
  TestFailureCases              — the key detection scenarios
  TestPassCases                 — clean workspaces that should pass
  TestMixedWorkspace            — partial evidence (some features have it, some don't)
  TestReportShape               — EvidenceGap fields and report structure
  TestSensoryContractOutput     — Option A: gap → interoceptive_signal shape
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from genesis.fd_sense import sense_convergence_evidence
from genesis.workspace_integrity import (
    TERMINAL_CONVERGENCE_EVENTS,
    LIFECYCLE_ONLY_EVENTS,
    EvidenceGap,
    ConvergenceEvidenceReport,
    check_convergence_evidence,
    _has_terminal_convergence_event,
    _converged_edges,
    _extract_feature_id,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def make_workspace(tmp_path: Path) -> Path:
    """Create a minimal workspace skeleton."""
    (tmp_path / ".ai-workspace" / "features" / "active").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "features" / "completed").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
    return tmp_path


def write_vector(
    workspace: Path,
    feature_id: str,
    trajectory: dict,
    status_dir: str = "active",
) -> Path:
    """Write a feature vector YAML with given trajectory."""
    fdir = workspace / ".ai-workspace" / "features" / status_dir
    fdir.mkdir(parents=True, exist_ok=True)
    fpath = fdir / f"{feature_id}.yml"
    fpath.write_text(yaml.dump({
        "feature": feature_id,
        "status": "in_progress",
        "trajectory": trajectory,
    }))
    return fpath


def write_events(workspace: Path, events: list[dict]) -> Path:
    """Write events.jsonl from a list of event dicts."""
    events_dir = workspace / ".ai-workspace" / "events"
    events_dir.mkdir(parents=True, exist_ok=True)
    path = events_dir / "events.jsonl"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
    return path


def edge_converged_event(feature: str, edge: str, **kwargs) -> dict:
    return {"event_type": "edge_converged", "feature": feature, "edge": edge, **kwargs}


def iteration_completed_event(feature: str, edge: str, status: str = "converged", **kwargs) -> dict:
    return {"event_type": "iteration_completed", "feature": feature, "edge": edge, "status": status, **kwargs}


def edge_started_event(feature: str, edge: str) -> dict:
    return {"event_type": "edge_started", "feature": feature, "edge": edge}


# ═══════════════════════════════════════════════════════════════════════════════
# TestTerminalEventRecognition
# ═══════════════════════════════════════════════════════════════════════════════


class TestTerminalEventRecognition:
    """Which event types constitute terminal convergence evidence."""

    def test_edge_converged_is_terminal(self):
        assert "edge_converged" in TERMINAL_CONVERGENCE_EVENTS

    def test_convergence_achieved_canonical_is_terminal(self):
        """REQ-EVENT-003: ConvergenceAchieved is the canonical convergence event."""
        assert "ConvergenceAchieved" in TERMINAL_CONVERGENCE_EVENTS

    def test_iteration_completed_is_not_terminal(self):
        """iteration_completed is a lifecycle event — ADR-S-037 explicitly excludes it."""
        assert "iteration_completed" not in TERMINAL_CONVERGENCE_EVENTS
        assert "iteration_completed" in LIFECYCLE_ONLY_EVENTS

    def test_iteration_completed_camel_is_not_terminal(self):
        assert "IterationCompleted" not in TERMINAL_CONVERGENCE_EVENTS
        assert "IterationCompleted" in LIFECYCLE_ONLY_EVENTS

    def test_edge_started_is_not_terminal(self):
        assert "edge_started" not in TERMINAL_CONVERGENCE_EVENTS

    def test_iteration_started_is_not_terminal(self):
        assert "iteration_started" not in TERMINAL_CONVERGENCE_EVENTS

    def test_terminal_and_lifecycle_sets_are_disjoint(self):
        """No event type can be both terminal and lifecycle-only."""
        assert TERMINAL_CONVERGENCE_EVENTS.isdisjoint(LIFECYCLE_ONLY_EVENTS)


# ═══════════════════════════════════════════════════════════════════════════════
# TestEdgeMatching
# ═══════════════════════════════════════════════════════════════════════════════


class TestEdgeMatching:
    """_has_terminal_convergence_event matching logic."""

    def _events(self, *evts):
        return list(evts)

    def test_exact_match_passes(self):
        events = [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_wrong_feature_does_not_match(self):
        """edge_converged for a different feature must not satisfy the check."""
        events = [edge_converged_event("REQ-F-OTHER-001", "code↔unit_tests")]
        assert not _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_wrong_edge_does_not_match(self):
        """edge_converged for a different edge must not satisfy the check."""
        events = [edge_converged_event("REQ-F-AUTH-001", "design→code")]
        assert not _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_instance_id_field_matches(self):
        """OL-format events use instance_id instead of feature."""
        events = [{"event_type": "edge_converged", "instance_id": "REQ-F-AUTH-001", "edge": "code↔unit_tests"}]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_feature_in_data_payload_matches(self):
        """Feature ID in event.data.feature must match."""
        events = [{"event_type": "edge_converged", "data": {"feature": "REQ-F-AUTH-001", "edge": "code↔unit_tests"}}]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_convergence_achieved_canonical_matches(self):
        """REQ-EVENT-003 ConvergenceAchieved satisfies the check."""
        events = [{"event_type": "ConvergenceAchieved", "feature": "REQ-F-AUTH-001", "edge": "code↔unit_tests"}]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_iteration_completed_with_status_converged_does_not_satisfy(self):
        """CRITICAL: iteration_completed even with status:converged is NOT terminal evidence."""
        events = [iteration_completed_event("REQ-F-AUTH-001", "code↔unit_tests", status="converged")]
        assert not _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_edge_started_does_not_satisfy(self):
        events = [edge_started_event("REQ-F-AUTH-001", "code↔unit_tests")]
        assert not _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_empty_stream_does_not_satisfy(self):
        assert not _has_terminal_convergence_event([], "REQ-F-AUTH-001", "code↔unit_tests")

    def test_multiple_events_first_match_returns_true(self):
        events = [
            edge_started_event("REQ-F-AUTH-001", "code↔unit_tests"),
            iteration_completed_event("REQ-F-AUTH-001", "code↔unit_tests"),
            edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests"),
        ]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_retroactive_emission_field_does_not_affect_matching(self):
        """emission: retroactive is valid evidence — the marker doesn't disqualify the event."""
        events = [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests", emission="retroactive")]
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")

    def test_corrupt_event_line_skipped_gracefully(self):
        """Malformed events in the stream must not crash the check."""
        events = [
            {"event_type": "edge_converged", "feature": "REQ-F-AUTH-001", "edge": "code↔unit_tests"},
        ]
        # Add a bad dict that would simulate a corrupt parse (missing fields)
        events.insert(0, {"event_type": None})
        assert _has_terminal_convergence_event(events, "REQ-F-AUTH-001", "code↔unit_tests")


# ═══════════════════════════════════════════════════════════════════════════════
# TestFailureCases — the detection scenarios
# ═══════════════════════════════════════════════════════════════════════════════


class TestFailureCases:
    """Scenarios where convergence_evidence_present must FAIL."""

    def test_converged_edge_with_no_events_at_all(self, tmp_path):
        """genesis_navigator case: vector claims converged, events.jsonl is empty."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged", "iteration": 1},
        })
        write_events(ws, [])  # empty stream

        report = check_convergence_evidence(ws)

        assert not report.passed
        assert report.delta == 1
        assert report.gaps[0].feature_id == "REQ-F-AUTH-001"
        assert report.gaps[0].edge == "code↔unit_tests"

    def test_converged_edge_with_only_iteration_completed(self, tmp_path):
        """CRITICAL: iteration_completed{status:converged} does NOT satisfy — must FAIL."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [
            iteration_completed_event("REQ-F-AUTH-001", "code↔unit_tests", status="converged"),
        ])

        report = check_convergence_evidence(ws)

        assert not report.passed, (
            "iteration_completed alone must not satisfy convergence_evidence_present — "
            "only terminal convergence events (edge_converged/ConvergenceAchieved) count"
        )
        assert report.delta == 1

    def test_converged_edge_with_only_edge_started(self, tmp_path):
        """edge_started alone does not satisfy."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [edge_started_event("REQ-F-AUTH-001", "code↔unit_tests")])

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.delta == 1

    def test_wrong_feature_id_in_stream(self, tmp_path):
        """edge_converged for a different feature must not satisfy."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [edge_converged_event("REQ-F-DB-001", "code↔unit_tests")])

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.gaps[0].feature_id == "REQ-F-AUTH-001"

    def test_wrong_edge_in_stream(self, tmp_path):
        """edge_converged for a different edge must not satisfy."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "design→code")])

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.gaps[0].edge == "code↔unit_tests"

    def test_multiple_converged_edges_none_evidenced(self, tmp_path):
        """Multiple converged edges all lacking evidence — all reported."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert report.delta == 2
        edges = {g.edge for g in report.gaps}
        assert edges == {"design→code", "code↔unit_tests"}

    def test_missing_events_file_treated_as_empty_stream(self, tmp_path):
        """No events.jsonl → all converged edges are gaps."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        # Do NOT write events file

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.delta == 1

    def test_completed_folder_vectors_are_checked(self, tmp_path):
        """Completed feature vectors are also subject to convergence evidence check."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        }, status_dir="completed")
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.gaps[0].feature_id == "REQ-F-AUTH-001"

    def test_no_events_file_no_vectors_passes(self, tmp_path):
        """Empty workspace with no vectors passes vacuously."""
        ws = make_workspace(tmp_path)
        report = check_convergence_evidence(ws)
        assert report.passed
        assert report.delta == 0
        assert report.checked_features == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TestPassCases — clean workspaces
# ═══════════════════════════════════════════════════════════════════════════════


class TestPassCases:
    """Scenarios where convergence_evidence_present must PASS."""

    def test_converged_edge_with_edge_converged_event(self, tmp_path):
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")])

        report = check_convergence_evidence(ws)
        assert report.passed
        assert report.delta == 0

    def test_converged_edge_with_convergence_achieved_canonical(self, tmp_path):
        """REQ-EVENT-003 ConvergenceAchieved satisfies the check."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [
            {"event_type": "ConvergenceAchieved", "feature": "REQ-F-AUTH-001", "edge": "code↔unit_tests"},
        ])

        report = check_convergence_evidence(ws)
        assert report.passed

    def test_iterating_edge_not_checked(self, tmp_path):
        """Only converged edges need evidence. Iterating edges are skipped."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "iterating"},
        })
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert report.passed
        assert report.checked_edges == 0

    def test_pending_edge_not_checked(self, tmp_path):
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "pending"},
        })
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert report.passed

    def test_retroactive_edge_converged_passes(self, tmp_path):
        """Retroactive convergence events are valid evidence per ADR-S-037 §3."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [
            edge_converged_event(
                "REQ-F-AUTH-001", "code↔unit_tests",
                emission="retroactive",
            ),
        ])

        report = check_convergence_evidence(ws)
        assert report.passed, (
            "emission: retroactive is valid convergence evidence per ADR-S-037 §3"
        )

    def test_multiple_features_all_evidenced_passes(self, tmp_path):
        ws = make_workspace(tmp_path)
        for fid in ["REQ-F-AUTH-001", "REQ-F-DB-001", "REQ-F-API-001"]:
            write_vector(ws, fid, {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [
            edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests"),
            edge_converged_event("REQ-F-DB-001", "code↔unit_tests"),
            edge_converged_event("REQ-F-API-001", "code↔unit_tests"),
        ])

        report = check_convergence_evidence(ws)
        assert report.passed
        assert report.checked_features == 3
        assert report.checked_edges == 3

    def test_vector_with_no_trajectory_section_passes(self, tmp_path):
        """A vector with no trajectory has no converged edges — passes vacuously."""
        ws = make_workspace(tmp_path)
        fdir = ws / ".ai-workspace" / "features" / "active"
        (fdir / "REQ-F-AUTH-001.yml").write_text(yaml.dump({
            "feature": "REQ-F-AUTH-001",
            "status": "in_progress",
        }))
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert report.passed


# ═══════════════════════════════════════════════════════════════════════════════
# TestMixedWorkspace — partial evidence
# ═══════════════════════════════════════════════════════════════════════════════


class TestMixedWorkspace:
    """Some features have evidence, some don't. Only gaps are reported."""

    def test_mixed_features_only_gaps_reported(self, tmp_path):
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_vector(ws, "REQ-F-DB-001",   {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [
            # Only AUTH has evidence
            edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests"),
        ])

        report = check_convergence_evidence(ws)
        assert not report.passed
        assert report.delta == 1
        assert report.gaps[0].feature_id == "REQ-F-DB-001"
        assert report.checked_features == 2
        assert report.checked_edges == 2

    def test_mixed_edges_on_same_feature(self, tmp_path):
        """One edge evidenced, one not — only the gap is reported."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
        })
        write_events(ws, [
            edge_converged_event("REQ-F-AUTH-001", "design→code"),
            # code↔unit_tests has no event
        ])

        report = check_convergence_evidence(ws)
        assert report.delta == 1
        assert report.gaps[0].edge == "code↔unit_tests"

    def test_genesis_navigator_scale(self, tmp_path):
        """Simulate genesis_navigator: 13 features × 2 edges, zero events — 26 gaps."""
        ws = make_workspace(tmp_path)
        for i in range(1, 14):
            fid = f"REQ-F-NAV-{i:03d}"
            write_vector(ws, fid, {
                "design→code": {"status": "converged"},
                "code↔unit_tests": {"status": "converged"},
            })
        write_events(ws, [])  # genesis_navigator: zero convergence events

        report = check_convergence_evidence(ws)
        assert report.delta == 26
        assert report.checked_features == 13
        assert report.checked_edges == 26

    def test_active_and_completed_both_checked(self, tmp_path):
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}}, "active")
        write_vector(ws, "REQ-F-DB-001",   {"code↔unit_tests": {"status": "converged"}}, "completed")
        write_events(ws, [
            edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests"),
            # DB-001 in completed/ has no event
        ])

        report = check_convergence_evidence(ws)
        assert report.delta == 1
        assert report.gaps[0].feature_id == "REQ-F-DB-001"


# ═══════════════════════════════════════════════════════════════════════════════
# TestReportShape — EvidenceGap fields and ConvergenceEvidenceReport
# ═══════════════════════════════════════════════════════════════════════════════


class TestReportShape:
    def test_evidence_gap_fields(self, tmp_path):
        ws = make_workspace(tmp_path)
        vpath = write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        gap = report.gaps[0]

        assert gap.feature_id == "REQ-F-AUTH-001"
        assert gap.edge == "code↔unit_tests"
        assert gap.claimed_status == "converged"
        assert gap.vector_path == vpath

    def test_report_counts(self, tmp_path):
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
            "intent→requirements": {"status": "iterating"},
        })
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "design→code")])

        report = check_convergence_evidence(ws)
        assert report.checked_features == 1
        assert report.checked_edges == 2  # only the 2 converged edges counted
        assert report.delta == 1


# ═══════════════════════════════════════════════════════════════════════════════
# TestSensoryContractOutput — Option A: gap → interoceptive_signal shape
# ═══════════════════════════════════════════════════════════════════════════════


class TestSensoryContractOutput:
    """The monitor output is interoceptive_signal, never intent_raised directly."""

    def test_evidence_gap_produces_interoceptive_signal_shape(self, tmp_path):
        """EvidenceGap.as_interoceptive_signal() returns the correct signal structure."""
        ws = make_workspace(tmp_path)
        gap = EvidenceGap(
            feature_id="REQ-F-AUTH-001",
            edge="code↔unit_tests",
            vector_path=ws / ".ai-workspace" / "features" / "active" / "REQ-F-AUTH-001.yml",
        )
        signal = gap.as_interoceptive_signal()

        assert signal["monitor_id"] == "INTRO-008"
        assert signal["severity"] == "critical"
        assert signal["observation"] == "convergence_without_evidence"
        assert "REQ-F-AUTH-001" in signal["affected_features"]
        assert signal["edge"] == "code↔unit_tests"

    def test_interoceptive_signal_contains_no_event_type_field(self, tmp_path):
        """The signal dict is not itself an event — it is the payload for interoceptive_signal.

        The sensory service wraps this in the event envelope. The check produces
        the observation payload; the caller decides the event_type.
        """
        ws = make_workspace(tmp_path)
        gap = EvidenceGap("REQ-F-AUTH-001", "code↔unit_tests", ws)
        signal = gap.as_interoceptive_signal()
        # The payload must NOT have event_type — that's the envelope layer
        assert "event_type" not in signal

    def test_check_function_returns_report_not_events(self, tmp_path):
        """check_convergence_evidence() returns a ConvergenceEvidenceReport, not events.

        The caller (sensory service) is responsible for wrapping gaps into
        interoceptive_signal events and emitting them. The check is observation-only.
        """
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [])

        result = check_convergence_evidence(ws)
        assert isinstance(result, ConvergenceEvidenceReport)
        # Not a list of events, not a dict with event_type
        assert not isinstance(result, dict)
        assert not isinstance(result, list)

    def test_all_gaps_have_interoceptive_signal_method(self, tmp_path):
        ws = make_workspace(tmp_path)
        for fid in ["REQ-F-AUTH-001", "REQ-F-DB-001"]:
            write_vector(ws, fid, {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        for gap in report.gaps:
            sig = gap.as_interoceptive_signal()
            assert sig["monitor_id"] == "INTRO-008"
            assert sig["severity"] == "critical"


# ═══════════════════════════════════════════════════════════════════════════════
# TestFeatureVectorParsing — YAML parsing edge cases
# ═══════════════════════════════════════════════════════════════════════════════


class TestFeatureVectorParsing:
    def test_nested_feature_id_format(self, tmp_path):
        """Legacy nested YAML format: feature: {id: REQ-F-AUTH-001}."""
        ws = make_workspace(tmp_path)
        fdir = ws / ".ai-workspace" / "features" / "active"
        (fdir / "REQ-F-AUTH-001.yml").write_text(yaml.dump({
            "feature": {"id": "REQ-F-AUTH-001", "status": "in_progress"},
            "trajectory": {"code↔unit_tests": {"status": "converged"}},
        }))
        write_events(ws, [])

        report = check_convergence_evidence(ws)
        assert report.delta == 1
        assert report.gaps[0].feature_id == "REQ-F-AUTH-001"

    def test_filename_fallback_for_feature_id(self, tmp_path):
        """If no feature field, use filename stem as feature ID."""
        ws = make_workspace(tmp_path)
        fdir = ws / ".ai-workspace" / "features" / "active"
        (fdir / "REQ-F-AUTH-001.yml").write_text(yaml.dump({
            "trajectory": {"code↔unit_tests": {"status": "converged"}},
        }))
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")])

        report = check_convergence_evidence(ws)
        assert report.passed

    def test_corrupt_yaml_file_skipped(self, tmp_path):
        """Corrupt YAML files must not crash the check — they are silently skipped."""
        ws = make_workspace(tmp_path)
        fdir = ws / ".ai-workspace" / "features" / "active"
        (fdir / "corrupt.yml").write_text("{{not: valid: yaml: [}")
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")])

        report = check_convergence_evidence(ws)
        assert report.passed  # corrupt file skipped, valid vector passes

    def test_empty_yaml_file_skipped(self, tmp_path):
        ws = make_workspace(tmp_path)
        fdir = ws / ".ai-workspace" / "features" / "active"
        (fdir / "empty.yml").write_text("")
        write_events(ws, [])
        report = check_convergence_evidence(ws)
        assert report.passed

    def test_custom_events_path(self, tmp_path):
        """events_path parameter allows pointing to a non-default events file."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})

        custom_events = tmp_path / "custom_events.jsonl"
        custom_events.write_text(
            json.dumps(edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")) + "\n"
        )

        report = check_convergence_evidence(ws, events_path=custom_events)
        assert report.passed


# ═══════════════════════════════════════════════════════════════════════════════
# TestSensoryWiring — sense_convergence_evidence() from fd_sense (INTRO-008 live path)
# ═══════════════════════════════════════════════════════════════════════════════


class TestSensoryWiring:
    """sense_convergence_evidence() is the wired INTRO-008 callable in fd_sense.

    Validates that the live sensory path returns a SenseResult with the
    correct shape and threshold semantics for both pass and breach cases.
    """

    def test_sense_returns_sense_result_with_breached_false_on_clean_workspace(self, tmp_path):
        """Clean workspace → SenseResult(breached=False, value=0)."""
        ws = make_workspace(tmp_path)
        # No converged edges → nothing to check → passes
        result = sense_convergence_evidence(ws)
        assert result.breached is False
        assert result.value == 0
        assert result.monitor_name == "convergence_evidence_present"

    def test_sense_returns_breached_true_when_gaps_exist(self, tmp_path):
        """Converged edge with no event → SenseResult(breached=True, value=N)."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [])
        result = sense_convergence_evidence(ws)
        assert result.breached is True
        assert result.value == 1
        assert result.threshold == 0

    def test_sense_value_equals_gap_count(self, tmp_path):
        """value field equals number of edges with missing evidence."""
        ws = make_workspace(tmp_path)
        for fid in ["REQ-F-AUTH-001", "REQ-F-DB-001"]:
            write_vector(ws, fid, {
                "design→code": {"status": "converged"},
                "code↔unit_tests": {"status": "converged"},
            })
        write_events(ws, [])
        result = sense_convergence_evidence(ws)
        assert result.value == 4  # 2 features × 2 edges

    def test_sense_passes_after_repair(self, tmp_path):
        """After appending edge_converged events, sense result clears."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [edge_converged_event("REQ-F-AUTH-001", "code↔unit_tests")])
        result = sense_convergence_evidence(ws)
        assert result.breached is False

    def test_sense_detail_describes_breach(self, tmp_path):
        """detail field is human-readable for health check output."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-AUTH-001", {"code↔unit_tests": {"status": "converged"}})
        write_events(ws, [])
        result = sense_convergence_evidence(ws)
        assert "1" in result.detail
        assert "convergence" in result.detail.lower() or "evidence" in result.detail.lower()
