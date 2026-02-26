"""Tests for genesis_engine.models — data model integrity."""

from genesis_engine.models import (
    Category,
    CheckOutcome,
    CheckResult,
    EvaluationResult,
    Event,
    FoldBackResult,
    FunctionalUnit,
    ResolvedCheck,
    RouteResult,
    SpawnRequest,
    SpawnResult,
    CATEGORY_FIXED,
)


def test_category_values():
    assert Category.F_D.value == "F_D"
    assert Category.F_P.value == "F_P"
    assert Category.F_H.value == "F_H"


def test_functional_unit_count():
    assert len(FunctionalUnit) == 8


def test_category_fixed_emit_is_fd():
    assert CATEGORY_FIXED[FunctionalUnit.EMIT] == Category.F_D


def test_category_fixed_decide_is_fh():
    assert CATEGORY_FIXED[FunctionalUnit.DECIDE] == Category.F_H


def test_check_outcome_values():
    assert {o.value for o in CheckOutcome} == {"pass", "fail", "skip", "error"}


def test_resolved_check_defaults():
    rc = ResolvedCheck(
        name="test", check_type="deterministic", functional_unit="evaluate",
        criterion="x", source="default", required=True,
    )
    assert rc.command is None
    assert rc.pass_criterion is None
    assert rc.unresolved == []


def test_check_result_defaults():
    cr = CheckResult(
        name="test", outcome=CheckOutcome.PASS, required=True,
        check_type="deterministic", functional_unit="evaluate",
    )
    assert cr.message == ""
    assert cr.exit_code is None


def test_evaluation_result_defaults():
    er = EvaluationResult(edge="code↔unit_tests")
    assert er.checks == []
    assert er.delta == 0
    assert er.converged is False
    assert er.spawn_requested == ""


def test_route_result():
    rr = RouteResult(selected_edge="a→b", reason="test", profile="standard")
    assert rr.candidates == []


def test_spawn_request():
    sr = SpawnRequest(
        question="why?", vector_type="discovery",
        parent_feature="REQ-F-001", triggered_at_edge="code↔unit_tests",
    )
    assert sr.context_hints == {}


def test_spawn_result():
    sr = SpawnResult(
        child_id="REQ-F-DISCOVERY-001", child_path="/tmp/x.yml",
        parent_updated=True, event_emitted=True, profile="minimal",
    )
    assert sr.child_id.startswith("REQ-F-")


def test_fold_back_result():
    fbr = FoldBackResult(
        parent_id="REQ-F-001", child_id="REQ-F-DISCOVERY-001",
        payload_path="/tmp/fb.md", parent_unblocked=True, event_emitted=True,
    )
    assert fbr.parent_unblocked is True


def test_event_defaults():
    e = Event(event_type="test", timestamp="2026-01-01T00:00:00Z", project="p")
    assert e.data == {}
