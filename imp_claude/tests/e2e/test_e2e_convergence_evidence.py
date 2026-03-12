# Validates: REQ-SENSE-001 (INTRO-008 convergence_evidence_present)
# Validates: REQ-EVENT-002 (Projection Authority — workspace claims subordinate to stream)
# Validates: REQ-LIFE-006 (convergence_without_evidence signal source)
"""E2E tests for convergence_evidence_present (ADR-S-037 §2).

These tests operate at workspace scale — real YAML vectors, real events.jsonl
files — and verify end-to-end detection and reporting behaviour.

Two test classes:

  TestWorkspaceScaleDetection  — workspace-level check across realistic workspaces.
    No Claude CLI required. Verifies the check function against real filesystem state.
    Marked: e2e (runs in the e2e suite, not the fast unit suite)

  TestGenesisNavigatorScenario — exact reproduction of the genesis_navigator
    post-mortem scenario: code-first build, synthetic workspace retrofit,
    zero convergence events. Verifies the check detects all 26 gaps that the
    homeostatic loop would have missed before ADR-S-037.

Run:
    pytest imp_claude/tests/e2e/test_e2e_convergence_evidence.py -v -m e2e -s
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml


# ── Path setup ────────────────────────────────────────────────────────────────

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "imp_claude" / "code"))

from genesis.workspace_integrity import (
    check_convergence_evidence,
    EvidenceGap,
    ConvergenceEvidenceReport,
    TERMINAL_CONVERGENCE_EVENTS,
    LIFECYCLE_ONLY_EVENTS,
)


# ── Workspace builder helpers ─────────────────────────────────────────────────


def _build_workspace(root: Path) -> Path:
    for sub in ("active", "completed"):
        (root / ".ai-workspace" / "features" / sub).mkdir(parents=True)
    (root / ".ai-workspace" / "events").mkdir(parents=True)
    return root


def _write_vector(
    root: Path,
    feature_id: str,
    trajectory: dict,
    folder: str = "active",
) -> Path:
    d = root / ".ai-workspace" / "features" / folder
    d.mkdir(parents=True, exist_ok=True)
    p = d / f"{feature_id}.yml"
    p.write_text(yaml.dump({
        "feature": feature_id,
        "status": "in_progress",
        "profile": "standard",
        "trajectory": trajectory,
    }))
    return p


def _write_events(root: Path, events: list[dict]) -> Path:
    p = root / ".ai-workspace" / "events" / "events.jsonl"
    p.write_text("\n".join(json.dumps(e) for e in events) + "\n" if events else "")
    return p


def _edge_converged(feature: str, edge: str, **kw) -> dict:
    return {"event_type": "edge_converged", "feature": feature, "edge": edge, **kw}


def _iteration_completed(feature: str, edge: str, status: str = "converged") -> dict:
    return {"event_type": "iteration_completed", "feature": feature, "edge": edge, "status": status}


# ═══════════════════════════════════════════════════════════════════════════════
# TestGenesisNavigatorScenario
#
# Structurally faithful simulation of the genesis_navigator post-mortem (2026-03-12):
#   - 13 features, all claiming converged on 2 edges  (same as production)
#   - 131 synthetic lifecycle events: 1 project_initialized +
#     13 features × 2 edges × 5 events (edge_started, 3× iteration_completed,
#     1× iteration_completed{status:converged}) — same pattern as production,
#     synthetic timestamps
#   - Zero edge_converged or ConvergenceAchieved events  (same as production)
#   - Software: functionally correct
#   - Methodology: evidentially broken (dark convergence)
#
# Note: the actual genesis_navigator events.jsonl had ~94 events with fewer
# iteration_completed events per edge. This simulation uses a consistent 5-event
# pattern per edge for repeatability. The critical invariant under test is the
# same: lifecycle events alone do not satisfy the convergence evidence check.
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.e2e
class TestGenesisNavigatorScenario:
    """Reproduce the genesis_navigator post-mortem case that motivated ADR-S-037."""

    FEATURES = [
        "REQ-F-NAV-CORE-001",
        "REQ-F-NAV-GRAPH-001",
        "REQ-F-NAV-EVENTS-001",
        "REQ-F-NAV-STATUS-001",
        "REQ-F-NAV-HEALTH-001",
        "REQ-F-NAV-WORKSPACE-001",
        "REQ-F-NAV-ITERATE-001",
        "REQ-F-NAV-CONSENSUS-001",
        "REQ-F-NAV-SPAWN-001",
        "REQ-F-NAV-REVIEW-001",
        "REQ-F-NAV-RELEASE-001",
        "REQ-F-NAV-INIT-001",
        "REQ-F-NAV-GAPS-001",
    ]
    EDGES = ["design→code", "code↔unit_tests"]

    def _build_navigator_workspace(self, root: Path) -> Path:
        """Build the genesis_navigator Pass 2 state: synthetic workspace, no events."""
        _build_workspace(root)
        for fid in self.FEATURES:
            _write_vector(root, fid, {
                edge: {"status": "converged", "iteration": 1, "delta": 0}
                for edge in self.EDGES
            })
        return root

    def _build_lifecycle_events_no_convergence(self, root: Path):
        """131 lifecycle events — project_initialized, edge_started, iteration_completed.
        Zero edge_converged. Structurally simulates the genesis_navigator pattern.
        Event count: 1 + 13 features × 2 edges × 5 events = 131.
        """
        events = [{"event_type": "project_initialized", "project": "genesis_navigator"}]
        for fid in self.FEATURES:
            for edge in self.EDGES:
                events.append({"event_type": "edge_started", "feature": fid, "edge": edge})
                # Several iteration_completed events per edge — even with status:converged
                for i in range(1, 4):
                    events.append(_iteration_completed(fid, edge, "iterating"))
                events.append(_iteration_completed(fid, edge, "converged"))
        _write_events(root, events)

    def test_genesis_navigator_has_26_gaps(self, tmp_path):
        """13 features × 2 edges = 26 convergence evidence gaps.

        This is the exact scenario that motivated ADR-S-037. The workspace
        YAML files all claim converged. The event stream has 94 events but
        zero terminal convergence events. The check must detect all 26 gaps.
        """
        root = self._build_navigator_workspace(tmp_path)
        _write_events(root, [])  # zero events

        report = check_convergence_evidence(root)

        assert not report.passed
        assert report.delta == 26, (
            f"Expected 26 gaps (13 features × 2 edges), got {report.delta}"
        )
        assert report.checked_features == 13
        assert report.checked_edges == 26

    def test_genesis_navigator_lifecycle_events_do_not_satisfy_check(self, tmp_path):
        """94 lifecycle events including iteration_completed{status:converged} → still 26 gaps.

        This is the critical ADR-S-037 assertion: lifecycle events (including
        iteration_completed) are NOT terminal convergence evidence.
        """
        root = self._build_navigator_workspace(tmp_path)
        self._build_lifecycle_events_no_convergence(root)

        events_path = root / ".ai-workspace" / "events" / "events.jsonl"
        event_count = len(events_path.read_text().strip().splitlines())

        report = check_convergence_evidence(root)

        # 1 project_initialized + 13 features × 2 edges × 5 events = 131
        assert event_count == 131, (
            f"Expected 131 synthetic lifecycle events, got {event_count}"
        )
        assert not report.passed, (
            f"With {event_count} lifecycle events but zero terminal convergence events, "
            "check must still FAIL for all 26 edges"
        )
        assert report.delta == 26

    def test_genesis_navigator_retroactive_repair_closes_gaps(self, tmp_path):
        """After real evaluators run and retroactive edge_converged events are appended,
        the check must pass. This validates the ADR-S-037 §3 remediation path.
        """
        root = self._build_navigator_workspace(tmp_path)
        self._build_lifecycle_events_no_convergence(root)

        # Simulate Pass 3: real evaluators ran, all passed, retroactive events appended
        events_path = root / ".ai-workspace" / "events" / "events.jsonl"
        retroactive_events = []
        for fid in self.FEATURES:
            for edge in self.EDGES:
                retroactive_events.append(
                    _edge_converged(fid, edge, emission="retroactive")
                )
        with events_path.open("a") as f:
            for ev in retroactive_events:
                f.write(json.dumps(ev) + "\n")

        report = check_convergence_evidence(root)

        assert report.passed, (
            "After appending retroactive edge_converged events for all 26 edges, "
            "convergence_evidence_present must pass"
        )
        assert report.delta == 0

    def test_genesis_navigator_partial_repair_reports_remaining_gaps(self, tmp_path):
        """If only some features are repaired, gaps remain for the others."""
        root = self._build_navigator_workspace(tmp_path)
        _write_events(root, [])

        # Repair only the first 5 features
        repaired = self.FEATURES[:5]
        events_path = root / ".ai-workspace" / "events" / "events.jsonl"
        with events_path.open("a") as f:
            for fid in repaired:
                for edge in self.EDGES:
                    f.write(json.dumps(_edge_converged(fid, edge, emission="retroactive")) + "\n")

        report = check_convergence_evidence(root)

        unrepaired = len(self.FEATURES) - 5
        expected_gaps = unrepaired * len(self.EDGES)
        assert report.delta == expected_gaps
        repaired_ids = set(repaired)
        for gap in report.gaps:
            assert gap.feature_id not in repaired_ids, (
                f"Repaired feature {gap.feature_id} should not appear in gaps"
            )

    def test_genesis_navigator_gaps_are_addressable_via_interoceptive_signal(self, tmp_path):
        """Each gap produces a well-formed interoceptive_signal payload.

        The sensory service wraps these into interoceptive_signal events and
        sends them to affect triage. This test verifies the payload shape for
        all 26 gaps — matching the expected INTRO-008 signal contract.
        """
        root = self._build_navigator_workspace(tmp_path)
        _write_events(root, [])

        report = check_convergence_evidence(root)

        assert report.delta == 26
        for gap in report.gaps:
            signal = gap.as_interoceptive_signal()
            assert signal["monitor_id"] == "INTRO-008"
            assert signal["severity"] == "critical"
            assert signal["observation"] == "convergence_without_evidence"
            assert len(signal["affected_features"]) == 1
            assert signal["affected_features"][0] == gap.feature_id
            assert signal["edge"] == gap.edge
            # Signal must not be an event — no event_type field
            assert "event_type" not in signal


# ═══════════════════════════════════════════════════════════════════════════════
# TestWorkspaceScaleDetection
#
# Realistic workspace scenarios at project scale.
# Tests the check function against filesystem state comparable to a real
# genesis project mid-iteration.
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.e2e
class TestWorkspaceScaleDetection:
    """Workspace-scale detection — multiple features, multiple edges, mixed evidence."""

    def test_clean_workspace_passes_immediately(self, tmp_path):
        """A properly evidenced workspace passes with zero gaps."""
        root = _build_workspace(tmp_path)
        feature_ids = [f"REQ-F-X-{i:03d}" for i in range(1, 6)]
        for fid in feature_ids:
            _write_vector(root, fid, {
                "design→code": {"status": "converged"},
                "code↔unit_tests": {"status": "converged"},
            })
        _write_events(root, [
            _edge_converged(fid, edge)
            for fid in feature_ids
            for edge in ["design→code", "code↔unit_tests"]
        ])

        report = check_convergence_evidence(root)

        assert report.passed
        assert report.checked_features == 5
        assert report.checked_edges == 10

    def test_mixed_profile_workspace(self, tmp_path):
        """Features at different stages: some converged, some iterating, some pending."""
        root = _build_workspace(tmp_path)

        # Feature A: fully converged with evidence
        _write_vector(root, "REQ-F-A-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
        })
        # Feature B: currently iterating — no convergence expected yet
        _write_vector(root, "REQ-F-B-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "iterating"},
        })
        # Feature C: dark convergence — claims converged, no events
        _write_vector(root, "REQ-F-C-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
        })

        _write_events(root, [
            _edge_converged("REQ-F-A-001", "design→code"),
            _edge_converged("REQ-F-A-001", "code↔unit_tests"),
            _edge_converged("REQ-F-B-001", "design→code"),
            # B's code↔unit_tests still iterating — correct
            # C has zero events — dark convergence
        ])

        report = check_convergence_evidence(root)

        assert not report.passed
        assert report.delta == 2  # C has 2 converged edges with no evidence
        gap_features = {g.feature_id for g in report.gaps}
        assert gap_features == {"REQ-F-C-001"}

    def test_completed_vectors_included_in_scan(self, tmp_path):
        """Completed feature vectors are checked — dark convergence persists after archival."""
        root = _build_workspace(tmp_path)

        _write_vector(root, "REQ-F-OLD-001", {
            "design→code": {"status": "converged"},
            "code↔unit_tests": {"status": "converged"},
        }, folder="completed")

        _write_events(root, [])

        report = check_convergence_evidence(root)
        assert report.delta == 2
        assert all(g.feature_id == "REQ-F-OLD-001" for g in report.gaps)

    def test_canonical_convergence_achieved_event_satisfies(self, tmp_path):
        """ConvergenceAchieved (REQ-EVENT-003 canonical) satisfies across 5 features."""
        root = _build_workspace(tmp_path)
        feature_ids = [f"REQ-F-X-{i:03d}" for i in range(1, 6)]
        for fid in feature_ids:
            _write_vector(root, fid, {"code↔unit_tests": {"status": "converged"}})
        _write_events(root, [
            {"event_type": "ConvergenceAchieved", "feature": fid, "edge": "code↔unit_tests"}
            for fid in feature_ids
        ])

        report = check_convergence_evidence(root)
        assert report.passed

    def test_iteration_completed_flood_does_not_satisfy(self, tmp_path):
        """Many iteration_completed events — even with status:converged — cannot satisfy."""
        root = _build_workspace(tmp_path)
        fid = "REQ-F-FLOOD-001"
        _write_vector(root, fid, {"code↔unit_tests": {"status": "converged"}})

        # Flood of lifecycle events, all with status:converged — none terminal
        events = [
            _iteration_completed(fid, "code↔unit_tests", status="converged")
            for _ in range(50)
        ]
        _write_events(root, events)

        report = check_convergence_evidence(root)
        assert not report.passed, (
            "50 iteration_completed events cannot satisfy convergence_evidence_present"
        )
        assert report.delta == 1

    def test_large_workspace_performance(self, tmp_path):
        """Check must complete in reasonable time for a large workspace (50 features × 3 edges)."""
        import time
        root = _build_workspace(tmp_path)
        n_features = 50
        edges = ["design→code", "code↔unit_tests", "requirements→design"]
        feature_ids = [f"REQ-F-LARGE-{i:03d}" for i in range(n_features)]

        for fid in feature_ids:
            _write_vector(root, fid, {e: {"status": "converged"} for e in edges})
        _write_events(root, [
            _edge_converged(fid, edge)
            for fid in feature_ids
            for edge in edges
        ])

        t0 = time.perf_counter()
        report = check_convergence_evidence(root)
        elapsed = time.perf_counter() - t0

        assert report.passed
        assert report.checked_edges == n_features * len(edges)
        assert elapsed < 5.0, f"Check took {elapsed:.2f}s — should be < 5s for 150 edges"

    def test_mixed_event_format_workspace(self, tmp_path):
        """workspace with both OL-format (instance_id) and flat-format (feature) events."""
        root = _build_workspace(tmp_path)
        _write_vector(root, "REQ-F-OL-001", {"code↔unit_tests": {"status": "converged"}})
        _write_vector(root, "REQ-F-FLAT-001", {"code↔unit_tests": {"status": "converged"}})

        _write_events(root, [
            # OL format — instance_id field
            {"event_type": "edge_converged", "instance_id": "REQ-F-OL-001", "edge": "code↔unit_tests"},
            # Flat format — feature field
            {"event_type": "edge_converged", "feature": "REQ-F-FLAT-001", "edge": "code↔unit_tests"},
        ])

        report = check_convergence_evidence(root)
        assert report.passed

    def test_real_ai_sdlc_method_workspace(self):
        """Smoke test against the actual ai_sdlc_method workspace.

        This test reads the live workspace and events. It does NOT assert pass/fail
        (the workspace may legitimately have gaps from two-pass builds).
        It asserts the check runs without error and produces a structured report.
        """
        workspace_root = PROJECT_ROOT / "projects" / "genesis_navigator"
        if not workspace_root.exists():
            pytest.skip("genesis_navigator workspace not present")

        report = check_convergence_evidence(workspace_root)

        # Structural assertions — the check must complete and produce a report
        assert isinstance(report, ConvergenceEvidenceReport)
        assert isinstance(report.gaps, list)
        assert report.checked_features >= 0
        assert report.delta >= 0

        # Log the result for human inspection
        print(f"\ngenesis_navigator workspace scan:")
        print(f"  Features checked: {report.checked_features}")
        print(f"  Edges checked:    {report.checked_edges}")
        print(f"  Gaps found:       {report.delta}")
        if report.gaps:
            print(f"  Gap sample:")
            for gap in report.gaps[:5]:
                print(f"    {gap.feature_id} / {gap.edge}")
            if len(report.gaps) > 5:
                print(f"    ... and {len(report.gaps) - 5} more")
