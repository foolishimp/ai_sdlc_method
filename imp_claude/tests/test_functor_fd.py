# Validates: REQ-ITER-003, REQ-EVAL-002, REQ-SENSE-001, REQ-SUPV-003
"""Tests for F_D functor modules — evaluate, emit, classify, sense, route, dispatch."""

import json
import pathlib
import sys
import textwrap

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "code"))

from genisis.models import (
    Category,
    CheckOutcome,
    CheckResult,
    EvaluationResult,
    Event,
    FunctionalUnit,
    ResolvedCheck,
)
from genisis.fd_evaluate import evaluate_checklist, run_check
from genisis.fd_emit import emit_event, make_event
from genisis.fd_classify import (
    classify_req_tag,
    classify_signal_source,
    classify_source_finding,
)
from genisis.fd_sense import (
    sense_event_freshness,
    sense_event_log_integrity,
    sense_feature_stall,
    sense_req_tag_coverage,
)
from genisis.fd_route import lookup_encoding, select_next_edge, select_profile
from genisis.dispatch import dispatch, lookup_and_dispatch


# ═══════════════════════════════════════════════════════════════════════════
# F_D EVALUATE
# ═══════════════════════════════════════════════════════════════════════════

class TestRunCheck:

    def test_passing_command(self, tmp_path):
        check = ResolvedCheck(
            name="echo_test",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="exits 0",
            source="default",
            required=True,
            command="echo hello",
            pass_criterion="exit code 0",
        )
        result = run_check(check, tmp_path)
        assert result.outcome == CheckOutcome.PASS
        assert result.exit_code == 0
        assert "hello" in result.stdout

    def test_failing_command(self, tmp_path):
        check = ResolvedCheck(
            name="fail_test",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="fails",
            source="default",
            required=True,
            command="exit 1",
            pass_criterion="exit code 0",
        )
        result = run_check(check, tmp_path)
        assert result.outcome == CheckOutcome.FAIL
        assert result.exit_code == 1

    def test_skip_agent_check(self, tmp_path):
        check = ResolvedCheck(
            name="agent_check",
            check_type="agent",
            functional_unit="evaluate",
            criterion="LLM judges",
            source="default",
            required=True,
        )
        result = run_check(check, tmp_path)
        assert result.outcome == CheckOutcome.SKIP

    def test_skip_unresolved_vars(self, tmp_path):
        check = ResolvedCheck(
            name="unresolved",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="check",
            source="default",
            required=True,
            command="$tools.missing.command",
            unresolved=["tools.missing.command"],
        )
        result = run_check(check, tmp_path)
        assert result.outcome == CheckOutcome.SKIP
        assert "unresolved" in result.message.lower()

    def test_skip_no_command(self, tmp_path):
        check = ResolvedCheck(
            name="no_cmd",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="check",
            source="default",
            required=True,
        )
        result = run_check(check, tmp_path)
        assert result.outcome == CheckOutcome.SKIP

    def test_timeout(self, tmp_path):
        check = ResolvedCheck(
            name="slow",
            check_type="deterministic",
            functional_unit="evaluate",
            criterion="fast",
            source="default",
            required=True,
            command="sleep 10",
            pass_criterion="exit code 0",
        )
        result = run_check(check, tmp_path, timeout=1)
        assert result.outcome == CheckOutcome.ERROR
        assert "timeout" in result.message.lower()


class TestEvaluateChecklist:

    def test_all_pass(self, tmp_path):
        checks = [
            ResolvedCheck(
                name="c1", check_type="deterministic", functional_unit="evaluate",
                criterion="ok", source="default", required=True,
                command="echo pass", pass_criterion="exit code 0",
            ),
            ResolvedCheck(
                name="c2", check_type="deterministic", functional_unit="evaluate",
                criterion="ok", source="default", required=True,
                command="true", pass_criterion="exit code 0",
            ),
        ]
        result = evaluate_checklist(checks, tmp_path, edge="test_edge")
        assert result.converged is True
        assert result.delta == 0
        assert result.edge == "test_edge"

    def test_one_fails_delta_nonzero(self, tmp_path):
        checks = [
            ResolvedCheck(
                name="pass_check", check_type="deterministic", functional_unit="evaluate",
                criterion="ok", source="default", required=True,
                command="true", pass_criterion="exit code 0",
            ),
            ResolvedCheck(
                name="fail_check", check_type="deterministic", functional_unit="evaluate",
                criterion="fail", source="default", required=True,
                command="false", pass_criterion="exit code 0",
            ),
        ]
        result = evaluate_checklist(checks, tmp_path)
        assert result.converged is False
        assert result.delta == 1
        assert len(result.escalations) == 1
        assert "fail_check" in result.escalations[0]

    def test_non_required_fail_no_delta(self, tmp_path):
        checks = [
            ResolvedCheck(
                name="advisory", check_type="deterministic", functional_unit="evaluate",
                criterion="advisory", source="default", required=False,
                command="false", pass_criterion="exit code 0",
            ),
        ]
        result = evaluate_checklist(checks, tmp_path)
        assert result.converged is True
        assert result.delta == 0

    def test_agent_checks_skipped(self, tmp_path):
        checks = [
            ResolvedCheck(
                name="agent_check", check_type="agent", functional_unit="evaluate",
                criterion="LLM check", source="default", required=True,
            ),
        ]
        result = evaluate_checklist(checks, tmp_path)
        # Agent checks are skipped, not counted as failures
        assert result.delta == 0


# ═══════════════════════════════════════════════════════════════════════════
# F_D EMIT
# ═══════════════════════════════════════════════════════════════════════════

class TestEmit:

    def test_make_event(self):
        event = make_event("test_event", "my_project", feature="REQ-F-001")
        assert event.event_type == "test_event"
        assert event.project == "my_project"
        assert "feature" in event.data
        assert event.timestamp  # non-empty

    def test_emit_creates_file(self, tmp_path):
        events_path = tmp_path / "events" / "events.jsonl"
        event = make_event("test_event", "proj")
        emit_event(events_path, event)
        assert events_path.exists()
        line = events_path.read_text().strip()
        parsed = json.loads(line)
        assert parsed["event_type"] == "test_event"
        assert parsed["project"] == "proj"

    def test_emit_appends(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        emit_event(events_path, make_event("e1", "p"))
        emit_event(events_path, make_event("e2", "p"))
        lines = events_path.read_text().strip().split("\n")
        assert len(lines) == 2
        assert json.loads(lines[0])["event_type"] == "e1"
        assert json.loads(lines[1])["event_type"] == "e2"

    def test_emit_validates_required_fields(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        with pytest.raises(ValueError, match="event_type"):
            emit_event(events_path, Event("", "2026-01-01", "proj"))
        with pytest.raises(ValueError, match="project"):
            emit_event(events_path, Event("evt", "2026-01-01", ""))

    def test_emit_extra_data(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        event = make_event("iteration_completed", "proj", delta=3, edge="code↔unit_tests")
        emit_event(events_path, event)
        parsed = json.loads(events_path.read_text().strip())
        assert parsed["delta"] == 3
        assert parsed["edge"] == "code↔unit_tests"


# ═══════════════════════════════════════════════════════════════════════════
# F_D CLASSIFY
# ═══════════════════════════════════════════════════════════════════════════

class TestClassifyReqTag:

    def test_valid_implements(self):
        r = classify_req_tag("Implements: REQ-ITER-003")
        assert r.classification == "VALID"

    def test_valid_validates(self):
        r = classify_req_tag("Validates: REQ-EVAL-002")
        assert r.classification == "VALID"

    def test_valid_in_context(self):
        r = classify_req_tag("# Implements: REQ-F-AUTH-001 — login flow")
        assert r.classification == "VALID"

    def test_invalid_format_bare_key(self):
        r = classify_req_tag("REQ-F-AUTH-001")
        assert r.classification == "INVALID_FORMAT"

    def test_missing_no_tag(self):
        r = classify_req_tag("just some code")
        assert r.classification == "MISSING"

    def test_missing_empty(self):
        r = classify_req_tag("")
        assert r.classification == "MISSING"


class TestClassifySourceFinding:

    def test_ambiguity(self):
        r = classify_source_finding("The error handling strategy is unclear")
        assert r.classification == "SOURCE_AMBIGUITY"

    def test_gap(self):
        r = classify_source_finding("Configuration loading is missing from the design")
        assert r.classification == "SOURCE_GAP"

    def test_underspec(self):
        r = classify_source_finding("The concurrency model is underspecified")
        assert r.classification == "SOURCE_UNDERSPEC"

    def test_unclassified(self):
        r = classify_source_finding("The code uses Python 3.12")
        assert r.classification == "UNCLASSIFIED"


class TestClassifySignalSource:

    def test_iteration(self):
        assert classify_signal_source({"event_type": "iteration_completed"}) == "iteration"

    def test_convergence(self):
        assert classify_signal_source({"event_type": "edge_converged"}) == "convergence"

    def test_intent_raised_with_source(self):
        assert classify_signal_source({
            "event_type": "intent_raised",
            "data": {"signal_source": "test_failure"},
        }) == "test_failure"

    def test_unknown_event(self):
        assert classify_signal_source({"event_type": "something_new"}) == "unknown"


# ═══════════════════════════════════════════════════════════════════════════
# F_D SENSE
# ═══════════════════════════════════════════════════════════════════════════

class TestSenseEventFreshness:

    def test_fresh_event(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        from genisis.fd_emit import make_event as mk
        event = mk("test", "proj")
        events_path.write_text(json.dumps({
            "event_type": "test",
            "timestamp": event.timestamp,
            "project": "proj",
        }) + "\n")
        result = sense_event_freshness(events_path, threshold_minutes=60)
        assert result.breached is False
        assert result.value < 1.0  # less than 1 minute old

    def test_missing_file(self, tmp_path):
        result = sense_event_freshness(tmp_path / "nope.jsonl")
        assert result.breached is True

    def test_empty_file(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        events_path.write_text("")
        result = sense_event_freshness(events_path)
        assert result.breached is True


class TestSenseFeatureStall:

    def test_no_stall(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        lines = []
        for delta in [5, 3, 1]:
            lines.append(json.dumps({
                "event_type": "iteration_completed",
                "timestamp": "2026-01-01T00:00:00Z",
                "project": "p",
                "feature": "REQ-F-001",
                "delta": delta,
            }))
        events_path.write_text("\n".join(lines) + "\n")
        result = sense_feature_stall(events_path, "REQ-F-001", threshold_iterations=3)
        assert result.breached is False

    def test_stalled(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        lines = []
        for _ in range(4):
            lines.append(json.dumps({
                "event_type": "iteration_completed",
                "timestamp": "2026-01-01T00:00:00Z",
                "project": "p",
                "feature": "REQ-F-001",
                "delta": 3,
            }))
        events_path.write_text("\n".join(lines) + "\n")
        result = sense_feature_stall(events_path, "REQ-F-001", threshold_iterations=3)
        assert result.breached is True

    def test_converged_not_stalled(self, tmp_path):
        """Delta of 0 repeated is not a stall — it's convergence."""
        events_path = tmp_path / "events.jsonl"
        lines = []
        for _ in range(3):
            lines.append(json.dumps({
                "event_type": "iteration_completed",
                "timestamp": "2026-01-01T00:00:00Z",
                "project": "p",
                "feature": "REQ-F-001",
                "delta": 0,
            }))
        events_path.write_text("\n".join(lines) + "\n")
        result = sense_feature_stall(events_path, "REQ-F-001", threshold_iterations=3)
        assert result.breached is False  # delta 0 means converged, not stuck


class TestSenseReqTagCoverage:

    def test_full_coverage(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.py").write_text("# Implements: REQ-F-AUTH-001\nclass Auth: pass\n")
        result = sense_req_tag_coverage(src, {"REQ-F-AUTH-001"})
        assert result.value == 1.0
        assert result.breached is False

    def test_partial_coverage(self, tmp_path):
        src = tmp_path / "src"
        src.mkdir()
        (src / "auth.py").write_text("# Implements: REQ-F-AUTH-001\n")
        result = sense_req_tag_coverage(src, {"REQ-F-AUTH-001", "REQ-F-DB-001"})
        assert result.value == 0.5
        assert result.breached is True
        assert "REQ-F-DB-001" in result.detail

    def test_no_source_dir(self, tmp_path):
        result = sense_req_tag_coverage(tmp_path / "nonexistent", {"REQ-F-001"})
        assert result.breached is True

    def test_empty_req_keys(self, tmp_path):
        result = sense_req_tag_coverage(tmp_path, set())
        assert result.breached is False


class TestSenseEventLogIntegrity:

    def test_valid_log(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        events_path.write_text(
            json.dumps({"event_type": "e", "timestamp": "t", "project": "p"}) + "\n"
        )
        result = sense_event_log_integrity(events_path)
        assert result.breached is False
        assert result.value == 1

    def test_invalid_json(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        events_path.write_text("not json\n")
        result = sense_event_log_integrity(events_path)
        assert result.breached is True

    def test_missing_fields(self, tmp_path):
        events_path = tmp_path / "events.jsonl"
        events_path.write_text(json.dumps({"event_type": "e"}) + "\n")
        result = sense_event_log_integrity(events_path)
        assert result.breached is True

    def test_missing_file(self, tmp_path):
        result = sense_event_log_integrity(tmp_path / "nope.jsonl")
        assert result.breached is True


# ═══════════════════════════════════════════════════════════════════════════
# F_D ROUTE
# ═══════════════════════════════════════════════════════════════════════════

class TestLookupEncoding:

    def test_standard_profile(self):
        profile = {
            "encoding": {
                "functional_units": {
                    "evaluate": "F_D",
                    "construct": "F_P",
                    "emit": "F_D",
                }
            }
        }
        assert lookup_encoding(profile, "evaluate") == Category.F_D
        assert lookup_encoding(profile, "construct") == Category.F_P

    def test_missing_unit_raises(self):
        profile = {"encoding": {"functional_units": {}}}
        with pytest.raises(KeyError):
            lookup_encoding(profile, "evaluate")


class TestSelectProfile:

    def test_feature_maps_to_standard(self, tmp_path):
        (tmp_path / "standard.yml").write_text("profile: standard\n")
        assert select_profile("feature", tmp_path) == "standard"

    def test_spike_maps_to_spike(self, tmp_path):
        (tmp_path / "spike.yml").write_text("profile: spike\n")
        assert select_profile("spike", tmp_path) == "spike"

    def test_unknown_falls_back_to_standard(self, tmp_path):
        (tmp_path / "standard.yml").write_text("profile: standard\n")
        assert select_profile("exotic", tmp_path) == "standard"

    def test_missing_profile_file_falls_back(self, tmp_path):
        (tmp_path / "standard.yml").write_text("profile: standard\n")
        assert select_profile("hotfix", tmp_path) == "standard"


class TestSelectNextEdge:

    def test_first_unconverged(self):
        profile = {
            "profile": "standard",
            "graph": {
                "include": ["intent→requirements", "requirements→design", "design→code"],
                "optional": [],
            },
        }
        trajectory = {
            "trajectory": {
                "intent_requirements": {"status": "converged"},
                "requirements_design": {"status": "iterating"},
            }
        }
        result = select_next_edge(trajectory, {}, profile)
        assert result.selected_edge == "requirements→design"

    def test_all_converged(self):
        profile = {
            "profile": "standard",
            "graph": {
                "include": ["intent→requirements"],
                "optional": [],
            },
        }
        trajectory = {
            "trajectory": {
                "intent_requirements": {"status": "converged"},
            }
        }
        result = select_next_edge(trajectory, {}, profile)
        assert result.selected_edge == ""
        assert "All edges converged" in result.reason

    def test_pending_returns_first(self):
        profile = {
            "profile": "standard",
            "graph": {
                "include": ["intent→requirements", "requirements→design"],
                "optional": [],
            },
        }
        result = select_next_edge({"trajectory": {}}, {}, profile)
        assert result.selected_edge == "intent→requirements"


# ═══════════════════════════════════════════════════════════════════════════
# DISPATCH TABLE
# ═══════════════════════════════════════════════════════════════════════════

class TestDispatch:

    def test_fd_evaluate_registered(self):
        fn = dispatch(FunctionalUnit.EVALUATE, Category.F_D)
        assert fn is run_check

    def test_fd_emit_registered(self):
        fn = dispatch(FunctionalUnit.EMIT, Category.F_D)
        assert fn is emit_event

    def test_fp_not_implemented(self):
        with pytest.raises(NotImplementedError):
            dispatch(FunctionalUnit.EVALUATE, Category.F_P)

    def test_fh_not_implemented(self):
        with pytest.raises(NotImplementedError):
            dispatch(FunctionalUnit.DECIDE, Category.F_H)

    def test_lookup_and_dispatch_from_profile(self):
        profile = {
            "encoding": {
                "functional_units": {
                    "evaluate": "F_D",
                }
            }
        }
        fn = lookup_and_dispatch(FunctionalUnit.EVALUATE, profile)
        assert fn is run_check
