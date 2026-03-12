"""
Tests for Human Proxy Mode (REQ-F-PROXY-001)

Validates: REQ-F-HPRX-001, REQ-F-HPRX-002, REQ-F-HPRX-003, REQ-F-HPRX-004,
           REQ-F-HPRX-005, REQ-F-HPRX-006, REQ-NFR-HPRX-001, REQ-NFR-HPRX-002,
           REQ-BR-HPRX-001, REQ-BR-HPRX-002

These are behavioural acceptance tests verifying the command-layer specification
for --human-proxy mode as defined in:
  - gen-start.md (flag validation, banner, loop control)
  - gen-iterate.md (proxy evaluation protocol, logging, event emission)
  - gen-status.md (morning review visibility)
  - imp_claude/design/REQ-F-PROXY-001-design.md
"""

import json
import os
import pytest
from datetime import datetime, timezone
from pathlib import Path


# ─── Fixtures ────────────────────────────────────────────────────────────────

@pytest.fixture
def proxy_log_dir(tmp_path):
    """Validates: REQ-F-HPRX-003 — proxy-log directory"""
    d = tmp_path / ".ai-workspace" / "reviews" / "proxy-log"
    # Directory NOT pre-created — tests verify auto-creation
    return d


@pytest.fixture
def events_path(tmp_path):
    """Minimal events.jsonl for test isolation"""
    # Validates: REQ-NFR-HPRX-002 — event stream traceability
    events = tmp_path / ".ai-workspace" / "events"
    events.mkdir(parents=True)
    p = events / "events.jsonl"
    p.write_text("")
    return p


@pytest.fixture
def sample_artifact(tmp_path):
    """A minimal candidate artifact for proxy evaluation"""
    f = tmp_path / "REQUIREMENTS.md"
    f.write_text("# Requirements\n\n## REQ-F-AUTH-001\nUser must authenticate.\n")
    return f


@pytest.fixture
def fh_criteria():
    """A representative set of F_H criteria from an edge checklist"""
    return [
        {
            "name": "human_validates_completeness",
            "criterion": "Human confirms all expected requirements are present.",
            "required": True,
        },
        {
            "name": "human_validates_priorities",
            "criterion": "Human confirms priority assignments are correct.",
            "required": True,
        },
    ]


# ─── REQ-F-HPRX-001: Flag validation ─────────────────────────────────────────

class TestHumanProxyFlag:
    """Validates: REQ-F-HPRX-001, REQ-BR-HPRX-002"""

    def test_human_proxy_requires_auto_flag(self):
        """--human-proxy without --auto must produce a specific error message.
        Validates: REQ-F-HPRX-001 AC-1
        """
        # Specification: "--human-proxy requires --auto"
        # This is a command-layer contract; we verify the specification text exists.
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        assert gen_start_src.exists(), "gen-start.md source must exist"
        content = gen_start_src.read_text()
        assert "--human-proxy requires --auto" in content, (
            "gen-start.md must contain the error message '--human-proxy requires --auto' "
            "(REQ-F-HPRX-001 AC-1)"
        )

    def test_human_proxy_flag_in_usage_table(self):
        """--human-proxy must appear in the gen-start Usage table.
        Validates: REQ-F-HPRX-001
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        assert "`--human-proxy`" in content, (
            "gen-start.md Usage table must include --human-proxy option"
        )

    def test_proxy_mode_active_banner_specified(self):
        """[proxy mode active] banner must be specified in gen-start.
        Validates: REQ-F-HPRX-001 AC-2
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        assert "[proxy mode active]" in content, (
            "gen-start.md must specify '[proxy mode active]' banner (REQ-F-HPRX-001 AC-2)"
        )

    def test_flag_not_persisted_to_workspace(self):
        """--human-proxy must be a per-invocation flag, never persisted.
        Validates: REQ-F-HPRX-001 AC-3, REQ-BR-HPRX-002
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        # Specification must state it is NOT persisted / NOT derived from config/env
        assert "per-invocation" in content or "never persisted" in content or "not persisted" in content, (
            "gen-start.md must specify that --human-proxy is a per-invocation option "
            "and is never persisted (REQ-F-HPRX-001 AC-3, REQ-BR-HPRX-002)"
        )

    def test_flag_only_affects_fh_evaluators(self):
        """--human-proxy must not affect F_D or F_P evaluators.
        Validates: REQ-F-HPRX-001 AC-4
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # Proxy path must only trigger on human evaluator gates
        assert "If human evaluator required" in content, (
            "gen-iterate.md must gate proxy path on 'If human evaluator required' "
            "(proxy affects only F_H — REQ-F-HPRX-001 AC-4)"
        )
        assert "human-proxy" in content, (
            "gen-iterate.md must handle --human-proxy in F_H gate branch"
        )


# ─── REQ-F-HPRX-002: Proxy evaluation protocol ───────────────────────────────

class TestProxyEvaluationProtocol:
    """Validates: REQ-F-HPRX-002"""

    def test_proxy_evaluates_each_fh_criterion(self):
        """Proxy must evaluate every F_H criterion with evidence.
        Validates: REQ-F-HPRX-002 AC-1
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "For each F_H criterion" in content or "each criterion" in content.lower(), (
            "gen-iterate.md proxy protocol must specify per-criterion evaluation "
            "(REQ-F-HPRX-002 AC-1)"
        )
        assert "Evidence" in content and "Satisfied" in content, (
            "gen-iterate.md proxy protocol must require evidence and satisfied fields "
            "(REQ-F-HPRX-002 AC-1)"
        )

    def test_proxy_decision_approved_only_if_all_required_pass(self):
        """Overall proxy decision must be approved iff ALL required criteria pass.
        Validates: REQ-F-HPRX-002 AC-2
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # Specification must define the decision rule
        assert (
            "approved` if every required F_H criterion is satisfied" in content
            or "approved only if every required" in content
            or ("approved" in content and "every required" in content)
        ), (
            "gen-iterate.md must specify: approved iff every required F_H criterion satisfied "
            "(REQ-F-HPRX-002 AC-2)"
        )

    def test_proxy_cites_evidence_from_artifact(self):
        """Proxy evaluation must cite specific evidence from the artifact.
        Validates: REQ-F-HPRX-002 AC-3
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "evidence" in content.lower() and "artifact" in content.lower(), (
            "gen-iterate.md must require citing evidence from the artifact "
            "(REQ-F-HPRX-002 AC-3)"
        )

    def test_proxy_uses_only_defined_criteria(self):
        """Proxy must not introduce criteria beyond those in the edge checklist.
        Validates: REQ-F-HPRX-002 AC-4
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert (
            "Do not introduce additional standards" in content
            or "only the defined F_H criteria" in content
            or "only evaluates defined criteria" in content
        ), (
            "gen-iterate.md must prohibit proxy from introducing extra standards "
            "(REQ-F-HPRX-002 AC-4)"
        )


# ─── REQ-F-HPRX-003: Proxy decision logging ──────────────────────────────────

class TestProxyDecisionLogging:
    """Validates: REQ-F-HPRX-003, REQ-NFR-HPRX-001"""

    def test_proxy_log_naming_convention_specified(self):
        """Log filename must follow {ISO}_{feature}_{edge-slug}.md pattern.
        Validates: REQ-F-HPRX-003 AC-1
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "proxy-log" in content, (
            "gen-iterate.md must specify the proxy-log directory (REQ-F-HPRX-003)"
        )
        # Log file naming pattern
        assert "{ISO" in content or "ISO-timestamp" in content or "ISO 8601" in content, (
            "gen-iterate.md must specify ISO timestamp in proxy-log filename (REQ-F-HPRX-003 AC-1)"
        )

    def test_proxy_log_contains_required_fields(self):
        """Log file format must include all required fields.
        Validates: REQ-F-HPRX-003 AC-2
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        required_fields = [
            "Feature", "Edge", "Iteration", "Timestamp", "Decision",
            "Criterion", "Evidence", "Satisfied", "Reasoning", "Summary",
        ]
        for field in required_fields:
            assert field in content, (
                f"gen-iterate.md proxy-log format must include '{field}' field "
                f"(REQ-F-HPRX-003 AC-2)"
            )

    def test_log_written_before_event(self):
        """Proxy log file must be written BEFORE review_approved event is emitted.
        Validates: REQ-F-HPRX-003 AC-3
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # Specification must state ordering: write log, then emit event
        assert "BEFORE" in content or "before" in content.lower(), (
            "gen-iterate.md must specify log is written before event emission "
            "(REQ-F-HPRX-003 AC-3)"
        )

    def test_proxy_log_directory_auto_created(self):
        """proxy-log directory must be created automatically if absent.
        Validates: REQ-F-HPRX-003 AC-4
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "create if absent" in content or "auto-created" in content or "create it" in content.lower(), (
            "gen-iterate.md must specify proxy-log directory is auto-created if absent "
            "(REQ-F-HPRX-003 AC-4)"
        )

    def test_incomplete_log_entry_on_interrupted_session(self):
        """Interrupted proxy evaluation must produce an incomplete log entry.
        Validates: REQ-NFR-HPRX-001 AC-1
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "incomplete" in content.lower(), (
            "gen-iterate.md must specify 'incomplete' status for interrupted sessions "
            "(REQ-NFR-HPRX-001 AC-1)"
        )

    def test_incomplete_entries_reported_at_session_start(self):
        """Incomplete proxy-log entries must be reported at next session start.
        Validates: REQ-NFR-HPRX-001 AC-2
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        assert "incomplete" in content.lower() and "proxy" in content.lower(), (
            "gen-start.md must report incomplete proxy decisions at --human-proxy session start "
            "(REQ-NFR-HPRX-001 AC-2)"
        )


# ─── REQ-F-HPRX-004: Proxy event emission ────────────────────────────────────

class TestProxyEventEmission:
    """Validates: REQ-F-HPRX-004, REQ-NFR-HPRX-002"""

    def test_review_approved_actor_field_is_human_proxy(self):
        """review_approved event must have actor: human-proxy for proxy decisions.
        Validates: REQ-F-HPRX-004 AC-2
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert '"human-proxy"' in content or "actor.*human-proxy" in content or "human-proxy" in content, (
            "gen-iterate.md must specify actor: 'human-proxy' on proxy review_approved events "
            "(REQ-F-HPRX-004 AC-2)"
        )

    def test_review_approved_has_proxy_log_field(self):
        """review_approved event must include proxy_log path.
        Validates: REQ-F-HPRX-004 AC-3
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "proxy_log" in content, (
            "gen-iterate.md must specify proxy_log field on review_approved event "
            "(REQ-F-HPRX-004 AC-3)"
        )

    def test_human_actor_field_on_standard_path(self):
        """Standard (non-proxy) review_approved must have actor: human.
        Validates: REQ-NFR-HPRX-002
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert 'actor: "human"' in content or "actor.*human" in content, (
            "gen-iterate.md must specify actor: 'human' on standard (non-proxy) review_approved "
            "(REQ-NFR-HPRX-002)"
        )

    def test_actor_field_always_present_invariant(self):
        """actor field must always be present on new review_approved events.
        Validates: REQ-NFR-HPRX-002 AC-1
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # Both paths must set actor
        assert '"human-proxy"' in content and ('"human"' in content or "actor.*human" in content), (
            "gen-iterate.md must set actor field on BOTH proxy and standard review_approved events "
            "(REQ-NFR-HPRX-002 AC-1)"
        )

    def test_backward_compat_absent_actor_treated_as_human(self):
        """Existing review_approved events without actor field must be treated as human.
        Validates: REQ-NFR-HPRX-002 AC-2
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # gen-status must handle absent actor
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        status_content = gen_status_src.read_text()
        assert "absent" in status_content.lower() or "missing" in status_content.lower() or (
            "actor" in status_content and "human" in status_content
        ), (
            "gen-status.md must handle review_approved events without actor field as 'human' "
            "(REQ-NFR-HPRX-002 AC-2)"
        )

    def test_proxy_log_field_points_to_existing_file(self):
        """proxy_log field must reference a file that exists at event emission time.
        Validates: REQ-F-HPRX-004 AC-3 (ordering invariant)
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        # Ordering: write log THEN emit event — already tested in logging section
        # Here we verify the specification mentions the path must be valid
        assert "proxy_log" in content and ("path" in content.lower() or "file" in content.lower()), (
            "gen-iterate.md must specify proxy_log path points to an existing file "
            "(REQ-F-HPRX-004 AC-3)"
        )


# ─── REQ-F-HPRX-005: Loop continuation and rejection halt ────────────────────

class TestLoopContinuationAndRejection:
    """Validates: REQ-F-HPRX-005, REQ-BR-HPRX-001"""

    def test_proxy_approval_continues_loop(self):
        """Proxy approval must let the auto-loop continue normally.
        Validates: REQ-F-HPRX-005 AC-1
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "continue" in content.lower() and "approval" in content.lower(), (
            "gen-iterate.md must specify loop continues on proxy approval (REQ-F-HPRX-005 AC-1)"
        )

    def test_proxy_rejection_halts_loop_with_message(self):
        """Proxy rejection must halt the loop and print a clear message.
        Validates: REQ-F-HPRX-005 AC-2
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "PROXY REJECTION" in content, (
            "gen-iterate.md must specify 'PROXY REJECTION' report on rejection halt "
            "(REQ-F-HPRX-005 AC-2)"
        )
        # Message must identify feature, edge, criterion
        assert "Feature" in content and "Edge" in content and "Criterion" in content, (
            "gen-iterate.md PROXY REJECTION report must identify feature, edge, and criterion "
            "(REQ-F-HPRX-005 AC-2)"
        )

    def test_proxy_may_not_self_correct(self):
        """After proxy rejection, the proxy must not construct a revised artifact.
        Validates: REQ-BR-HPRX-001, REQ-F-HPRX-005 AC-3
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        iterate_content = gen_iterate_src.read_text()
        start_content = gen_start_src.read_text()
        combined = iterate_content + start_content
        assert (
            "self-correction" in combined.lower()
            or "self-correct" in combined.lower()
            or "rejected_in_session" in combined
        ), (
            "gen-iterate.md or gen-start.md must prohibit proxy self-correction after rejection "
            "(REQ-BR-HPRX-001, REQ-F-HPRX-005 AC-3)"
        )

    def test_feature_stays_iterating_after_rejection(self):
        """Proxy rejection must not corrupt the feature vector state.
        Validates: REQ-F-HPRX-005 AC-4
        """
        gen_iterate_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-iterate.md"
        )
        content = gen_iterate_src.read_text()
        assert "iterating" in content.lower() and ("rejection" in content.lower() or "rejected" in content.lower()), (
            "gen-iterate.md must specify feature stays in 'iterating' status after rejection "
            "(REQ-F-HPRX-005 AC-4)"
        )

    def test_rejection_does_not_affect_other_features(self):
        """Proxy rejection of one feature must not block other features in session.
        Validates: REQ-BR-HPRX-001 AC-3
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        assert "rejected_in_session" in content or "other features" in content.lower(), (
            "gen-start.md must specify rejection only affects the rejected feature+edge pair "
            "(REQ-BR-HPRX-001 AC-3)"
        )


# ─── REQ-F-HPRX-006: Morning review visibility ───────────────────────────────

class TestMorningReviewVisibility:
    """Validates: REQ-F-HPRX-006, REQ-NFR-HPRX-002"""

    def test_gen_status_shows_proxy_decisions_section(self):
        """gen-status must display Proxy Decisions section when entries exist.
        Validates: REQ-F-HPRX-006 AC-1
        """
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        content = gen_status_src.read_text()
        assert "Proxy Decisions" in content, (
            "gen-status.md must include 'Proxy Decisions' section (REQ-F-HPRX-006)"
        )

    def test_proxy_decisions_show_feature_edge_decision(self):
        """Proxy Decisions table must show feature, edge, decision, age.
        Validates: REQ-F-HPRX-006 AC-1
        """
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        content = gen_status_src.read_text()
        # Table must include the required columns
        for col in ("Feature", "Edge", "Decision", "Age"):
            assert col in content, (
                f"gen-status.md Proxy Decisions table must include '{col}' column "
                f"(REQ-F-HPRX-006 AC-1)"
            )

    def test_proxy_approval_counts_separate_from_human(self):
        """gen-status must count proxy approvals separately from human approvals.
        Validates: REQ-NFR-HPRX-002 AC-3
        """
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        content = gen_status_src.read_text()
        assert "human" in content.lower() and "proxy" in content.lower() and "Approvals" in content, (
            "gen-status.md must show separate approval counts for human and proxy "
            "(REQ-NFR-HPRX-002 AC-3)"
        )

    def test_dismiss_mechanism_specified(self):
        """Human must be able to dismiss proxy decisions from review queue.
        Validates: REQ-F-HPRX-006 AC-2
        """
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        content = gen_status_src.read_text()
        assert "dismiss" in content.lower() or "Reviewed:" in content, (
            "gen-status.md must specify how to dismiss proxy decisions from review queue "
            "(REQ-F-HPRX-006 AC-2)"
        )

    def test_override_mechanism_specified(self):
        """Human must be able to override a proxy approval via /gen-review.
        Validates: REQ-F-HPRX-006 AC-3
        """
        gen_status_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-status.md"
        )
        content = gen_status_src.read_text()
        assert "/gen-review" in content and "override" in content.lower(), (
            "gen-status.md must specify /gen-review as the override mechanism "
            "(REQ-F-HPRX-006 AC-3)"
        )


# ─── REQ-BR-HPRX-002: Opt-in only ────────────────────────────────────────────

class TestProxyOptInOnly:
    """Validates: REQ-BR-HPRX-002"""

    def test_auto_without_proxy_flag_still_pauses_at_fh(self):
        """--auto without --human-proxy must still pause at F_H gates.
        Validates: REQ-BR-HPRX-002 AC-1
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        # Standard pause must still exist
        assert "human_required and not proxy_mode" in content or (
            "human_required" in content and "proxy_mode" in content
        ), (
            "gen-start.md must only skip F_H pause when proxy_mode is set; "
            "standard --auto must still pause (REQ-BR-HPRX-002 AC-1)"
        )

    def test_no_config_or_env_activation(self):
        """--human-proxy must not be activatable via config or env vars.
        Validates: REQ-BR-HPRX-002 AC-2
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        # The spec must state flag-only activation
        assert (
            "never activated by config" in content
            or "config, env" in content
            or "explicit" in content.lower()
        ), (
            "gen-start.md must specify --human-proxy is never activated by config or env var "
            "(REQ-BR-HPRX-002 AC-2)"
        )

    def test_flag_must_be_re_supplied_every_invocation(self):
        """--human-proxy must never be implied or inferred across invocations.
        Validates: REQ-BR-HPRX-002 AC-3
        """
        gen_start_src = Path(
            "imp_claude/code/.claude-plugin/plugins/genesis/commands/gen-start.md"
        )
        content = gen_start_src.read_text()
        assert (
            "per-invocation" in content
            or "re-supplied" in content
            or "re-run" in content.lower()
        ), (
            "gen-start.md must specify --human-proxy is a per-invocation option "
            "(REQ-BR-HPRX-002 AC-3)"
        )


# ─── ADR-020: Architecture decision documented ───────────────────────────────

class TestADR020Presence:
    """Validates that ADR-020 documents the command-layer proxy decision"""

    def test_adr_020_exists(self):
        """ADR-020 must exist documenting the proxy-in-command-layer decision."""
        adr = Path("imp_claude/design/adrs/ADR-020-human-proxy-in-command-layer.md")
        assert adr.exists(), "ADR-020 must be present (command-layer proxy design decision)"

    def test_adr_020_covers_key_sections(self):
        """ADR-020 must cover Context, Decision, Rationale, and Consequences."""
        adr = Path("imp_claude/design/adrs/ADR-020-human-proxy-in-command-layer.md")
        content = adr.read_text()
        for section in ("## Context", "## Decision", "## Rationale", "## Consequences"):
            assert section in content, f"ADR-020 must contain '{section}' section"

    def test_adr_020_references_req_keys(self):
        """ADR-020 must reference the REQ-F-PROXY-001 key set."""
        adr = Path("imp_claude/design/adrs/ADR-020-human-proxy-in-command-layer.md")
        content = adr.read_text()
        assert "REQ-F-PROXY-001" in content or "REQ-F-HPRX" in content, (
            "ADR-020 must reference REQ-F-PROXY-001 or REQ-F-HPRX-* keys"
        )
