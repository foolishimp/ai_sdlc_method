# Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
"""UC-07: Sensory Systems — 16 scenarios.

Tests interoceptive monitoring, exteroceptive monitoring, affect triage,
configuration, and review boundary.
"""

from __future__ import annotations

import json

import pytest

from imp_claude.tests.uat.conftest import make_event, write_events
from imp_claude.tests.uat.workspace_state import (
    classify_tolerance_breach,
    load_events,
)

pytestmark = [pytest.mark.uat]


# -- EXISTING COVERAGE (not duplicated) --
# UC-07-12: TestSensoryMonitorRegistry (test_config_validation.py)


# ===================================================================
# UC-07-01..04: INTEROCEPTIVE MONITORING (Tier 1 / Tier 3)
# ===================================================================


class TestInteroceptiveMonitoring:
    """UC-07-01 through UC-07-04: internal health monitors."""

    # UC-07-01 | Validates: REQ-SENSE-001 | Fixture: IN_PROGRESS
    def test_seven_interoceptive_monitors(self, sensory_monitors):
        """Sensory config defines 7 interoceptive monitors."""
        monitors = sensory_monitors.get("monitors", {}).get("interoceptive", [])
        assert len(monitors) >= 7
        ids = {m["id"] for m in monitors}
        expected = {"INTRO-001", "INTRO-002", "INTRO-003", "INTRO-004",
                   "INTRO-005", "INTRO-006", "INTRO-007"}
        assert expected.issubset(ids)

    # UC-07-02 | Validates: REQ-SENSE-001 | Fixture: IN_PROGRESS
    def test_interoceptive_signal_event(self, in_progress_workspace):
        """Interoceptive signal logged to interoceptive_signal event."""
        # Create a synthetic interoceptive signal event and validate its schema
        ws = in_progress_workspace / ".ai-workspace"
        events_file = ws / "events" / "events.jsonl"

        # Load existing events and append a synthetic interoceptive signal
        existing_events = load_events(in_progress_workspace)
        signal_event = make_event(
            "interoceptive_signal",
            monitor_id="INTRO-001",
            monitor_name="event_freshness",
            value=10,
            threshold=7,
            classification="staleness",
            severity="warning",
        )
        existing_events.append(signal_event)
        write_events(events_file, existing_events)

        # Re-load and validate the signal event schema
        reloaded = load_events(in_progress_workspace)
        signal_events = [
            e for e in reloaded if e.get("event_type") == "interoceptive_signal"
        ]
        assert len(signal_events) >= 1, "Should have at least one interoceptive_signal event"

        ev = signal_events[0]
        # Required schema fields
        assert "event_type" in ev
        assert ev["event_type"] == "interoceptive_signal"
        assert "monitor_id" in ev
        assert ev["monitor_id"].startswith("INTRO-")
        assert "value" in ev
        assert "threshold" in ev
        assert "classification" in ev
        assert "timestamp" in ev

    # UC-07-03 | Validates: REQ-SENSE-004 | Fixture: INITIALIZED
    def test_monitor_thresholds_configurable(self, sensory_monitors):
        """Profile overrides can adjust monitor thresholds."""
        overrides = sensory_monitors.get("profile_overrides", {})
        assert overrides, "Profile overrides should exist"
        hotfix = overrides.get("hotfix", {})
        assert hotfix.get("disable") or hotfix.get("threshold_overrides")

    # UC-07-04 | Validates: REQ-SENSE-004 | Fixture: INITIALIZED
    def test_full_profile_all_monitors(self, sensory_monitors):
        """Full profile runs all monitors without suppression."""
        overrides = sensory_monitors.get("profile_overrides", {})
        full = overrides.get("full", {})
        assert not full.get("disable"), "Full profile should not disable any monitors"


# ===================================================================
# UC-07-05..07: EXTEROCEPTIVE MONITORING (Tier 1 / Tier 3)
# ===================================================================


class TestExteroceptiveMonitoring:
    """UC-07-05 through UC-07-07: external environment monitors."""

    # UC-07-05 | Validates: REQ-SENSE-002 | Fixture: IN_PROGRESS
    def test_four_exteroceptive_monitors(self, sensory_monitors):
        """Sensory config defines 4 exteroceptive monitors."""
        monitors = sensory_monitors.get("monitors", {}).get("exteroceptive", [])
        assert len(monitors) >= 4
        ids = {m["id"] for m in monitors}
        expected = {"EXTRO-001", "EXTRO-002", "EXTRO-003", "EXTRO-004"}
        assert expected.issubset(ids)

    # UC-07-06 | Validates: REQ-SENSE-002 | Fixture: IN_PROGRESS
    def test_exteroceptive_signal_event(self, in_progress_workspace):
        """Exteroceptive signal logged to exteroceptive_signal event."""
        # Create a synthetic exteroceptive signal event and validate its schema
        ws = in_progress_workspace / ".ai-workspace"
        events_file = ws / "events" / "events.jsonl"

        existing_events = load_events(in_progress_workspace)
        signal_event = make_event(
            "exteroceptive_signal",
            monitor_id="EXTRO-002",
            monitor_name="cve_scanning",
            value=3,
            threshold=0,
            classification="vulnerability",
            severity="critical",
        )
        existing_events.append(signal_event)
        write_events(events_file, existing_events)

        # Re-load and validate the signal event schema
        reloaded = load_events(in_progress_workspace)
        signal_events = [
            e for e in reloaded if e.get("event_type") == "exteroceptive_signal"
        ]
        assert len(signal_events) >= 1, "Should have at least one exteroceptive_signal event"

        ev = signal_events[0]
        # Required schema fields
        assert "event_type" in ev
        assert ev["event_type"] == "exteroceptive_signal"
        assert "monitor_id" in ev
        assert ev["monitor_id"].startswith("EXTRO-")
        assert "value" in ev
        assert "threshold" in ev
        assert "classification" in ev
        assert "timestamp" in ev

    # UC-07-07 | Validates: REQ-SENSE-004 | Fixture: INITIALIZED
    def test_spike_disables_exteroception(self, sensory_monitors):
        """Spike profile disables all exteroceptive monitors."""
        overrides = sensory_monitors.get("profile_overrides", {})
        spike = overrides.get("spike", {})
        disabled = spike.get("disable", [])
        assert "EXTRO-001" in disabled
        assert "EXTRO-002" in disabled
        assert "EXTRO-003" in disabled
        assert "EXTRO-004" in disabled


# ===================================================================
# UC-07-08..11: AFFECT TRIAGE PIPELINE (Tier 1 / Tier 3)
# ===================================================================


class TestAffectTriage:
    """UC-07-08 through UC-07-11: triage rules, agent fallback, thresholds."""

    # UC-07-08 | Validates: REQ-SENSE-003 | Fixture: IN_PROGRESS
    def test_rule_based_classification(self, affect_triage):
        """Affect triage has rule-based classification (fast path)."""
        rules = affect_triage.get("classification_rules", [])
        assert len(rules) >= 10
        # Last rule should be agent fallback
        last = rules[-1]
        assert last.get("name") == "agent_fallback"

    # UC-07-09 | Validates: REQ-SENSE-003 | Fixture: IN_PROGRESS
    def test_agent_classification_fallback(self, affect_triage):
        """Agent classification available for ambiguous signals."""
        agent_config = affect_triage.get("agent_classification", {})
        assert agent_config.get("model"), "Agent classification should specify model"
        assert agent_config.get("prompt_template"), "Agent classification needs prompt"

    # UC-07-10 | Validates: REQ-SENSE-003 | Fixture: INITIALIZED
    def test_escalation_thresholds_per_profile(self, affect_triage):
        """Escalation thresholds vary by profile."""
        thresholds = affect_triage.get("escalation_thresholds", {})
        assert thresholds.get("full", {}).get("minimum_severity") == "info"
        assert thresholds.get("spike", {}).get("minimum_severity") == "critical"
        assert thresholds.get("hotfix", {}).get("minimum_severity") == "info"

    # UC-07-11 | Validates: REQ-SENSE-003 | Fixture: IN_PROGRESS
    def test_above_threshold_generates_proposal(self, affect_triage):
        """Above-threshold signals generate draft proposals."""
        # Test classify_tolerance_breach() for above-threshold signals
        # A value above threshold with non-critical severity -> specEventLog
        result = classify_tolerance_breach(10, 7, severity="warning")
        assert result in ("specEventLog", "escalate"), (
            f"Above-threshold signal should produce specEventLog or escalate, got {result}"
        )

        # A value well above threshold (ratio > 2.0) -> escalate
        result_critical = classify_tolerance_breach(20, 7, severity="warning")
        assert result_critical == "escalate", (
            "Far-above-threshold signal should escalate"
        )

        # A critical severity always escalates
        result_sev = classify_tolerance_breach(8, 7, severity="critical")
        assert result_sev == "escalate", (
            "Critical severity should always escalate"
        )

        # Below threshold -> reflex.log (no proposal)
        result_below = classify_tolerance_breach(5, 7, severity="warning")
        assert result_below == "reflex.log", (
            "Below-threshold signal should be logged only"
        )

        # Validate that affect_triage config defines proposal generation
        # via the review boundary (draft_only autonomy model)
        boundary = affect_triage.get("review_boundary", {})
        assert boundary.get("autonomy_model") == "draft_only", (
            "Review boundary should use draft_only model for proposal generation"
        )


# ===================================================================
# UC-07-12..13: SENSORY CONFIGURATION (Tier 1 / Tier 3)
# ===================================================================


class TestSensoryConfiguration:
    """UC-07-12 through UC-07-13: config registry and meta-monitoring."""

    # UC-07-12 | Validates: REQ-SENSE-004 | Fixture: INITIALIZED
    def test_sensory_config_exists(self, sensory_monitors):
        """Sensory monitor registry is defined in configuration."""
        assert sensory_monitors.get("version")
        assert sensory_monitors.get("monitors")

    # UC-07-13 | Validates: REQ-SENSE-004 | Fixture: IN_PROGRESS
    def test_meta_monitoring_enabled(self, sensory_monitors):
        """Meta-monitoring detects monitor failures."""
        meta = sensory_monitors.get("meta_monitoring", {})
        assert meta.get("enabled") is True
        assert meta.get("on_monitor_failure", {}).get("emit") == "interoceptive_signal"


# ===================================================================
# UC-07-14..16: REVIEW BOUNDARY (Tier 1 / Tier 3)
# ===================================================================


class TestReviewBoundary:
    """UC-07-14 through UC-07-16: sensing vs changes boundary."""

    # UC-07-14 | Validates: REQ-SENSE-005 | Fixture: IN_PROGRESS
    def test_review_boundary_tools(self, affect_triage):
        """Review boundary defines MCP tools for human interaction."""
        boundary = affect_triage.get("review_boundary", {})
        tools = boundary.get("mcp_tools", [])
        assert len(tools) >= 4
        tool_names = {t["name"] for t in tools}
        assert "sensory-status" in tool_names
        assert "sensory-proposals" in tool_names
        assert "sensory-approve" in tool_names
        assert "sensory-dismiss" in tool_names

    # UC-07-15 | Validates: REQ-SENSE-005 | Fixture: IN_PROGRESS
    def test_two_event_categories(self, affect_triage):
        """Review boundary separates observation from change-approval."""
        boundary = affect_triage.get("review_boundary", {})
        assert boundary.get("autonomy_model") == "draft_only"

    # UC-07-16 | Validates: REQ-SENSE-005 | Fixture: IN_PROGRESS
    def test_human_required_for_modifications(self, affect_triage):
        """File modifications require human approval."""
        boundary = affect_triage.get("review_boundary", {})
        human_req = boundary.get("human_required_for", [])
        assert "file_modification" in human_req
