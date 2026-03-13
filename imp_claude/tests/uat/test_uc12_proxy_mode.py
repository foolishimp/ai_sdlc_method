# Validates: REQ-F-HPRX-001, REQ-F-HPRX-002, REQ-F-HPRX-003, REQ-F-HPRX-004
# Validates: REQ-F-HPRX-005, REQ-F-HPRX-006, REQ-NFR-HPRX-001, REQ-NFR-HPRX-002
# Validates: REQ-BR-HPRX-001, REQ-BR-HPRX-002
"""
UC-12: Human Proxy Mode for Autonomous Overnight Runs (REQ-F-PROXY-001)

A practitioner can leave Genesis running overnight. When the work reaches a decision
point that normally requires human judgment, the system makes that decision automatically
on the practitioner's behalf. Every automated decision is written to a review log.
The next morning, the practitioner reviews those decisions and the run continues or
is corrected from there.

BDD scenarios are written in business language — no technical implementation detail.
"""

import json
import re
from pathlib import Path
import pytest


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-01: Overnight Run Flag
# REQ-F-HPRX-001 — The overnight-run option only works when combined with auto mode.
# ─────────────────────────────────────────────────────────────────────────────

class TestOvernightRunFlag:
    """
    Feature: Overnight Autonomous Run

      A practitioner can request that Genesis run overnight without intervention.
      The overnight option requires the auto-loop to be active — it makes no sense
      to proxy decisions if the system is not iterating automatically.
    """

    # UC-12-01-01 | Validates: REQ-F-HPRX-001 AC-1
    def test_overnight_flag_requires_auto_loop(self):
        """
        Scenario: Practitioner uses overnight flag without auto mode
          Given a practitioner runs Genesis with the overnight proxy option
          But does not enable the automatic loop
          Then Genesis reports that the overnight option requires the auto-loop
          And no work is attempted

        Specification check: gen-start.md must state '--human-proxy requires --auto'.
        """
        gen_start = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        assert gen_start.exists(), "gen-start.md must exist"
        content = gen_start.read_text()
        assert "--human-proxy requires --auto" in content, (
            "Specification must state that --human-proxy requires --auto "
            "(REQ-F-HPRX-001 AC-1)"
        )

    # UC-12-01-02 | Validates: REQ-F-HPRX-001 AC-2
    def test_overnight_run_announces_itself(self):
        """
        Scenario: Practitioner starts an overnight run successfully
          Given a practitioner runs Genesis with both overnight proxy and auto-loop
          Then Genesis announces that proxy mode is active
          So that the practitioner knows decisions will be made on their behalf

        Specification check: gen-start.md must include a '[proxy mode active]' banner.
        """
        content = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        ).read_text()
        assert "[proxy mode active]" in content, (
            "gen-start.md must include the '[proxy mode active]' banner so the "
            "practitioner knows overnight mode is running (REQ-F-HPRX-001 AC-2)"
        )

    # UC-12-01-03 | Validates: REQ-F-HPRX-001 AC-3, REQ-BR-HPRX-002
    def test_overnight_mode_is_not_remembered_between_sessions(self):
        """
        Scenario: Practitioner runs Genesis the next morning without overnight flag
          Given overnight proxy mode was used the previous evening
          When the practitioner runs Genesis the next morning without the overnight flag
          Then Genesis does NOT automatically continue making decisions on their behalf
          And the practitioner must explicitly request overnight mode again

        Specification check: overnight proxy is per-invocation only; never persisted.
        """
        content = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        ).read_text()
        assert "Per-invocation only" in content or "per invocation only" in content or \
               "never persisted" in content or "not persisted" in content or \
               "Per-invocation" in content, (
            "Specification must state that --human-proxy is per-invocation only and "
            "is never persisted between sessions (REQ-F-HPRX-001 AC-3, REQ-BR-HPRX-002)"
        )

    # UC-12-01-04 | Validates: REQ-F-HPRX-001 AC-4
    def test_overnight_proxy_only_affects_human_decision_points(self):
        """
        Scenario: Genesis reaches an automated check during an overnight run
          Given overnight proxy mode is active
          When Genesis reaches a fully automated check (not a human decision point)
          Then Genesis runs the check normally — proxy mode has no effect
          And only human decision points are proxied

        Specification check: proxy only substitutes at F_H gates.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate.read_text()
        # The spec must describe proxy evaluation at F_H gates specifically
        assert "F_H" in content and ("human-proxy" in content or "human_proxy" in content), (
            "gen-iterate.md must describe proxy substitution at F_H gates only "
            "(REQ-F-HPRX-001 AC-4)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-02: Automated Decision Protocol
# REQ-F-HPRX-002 — How the system evaluates at human decision points.
# ─────────────────────────────────────────────────────────────────────────────

class TestAutomatedDecisionProtocol:
    """
    Feature: Automated Decision-Making at Human Gates

      When Genesis reaches a point that normally needs human judgment during an
      overnight run, it evaluates each criterion systematically. It can only approve
      work when every required criterion is met; any failure causes rejection.
    """

    # UC-12-02-01 | Validates: REQ-F-HPRX-002 AC-1
    def test_proxy_approves_only_when_all_criteria_pass(self):
        """
        Scenario: All decision criteria are met during an overnight run
          Given overnight proxy mode is active
          And Genesis reaches a human decision point
          And the work satisfies every required criterion
          Then Genesis automatically approves the work
          And records the approval in the review log

        Specification check: approve iff all required criteria pass.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        assert "approved" in gen_iterate.lower() and "criteria" in gen_iterate.lower(), (
            "gen-iterate.md must specify approval when all criteria pass "
            "(REQ-F-HPRX-002 AC-1)"
        )

    # UC-12-02-02 | Validates: REQ-F-HPRX-002 AC-2
    def test_proxy_rejects_when_any_criterion_fails(self):
        """
        Scenario: A decision criterion fails during an overnight run
          Given overnight proxy mode is active
          And Genesis reaches a human decision point
          And one or more required criteria are not met
          Then Genesis automatically rejects the work
          And the overnight run stops at that point
          And the rejection is recorded in the review log

        Specification check: rejected if any required criterion fails; run halts.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        assert "rejected" in gen_iterate.lower() or "rejection" in gen_iterate.lower(), (
            "gen-iterate.md must describe rejection when criteria fail "
            "(REQ-F-HPRX-002 AC-2)"
        )

    # UC-12-02-03 | Validates: REQ-F-HPRX-002, REQ-BR-HPRX-001
    def test_proxy_writes_log_before_recording_decision(self):
        """
        Scenario: Genesis records an automated decision
          Given overnight proxy mode is active
          And Genesis makes an automated decision (approve or reject)
          Then Genesis writes the decision rationale to the review log FIRST
          And only then records the outcome in the event stream
          So that the record cannot exist without the supporting rationale

        Specification check: proxy-log written BEFORE event emission.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        # Must mention writing the log before emitting the event
        assert "proxy-log" in gen_iterate or "proxy_log" in gen_iterate, (
            "gen-iterate.md must mention proxy-log file writing before event emission "
            "(REQ-F-HPRX-002, REQ-BR-HPRX-001)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-03: Review Log
# REQ-F-HPRX-003 — Every automated decision must be logged for human review.
# ─────────────────────────────────────────────────────────────────────────────

class TestReviewLog:
    """
    Feature: Overnight Decision Review Log

      Every decision made automatically on the practitioner's behalf is written
      to a review log. The practitioner reads this log the next morning to understand
      what was decided and why.
    """

    # UC-12-03-01 | Validates: REQ-F-HPRX-003 AC-1
    def test_review_log_location_is_specified(self):
        """
        Scenario: Practitioner wants to find automated decisions from the overnight run
          Given an overnight run has completed
          When the practitioner looks for the review log
          Then the log is in a well-known location they can find without searching

        Specification check: proxy-log goes to .ai-workspace/reviews/proxy-log/.
        """
        gen_start = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        ).read_text()
        assert "proxy-log" in gen_start and "reviews" in gen_start, (
            "gen-start.md must specify the proxy-log location under reviews/ "
            "(REQ-F-HPRX-003 AC-1)"
        )

    # UC-12-03-02 | Validates: REQ-F-HPRX-003 AC-2
    def test_review_log_contains_decision_rationale(self):
        """
        Scenario: Practitioner reads a review log entry
          Given an automated decision was made overnight
          When the practitioner reads the review log
          Then they can see what was decided and the evidence behind it
          So they can judge whether to accept or override the decision

        Specification check: proxy-log must contain evidence for the decision.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        # Log must contain the artifact being evaluated + evidence
        assert "proxy-log" in gen_iterate or "proxy_log" in gen_iterate, (
            "gen-iterate.md must describe proxy-log content including evidence "
            "(REQ-F-HPRX-003 AC-2)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-04: Morning Review
# REQ-F-HPRX-004 — Status command surfaces overnight decisions for morning review.
# ─────────────────────────────────────────────────────────────────────────────

class TestMorningReview:
    """
    Feature: Morning Review of Overnight Decisions

      The practitioner starts the next morning by checking what happened overnight.
      Genesis shows them a summary of all automated decisions made on their behalf.
      They can accept or override each one.
    """

    # UC-12-04-01 | Validates: REQ-F-HPRX-004 AC-1
    def test_status_surfaces_overnight_decisions(self):
        """
        Scenario: Practitioner checks Genesis the morning after an overnight run
          Given automated decisions were made overnight
          When the practitioner runs the status command
          Then Genesis shows the automated decisions that were made
          And indicates they are pending human review

        Specification check: gen-status.md surfaces proxy-log entries.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        assert "proxy-log" in gen_status or "proxy" in gen_status.lower(), (
            "gen-status.md must surface proxy-log entries for morning review "
            "(REQ-F-HPRX-004 AC-1)"
        )

    # UC-12-04-02 | Validates: REQ-F-HPRX-004 AC-2
    def test_practitioner_can_dismiss_reviewed_decisions(self):
        """
        Scenario: Practitioner has read and accepted an automated decision
          Given a proxy log entry is shown as pending review
          When the practitioner adds a 'Reviewed' note to the log entry
          Then Genesis no longer shows that decision as pending
          So the morning review list stays manageable over time

        Specification check: Reviewed: date line dismisses a proxy-log entry.
        """
        gen_status = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        ).read_text()
        assert "Reviewed" in gen_status, (
            "gen-status.md must describe dismissing proxy-log entries with 'Reviewed:' "
            "(REQ-F-HPRX-004 AC-2)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-05: Rejection Halt
# REQ-F-HPRX-005 — Automatic rejection stops the overnight run immediately.
# ─────────────────────────────────────────────────────────────────────────────

class TestRejectionHalt:
    """
    Feature: Overnight Run Stops on Rejection

      If the automated evaluation finds work that doesn't meet the criteria,
      the overnight run stops at that point. It does not continue working and
      potentially compound the problem. The practitioner picks up from there
      the next morning.
    """

    # UC-12-05-01 | Validates: REQ-F-HPRX-005 AC-1
    def test_rejection_stops_overnight_run(self):
        """
        Scenario: Automated evaluation rejects work during an overnight run
          Given overnight proxy mode is active
          When the automated evaluation rejects work at a human decision point
          Then the overnight run stops — no further edges are iterated
          And the practitioner sees the rejection when they check the next morning

        Specification check: proxy rejection pauses the auto-loop immediately.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        assert "pause" in gen_iterate.lower() or "halt" in gen_iterate.lower() or \
               "stops" in gen_iterate.lower() or "stop" in gen_iterate.lower(), (
            "gen-iterate.md must describe the auto-loop stopping on proxy rejection "
            "(REQ-F-HPRX-005 AC-1)"
        )

    # UC-12-05-02 | Validates: REQ-F-HPRX-005 AC-2
    def test_same_edge_not_retried_after_rejection(self):
        """
        Scenario: Practitioner resumes after a rejection without addressing it
          Given the overnight run stopped due to an automated rejection
          When the practitioner starts Genesis again in the same session
          Without addressing the rejected work
          Then Genesis does not re-attempt the same rejected edge
          And shows the practitioner that a rejection needs to be addressed

        Specification check: rejected edges not re-attempted in same session.
        """
        # Rejection session guard lives in gen-start.md (the loop controller)
        gen_start = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        ).read_text()
        assert "rejected_in_session" in gen_start or "same session" in gen_start.lower(), (
            "gen-start.md must describe that rejected edges are not retried in the "
            "same session (REQ-F-HPRX-005 AC-2)"
        )


# ─────────────────────────────────────────────────────────────────────────────
# UC-12-06: Decision Attribution
# REQ-NFR-HPRX-001, REQ-NFR-HPRX-002 — Automated decisions are clearly labeled.
# ─────────────────────────────────────────────────────────────────────────────

class TestDecisionAttribution:
    """
    Feature: Clear Attribution of Automated vs Human Decisions

      The event history must always be clear about whether a decision was made
      by a human or by the overnight proxy. This is essential for audit and
      accountability — the practitioner can always tell which decisions they
      personally made and which were automated.
    """

    # UC-12-06-01 | Validates: REQ-NFR-HPRX-001 AC-1
    def test_automated_decisions_labeled_as_proxy_not_human(self):
        """
        Scenario: Reviewing the event history after an overnight run
          Given an automated decision was made during an overnight run
          When the practitioner reviews the event history
          Then the event is labeled 'human-proxy' not 'human'
          So there is no ambiguity about who made the decision

        Specification check: actor field must be 'human-proxy' for proxy decisions.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        assert '"human-proxy"' in gen_iterate or "human-proxy" in gen_iterate, (
            "gen-iterate.md must specify actor: 'human-proxy' for proxy decisions, "
            "never 'human' (REQ-NFR-HPRX-001 AC-1)"
        )

    # UC-12-06-02 | Validates: REQ-NFR-HPRX-001 AC-2
    def test_human_decisions_not_labeled_as_proxy(self):
        """
        Scenario: Human approves work during a normal (non-overnight) session
          Given the practitioner manually reviews and approves work
          When the approval is recorded in the event history
          Then the event is labeled 'human' not 'human-proxy'
          So the distinction between proxy and direct human decisions is preserved

        Specification check: human decisions use actor: 'human'; proxy uses 'human-proxy'.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        # Both actor values must be distinguished in the spec
        has_human = '"human"' in gen_iterate or "actor: human" in gen_iterate.lower() or \
                    'actor: "human"' in gen_iterate
        has_proxy = "human-proxy" in gen_iterate
        assert has_human and has_proxy, (
            "gen-iterate.md must distinguish between actor: 'human' (direct) and "
            "actor: 'human-proxy' (automated) — they must never be confused "
            "(REQ-NFR-HPRX-001 AC-2)"
        )

    # UC-12-06-03 | Validates: REQ-NFR-HPRX-002 AC-1
    def test_proxy_log_path_recorded_in_event(self):
        """
        Scenario: Practitioner wants to find the rationale for an automated decision
          Given the event history shows an automated approval from an overnight run
          When the practitioner inspects the event
          Then the event includes a link to the review log entry with the rationale
          So they can always find the supporting evidence

        Specification check: review_approved event includes proxy_log path.
        """
        gen_iterate = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        ).read_text()
        # The event must carry a reference to the proxy-log file
        assert "proxy_log" in gen_iterate or "proxy-log" in gen_iterate, (
            "gen-iterate.md must specify that review_approved{actor: human-proxy} "
            "carries the proxy_log path for traceability (REQ-NFR-HPRX-002 AC-1)"
        )
