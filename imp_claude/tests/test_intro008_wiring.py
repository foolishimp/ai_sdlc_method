# Validates: REQ-SENSE-001 (Interoceptive Monitoring — INTRO-008 health pass wiring)
# Validates: REQ-UX-005 (Recovery and Self-Healing — gen-start Step 10)
# Validates: REQ-EVENT-002 (Projection Contract — retroactive convergence evidence)
"""Tests for INTRO-008 wiring: gen-start Step 10 detection + workspace_repair affordance.

Design contract (v3):
  Detection: sense_convergence_evidence() called at gen-start Step 10 + gen-status --health
  Repair:    repair_convergence_evidence() called only via gen-status --repair (explicit F_H gate)
  No EDGE_RUNNER involvement — repair domain is (gap) → event_appended.

Test structure:
  TestHealthPassDetection    — health pass fires INTRO-008, emits interoceptive_signal
  TestRepairClosesGaps       — repair_convergence_evidence() appends correct events
  TestFHGateBlocks           — repair requires explicit approval; unapproved gaps not closed
  TestProvenanceFields       — emitted events carry required provenance
  TestRepairPromptFormat     — format_repair_prompt produces correct F_H gate text
  TestReadOnlyHealthPath     — --health does not mutate; only --repair mutates
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from genesis.fd_sense import sense_convergence_evidence
from genesis.workspace_integrity import EvidenceGap
from genesis.workspace_repair import (
    RepairProvenance,
    RepairResult,
    format_repair_prompt,
    repair_convergence_evidence,
)


# ── Fixtures ──────────────────────────────────────────────────────────────────


def make_workspace(tmp_path: Path) -> Path:
    (tmp_path / ".ai-workspace" / "features" / "active").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "features" / "completed").mkdir(parents=True)
    (tmp_path / ".ai-workspace" / "events").mkdir(parents=True)
    return tmp_path


def write_vector(workspace: Path, feature_id: str, trajectory: dict) -> Path:
    fdir = workspace / ".ai-workspace" / "features" / "active"
    fpath = fdir / f"{feature_id}.yml"
    fpath.write_text(yaml.dump({
        "feature": feature_id,
        "status": "in_progress",
        "trajectory": trajectory,
    }))
    return fpath


def write_events(workspace: Path, events: list[dict]) -> Path:
    path = workspace / ".ai-workspace" / "events" / "events.jsonl"
    path.write_text(
        "\n".join(json.dumps(e) for e in events) + "\n"
        if events else ""
    )
    return path


def make_gap(feature_id: str, edge: str, workspace: Path) -> EvidenceGap:
    vector_path = workspace / ".ai-workspace" / "features" / "active" / f"{feature_id}.yml"
    return EvidenceGap(feature_id=feature_id, edge=edge, vector_path=vector_path)


def make_provenance(**kwargs) -> RepairProvenance:
    return RepairProvenance(
        confirmed_by=kwargs.get("confirmed_by", "test-session"),
        basis=kwargs.get("basis", "human_confirmation_repair"),
        confirmed_at=kwargs.get("confirmed_at", "2026-03-13T00:00:00+00:00"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TestHealthPassDetection
# ═══════════════════════════════════════════════════════════════════════════════


class TestHealthPassDetection:
    """Health pass fires INTRO-008 and returns structured result for signal emission."""

    def test_health_pass_detects_gap(self, tmp_path):
        """sense_convergence_evidence breached when YAML converged but no terminal event."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-FOO-001", {
            "design": {"status": "converged"}
        })
        events_path = write_events(ws, [
            {"event_type": "iteration_completed", "feature": "REQ-F-FOO-001", "edge": "design"}
        ])
        result = sense_convergence_evidence(ws, events_path)
        assert result.breached
        assert result.data.delta == 1

    def test_health_pass_clean_workspace(self, tmp_path):
        """sense_convergence_evidence not breached when terminal event present."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-FOO-001", {
            "design": {"status": "converged"}
        })
        events_path = write_events(ws, [
            {"event_type": "edge_converged", "feature": "REQ-F-FOO-001", "edge": "design"}
        ])
        result = sense_convergence_evidence(ws, events_path)
        assert not result.breached

    def test_health_pass_exposes_gap_list(self, tmp_path):
        """Breached result exposes ConvergenceEvidenceReport with gap details."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-BAR-001", {
            "code": {"status": "converged"},
            "unit_tests": {"status": "converged"},
        })
        events_path = write_events(ws, [])
        result = sense_convergence_evidence(ws, events_path)
        assert result.breached
        report = result.data
        gap_edges = {g.edge for g in report.gaps}
        assert "code" in gap_edges
        assert "unit_tests" in gap_edges

    def test_interoceptive_signal_shape_from_gap(self, tmp_path):
        """EvidenceGap.as_interoceptive_signal() returns expected fields."""
        ws = make_workspace(tmp_path)
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        sig = gap.as_interoceptive_signal()
        assert sig["monitor_id"] == "INTRO-008"
        assert sig["severity"] == "critical"
        assert "REQ-F-FOO-001" in sig["affected_features"]

    def test_health_pass_does_not_emit_events(self, tmp_path):
        """Detection path never writes to events.jsonl — it only reads."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-GAP-001", {"design": {"status": "converged"}})
        events_path = write_events(ws, [])
        before = events_path.read_text()
        sense_convergence_evidence(ws, events_path)
        after = events_path.read_text()
        assert before == after  # no mutation

    def test_health_pass_multiple_features(self, tmp_path):
        """Detects gaps across multiple feature vectors."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-A-001", {"design": {"status": "converged"}})
        write_vector(ws, "REQ-F-B-001", {"code": {"status": "converged"}})
        events_path = write_events(ws, [
            {"event_type": "edge_converged", "feature": "REQ-F-A-001", "edge": "design"}
        ])
        result = sense_convergence_evidence(ws, events_path)
        # A-001/design has evidence; B-001/code does not
        assert result.breached
        assert result.data.delta == 1
        assert result.data.gaps[0].feature_id == "REQ-F-B-001"


# ═══════════════════════════════════════════════════════════════════════════════
# TestRepairClosesGaps
# ═══════════════════════════════════════════════════════════════════════════════


class TestRepairClosesGaps:
    """repair_convergence_evidence() appends edge_converged events that close gaps."""

    def test_repair_appends_edge_converged(self, tmp_path):
        """Approved gap produces edge_converged event in events.jsonl."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [
            {"event_type": "project_initialized", "project": "test-project"}
        ])
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        provenance = make_provenance()

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        last_event = json.loads(lines[-1])
        assert last_event["event_type"] == "edge_converged"
        assert last_event["feature"] == "REQ-F-FOO-001"
        assert last_event["edge"] == "design→code"
        assert last_event["emission"] == "retroactive"
        assert last_event["executor"] == "human"

    def test_repair_closes_gap_on_recheck(self, tmp_path):
        """After repair, re-running sense_convergence_evidence returns not breached."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-FOO-001", {"design": {"status": "converged"}})
        events_path = write_events(ws, [
            {"event_type": "project_initialized", "project": "test-project"}
        ])

        # Initially breached
        result_before = sense_convergence_evidence(ws, events_path)
        assert result_before.breached

        # Repair
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance()
        repair_convergence_evidence([gap], provenance, events_path)

        # Now clean
        result_after = sense_convergence_evidence(ws, events_path)
        assert not result_after.breached

    def test_repair_returns_repair_result(self, tmp_path):
        """repair_convergence_evidence returns RepairResult with repaired list."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        provenance = make_provenance()

        result = repair_convergence_evidence([gap], provenance, events_path)

        assert isinstance(result, RepairResult)
        assert "REQ-F-FOO-001/design→code" in result.repaired
        assert result.repair_count == 1

    def test_repair_multiple_gaps(self, tmp_path):
        """Multiple gaps all repaired when approved=None."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gaps = [
            make_gap("REQ-F-A-001", "design→code", ws),
            make_gap("REQ-F-B-001", "code↔unit_tests", ws),
        ]
        provenance = make_provenance()

        result = repair_convergence_evidence(gaps, provenance, events_path)

        assert result.repair_count == 2
        lines = [json.loads(l) for l in events_path.read_text().strip().split("\n") if l]
        ec_events = [e for e in lines if e["event_type"] == "edge_converged"]
        assert len(ec_events) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# TestFHGateBlocks
# ═══════════════════════════════════════════════════════════════════════════════


class TestFHGateBlocks:
    """Unapproved gaps are not repaired; approved=[] skips all."""

    def test_empty_approved_list_skips_all(self, tmp_path):
        """approved=[] means no gaps are repaired (reject all)."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        provenance = make_provenance()

        result = repair_convergence_evidence([gap], provenance, events_path, approved=[])

        assert result.repair_count == 0
        assert "REQ-F-FOO-001/design→code" in result.skipped
        # No events written
        assert events_path.read_text() == ""

    def test_selective_approval(self, tmp_path):
        """Only the approved subset is repaired."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gaps = [
            make_gap("REQ-F-A-001", "design", ws),
            make_gap("REQ-F-B-001", "code", ws),
        ]
        provenance = make_provenance()

        result = repair_convergence_evidence(
            gaps, provenance, events_path,
            approved=["REQ-F-A-001/design"]
        )

        assert "REQ-F-A-001/design" in result.repaired
        assert "REQ-F-B-001/code" in result.skipped
        assert result.repair_count == 1

        lines = [json.loads(l) for l in events_path.read_text().strip().split("\n") if l]
        ec = [e for e in lines if e["event_type"] == "edge_converged"]
        assert len(ec) == 1
        assert ec[0]["feature"] == "REQ-F-A-001"

    def test_none_approved_approves_all(self, tmp_path):
        """approved=None means all gaps approved (approve all)."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gaps = [
            make_gap("REQ-F-A-001", "design", ws),
            make_gap("REQ-F-B-001", "code", ws),
        ]
        provenance = make_provenance()

        result = repair_convergence_evidence(gaps, provenance, events_path, approved=None)

        assert result.repair_count == 2
        assert len(result.skipped) == 0


# ═══════════════════════════════════════════════════════════════════════════════
# TestProvenanceFields
# ═══════════════════════════════════════════════════════════════════════════════


class TestProvenanceFields:
    """Emitted events carry required provenance — the validity ground of repair."""

    def test_confirmed_by_in_event(self, tmp_path):
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance(confirmed_by="jim-session-42")

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        event = json.loads(lines[-1])
        assert event["data"]["confirmed_by"] == "jim-session-42"

    def test_basis_in_event(self, tmp_path):
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance(basis="reviewed_artifacts_manually")

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        event = json.loads(lines[-1])
        assert event["data"]["basis"] == "reviewed_artifacts_manually"

    def test_monitor_id_in_event(self, tmp_path):
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance()

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        event = json.loads(lines[-1])
        assert event["data"]["monitor_id"] == "INTRO-008"

    def test_convergence_type_retroactive_repair(self, tmp_path):
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance()

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        event = json.loads(lines[-1])
        assert event["data"]["convergence_type"] == "retroactive_repair"

    def test_confirmed_at_in_event(self, tmp_path):
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance(confirmed_at="2026-03-13T00:00:00+00:00")

        repair_convergence_evidence([gap], provenance, events_path)

        lines = events_path.read_text().strip().split("\n")
        event = json.loads(lines[-1])
        assert event["data"]["confirmed_at"] == "2026-03-13T00:00:00+00:00"


# ═══════════════════════════════════════════════════════════════════════════════
# TestRepairPromptFormat
# ═══════════════════════════════════════════════════════════════════════════════


class TestRepairPromptFormat:
    """format_repair_prompt() produces correct F_H gate text."""

    def test_prompt_contains_feature_id(self, tmp_path):
        ws = make_workspace(tmp_path)
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        prompt = format_repair_prompt([gap])
        assert "REQ-F-FOO-001" in prompt

    def test_prompt_contains_edge(self, tmp_path):
        ws = make_workspace(tmp_path)
        gap = make_gap("REQ-F-FOO-001", "design→code", ws)
        prompt = format_repair_prompt([gap])
        assert "design→code" in prompt

    def test_prompt_contains_gap_count(self, tmp_path):
        ws = make_workspace(tmp_path)
        gaps = [
            make_gap("REQ-F-A-001", "design", ws),
            make_gap("REQ-F-B-001", "code", ws),
        ]
        prompt = format_repair_prompt(gaps)
        assert "2 gap" in prompt

    def test_prompt_mentions_retroactive(self, tmp_path):
        ws = make_workspace(tmp_path)
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        prompt = format_repair_prompt([gap])
        assert "retroactive" in prompt.lower()

    def test_prompt_contains_confirm_choice(self, tmp_path):
        ws = make_workspace(tmp_path)
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        prompt = format_repair_prompt([gap])
        assert "[y/n/selective]" in prompt

    def test_empty_gaps_no_crash(self):
        prompt = format_repair_prompt([])
        assert "0 gap" in prompt


# ═══════════════════════════════════════════════════════════════════════════════
# TestReadOnlyHealthPath
# ═══════════════════════════════════════════════════════════════════════════════


class TestReadOnlyHealthPath:
    """--health path (sense_convergence_evidence) never mutates events.jsonl."""

    def test_detection_never_writes_events(self, tmp_path):
        """sense_convergence_evidence() is read-only regardless of breach state."""
        ws = make_workspace(tmp_path)
        write_vector(ws, "REQ-F-FOO-001", {"design": {"status": "converged"}})
        write_vector(ws, "REQ-F-BAR-001", {"code": {"status": "converged"}})
        events_path = write_events(ws, [
            {"event_type": "project_initialized", "project": "test"}
        ])
        original_content = events_path.read_text()

        result = sense_convergence_evidence(ws, events_path)
        assert result.breached

        assert events_path.read_text() == original_content

    def test_repair_is_only_mutation_path(self, tmp_path):
        """Calling repair_convergence_evidence appends; detection does not."""
        ws = make_workspace(tmp_path)
        events_path = write_events(ws, [
            {"event_type": "project_initialized", "project": "test"}
        ])
        gap = make_gap("REQ-F-FOO-001", "design", ws)
        provenance = make_provenance()

        before_lines = events_path.read_text().strip().split("\n")
        repair_convergence_evidence([gap], provenance, events_path)
        after_lines = events_path.read_text().strip().split("\n")

        assert len(after_lines) == len(before_lines) + 1
        new_event = json.loads(after_lines[-1])
        assert new_event["event_type"] == "edge_converged"
