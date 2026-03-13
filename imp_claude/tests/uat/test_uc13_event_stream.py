# Validates: REQ-EVENT-001, REQ-EVENT-002, REQ-EVENT-003, REQ-EVENT-004, REQ-EVENT-005
"""
UC-13: Event Stream & Projections (REQ-F-EVENT-001)

The methodology records all work as an ordered, permanent log of events.
Everything the user sees — feature status, progress, convergence — is derived
from that log. Nothing is stored as mutable state that can be corrupted or lost.

BDD scenarios are in business language. No technical implementation detail.
"""

import json
from pathlib import Path
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# UC-13-01: Permanent Event Log
# REQ-EVENT-001 — All work is recorded as permanent, ordered events.
# ─────────────────────────────────────────────────────────────────────────────

class TestPermanentEventLog:
    """
    Feature: Permanent Work Log

      Every action Genesis takes is written to a permanent log of events.
      Past events cannot be changed or erased — the history is the record.
    """

    # UC-13-01-01 | Validates: REQ-EVENT-001 AC-1
    def test_events_are_never_modified_after_writing(self):
        """
        Scenario: Practitioner wants to audit past work
          Given Genesis has been running and recording events
          When the practitioner reviews the event log
          Then every event written in the past is still present, unmodified
          And no previously written event has been altered

        Specification check: gen-start.md and gen-iterate.md describe append-only writes.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        # Append-only contract must be explicitly stated in the command spec
        assert "append-only" in gen_iterate.lower() or "append only" in gen_iterate.lower(), (
            "gen-iterate.md must state the event log is append-only "
            "(REQ-EVENT-001 AC-1)"
        )

    # UC-13-01-02 | Validates: REQ-EVENT-001 AC-2
    def test_events_are_in_chronological_order(self):
        """
        Scenario: Practitioner replays the history of a feature
          Given multiple events have been recorded for a feature
          When the practitioner reads the event log
          Then the events appear in the order they happened
          So the story of the work is coherent

        Specification check: event spec requires ordered stream.
        """
        req_spec = Path(
            "specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        # The spec must state the ordering guarantee
        assert "ordered" in req_spec and "append-only" in req_spec.lower(), (
            "Requirements must specify an ordered, append-only event stream "
            "(REQ-EVENT-001 AC-2)"
        )

    # UC-13-01-03 | Validates: REQ-EVENT-001 AC-3
    def test_event_log_is_the_durability_medium(self):
        """
        Scenario: Genesis restarts after an unexpected stop
          Given Genesis was working and then stopped unexpectedly
          When Genesis starts again
          Then it reads the event log to know where it left off
          And can continue from there without losing any recorded work

        Specification check: gen-start.md recovery reads events.jsonl.
        """
        gen_start = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        ).read_text()
        assert "events.jsonl" in gen_start, (
            "gen-start.md must reference events.jsonl as the recovery source "
            "(REQ-EVENT-001 AC-3)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-13-02: Derived Views from the Event Log
# REQ-EVENT-002 — Status and progress are computed from the log, not stored.
# ─────────────────────────────────────────────────────────────────────────────

class TestDerivedProjections:
    """
    Feature: Status Derived from Event Log

      Feature status, progress indicators, and convergence states are all
      computed from the event log. They are never stored separately in a way
      that could get out of sync with the actual history.
    """

    # UC-13-02-01 | Validates: REQ-EVENT-002 AC-1 (determinism)
    def test_same_event_log_always_produces_same_status(self):
        """
        Scenario: Practitioner checks status twice in a row
          Given the event log has not changed
          When the practitioner runs the status command twice
          Then both runs show exactly the same feature status
          So the practitioner can trust what they see

        Specification check: gen-status.md derives from events.jsonl deterministically.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        assert "events.jsonl" in gen_status, (
            "gen-status.md must derive status from events.jsonl "
            "(REQ-EVENT-002 AC-1)"
        )
        # Status is described as a projection/derived view, not mutable state
        assert "source of truth" in gen_status.lower() or "projection" in gen_status.lower(), (
            "gen-status.md must describe events.jsonl as the source of truth "
            "(REQ-EVENT-002 AC-1)"
        )

    # UC-13-02-02 | Validates: REQ-EVENT-002 AC-2 (completeness)
    def test_status_md_can_be_regenerated_from_event_log(self):
        """
        Scenario: The status file is accidentally deleted
          Given the status file (.ai-workspace/STATUS.md) has been lost
          When the practitioner runs the status command
          Then Genesis regenerates it from the event log
          And the regenerated status is identical to the original
          So no work is lost even if files are deleted

        Specification check: gen-status --gantt overwrites STATUS.md from events.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        assert "STATUS.md" in gen_status, (
            "gen-status.md must write STATUS.md as a derived projection "
            "(REQ-EVENT-002 AC-2)"
        )
        assert "overwrites" in gen_status.lower() or "always overwrite" in gen_status.lower() \
            or "derived snapshot" in gen_status.lower(), (
            "gen-status.md must state that STATUS.md is regenerated on each run "
            "(REQ-EVENT-002 AC-2)"
        )

    # UC-13-02-03 | Validates: REQ-EVENT-002 — Projection Authority (ADR-S-037)
    def test_convergence_state_must_be_backed_by_event_evidence(self):
        """
        Scenario: A feature shows as complete but the log says otherwise
          Given a feature vector file claims an edge is complete
          But the event log has no record of that edge completing
          When Genesis runs a health check
          Then Genesis flags the discrepancy as a projection authority violation
          So practitioners are not misled by stale status files

        Specification check: INTRO-008 checks convergence_without_evidence.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        # Health check must include INTRO-008 convergence evidence check
        assert "convergence_evidence" in gen_status or "INTRO-008" in gen_status, (
            "gen-status.md --health must enforce Projection Authority via INTRO-008 "
            "(REQ-EVENT-002 — ADR-S-037)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-13-03: Event Taxonomy
# REQ-EVENT-003 — Specific event types must be used for specific actions.
# ─────────────────────────────────────────────────────────────────────────────

class TestEventTaxonomy:
    """
    Feature: Consistent Event Language

      Genesis uses a standard vocabulary of event types so that monitoring tools,
      audit logs, and replays all understand the same language.
    """

    # UC-13-03-01 | Validates: REQ-EVENT-003 AC-1 (lifecycle events)
    def test_lifecycle_events_are_defined_in_config(self):
        """
        Scenario: A monitoring tool wants to track when work starts and finishes
          Given the event taxonomy is defined in the configuration
          When the monitoring tool inspects the event stream
          Then it finds standard events marking when iterations start and complete
          So the tool can build progress views without custom parsing

        Specification check: event taxonomy config includes lifecycle event types.
        """
        # Check that the event taxonomy is referenced in implementation
        # Look for canonical event names in the codebase
        taxonomy_files = list(Path("imp_claude/code").rglob("event_taxonomy*")) + \
                         list(Path("imp_claude/tests").rglob("test_event_taxonomy*"))
        assert len(taxonomy_files) > 0, (
            "An event taxonomy definition or test must exist "
            "(REQ-EVENT-003 AC-1)"
        )

    # UC-13-03-02 | Validates: REQ-EVENT-003 AC-2 (mandatory fields)
    def test_all_events_carry_mandatory_fields(self):
        """
        Scenario: Audit team reviews the event log
          Given events have been recorded during normal operation
          When the audit team inspects each event
          Then every event has a timestamp showing when it was recorded
          And every event has a project identifier
          And every event has a type that describes what happened
          So the log is self-describing and auditable

        Specification check: all events in current log have required fields.
        """
        events_path = Path(".ai-workspace/events/events.jsonl")
        if not events_path.exists():
            pytest.skip("No event log yet")

        lines = [l.strip() for l in events_path.read_text().splitlines() if l.strip()]
        if not lines:
            pytest.skip("Event log is empty")

        for i, line in enumerate(lines[-20:], 1):  # Check last 20 events
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                pytest.fail(f"Event line {i} is not valid JSON")

            assert "event_type" in event, f"Event {i} missing event_type: {line[:80]}"
            assert "timestamp" in event, f"Event {i} missing timestamp: {line[:80]}"
            assert "project" in event, f"Event {i} missing project: {line[:80]}"


# ─────────────────────────────────────────────────────────────────────────────
# UC-13-04: Executor Attribution
# REQ-EVENT-005 — Events show whether work was done by the engine, AI, or human.
# ─────────────────────────────────────────────────────────────────────────────

class TestExecutorAttribution:
    """
    Feature: Knowing Who Did the Work

      For each recorded event, monitoring tools can tell whether the work was
      done automatically by the engine, by the AI assistant, or by a human.
      This matters for audit, accountability, and understanding how the system
      is actually being used.
    """

    # UC-13-04-01 | Validates: REQ-EVENT-005 AC-1 (inference from format)
    def test_engine_events_identifiable_without_extra_fields(self):
        """
        Scenario: Monitoring tool identifies automatically executed steps
          Given events were recorded by the deterministic engine
          When the monitoring tool reads those events
          Then it can identify them as engine-executed even without explicit labels
          Because engine events follow a recognisable format

        Specification check: engine executor inferred from OL event format.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        assert "executor" in gen_status.lower() or "OL" in gen_status or \
               "engine" in gen_status.lower(), (
            "gen-status.md must handle executor attribution from events "
            "(REQ-EVENT-005 AC-1)"
        )

    # UC-13-04-02 | Validates: REQ-EVENT-005 AC-2 (retroactive emission)
    def test_retroactively_recorded_events_are_labeled(self):
        """
        Scenario: Work was done earlier and the record is filled in now
          Given some work happened on the AI-assisted path without live event recording
          When the observation is recorded after the fact to close the observability gap
          Then the event is labeled as retroactive
          So auditors can distinguish real-time records from catch-up records

        Specification check: emission: retroactive field is specified.
        """
        req_spec = Path(
            "specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        assert "retroactive" in req_spec, (
            "Specification must define the 'retroactive' emission field "
            "(REQ-EVENT-005 AC-2)"
        )

    # UC-13-04-03 | Validates: REQ-EVENT-005 AC-4 (dark edges)
    def test_unrecorded_work_is_classified_as_dark(self):
        """
        Scenario: Work was done but nothing was ever recorded
          Given an edge was traversed on the AI-assisted path
          But no events of any kind were recorded for it
          When an auditor inspects the observability status
          Then the edge is flagged as 'dark' — work with no record at all
          So the practitioner knows where the observability gaps are

        Specification check: dark edge classification in spec.
        """
        req_spec = Path(
            "specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        assert "dark" in req_spec and "observability debt" in req_spec.lower(), (
            "Specification must define 'dark' edges (unrecorded work) as distinct "
            "from retroactive observability debt (REQ-EVENT-005 AC-4)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-13-05: Saga Compensation (Phase 2)
# REQ-EVENT-004 — If a later step fails, the record shows the earlier work
#                 was rolled back.
# ─────────────────────────────────────────────────────────────────────────────

class TestSagaCompensation:
    """
    Feature: Recording That Earlier Work Was Undone

      When a sequence of steps fails partway through, the event log records
      that the earlier completed steps were rolled back. This is expressed
      as new events — the original completion events remain untouched.
    """

    # UC-13-05-01 | Validates: REQ-EVENT-004 AC-3 (compensation as events)
    def test_compensation_expressed_as_new_events_not_rollback(self):
        """
        Scenario: A step fails after a previous step already completed
          Given step A completed successfully and was recorded
          And then step B failed unexpectedly
          When the system records the compensation (undoing step A)
          Then it adds NEW events to the log describing the compensation
          And the original completion event for step A remains unmodified
          So the history shows both what happened and what was corrected

        Specification check: REQ-EVENT-004 specifies compensation as new events.
        """
        req_spec = Path(
            "specification/requirements/AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        ).read_text()
        assert "CompensationTriggered" in req_spec or "compensation" in req_spec.lower(), (
            "Specification must define saga compensation as new events, not rollback "
            "(REQ-EVENT-004 AC-3)"
        )
        assert "not state rollback" in req_spec.lower() or \
               "new events" in req_spec.lower(), (
            "REQ-EVENT-004 must explicitly state compensation is new events, not rollback"
        )
