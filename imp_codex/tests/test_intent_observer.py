# Validates: REQ-F-DISPATCH-001, REQ-F-ENGINE-001, REQ-F-LIFE-001
"""Durable intent observer tests derived from the accepted dispatch ADR."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from imp_codex.runtime import RuntimePaths, append_run_event, bootstrap_workspace
from imp_codex.runtime.intent_observer import run_intent_observer


def _write_intent(project_root: Path) -> None:
    spec_dir = project_root / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text("# Intent\n\nObserver spec fixture.\n")


def _write_feature(paths: RuntimePaths, feature_id: str, *, profile: str = "minimal") -> None:
    feature_doc = yaml.safe_load(paths.feature_template_path.read_text())
    feature_doc["feature"] = feature_id
    feature_doc["title"] = feature_id
    feature_doc["profile"] = profile
    feature_doc["status"] = "in_progress"
    feature_doc["trajectory"] = {}
    paths.active_features_dir.mkdir(parents=True, exist_ok=True)
    (paths.active_features_dir / f"{feature_id}.yml").write_text(yaml.safe_dump(feature_doc, sort_keys=False))


def _emit_intent(
    paths: RuntimePaths,
    *,
    intent_id: str,
    affected_features: list[str] | None = None,
) -> None:
    append_run_event(
        paths.events_file,
        project_name="demo",
        semantic_type="intent_raised",
        actor="pytest",
        edge="gap_analysis",
        payload={
            "intent_id": intent_id,
            "trigger": "observer test",
            "delta": "pending work",
            "signal_source": "gap",
            "vector_type": "feature",
            "severity": "high",
            "requires_spec_change": False,
            "affected_features": list(affected_features or []),
            "affected_req_keys": [],
        },
    )


def test_once_mode_dispatches_existing_intent(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-TEST-001")
    _emit_intent(paths, intent_id="INT-001", affected_features=["REQ-F-TEST-001"])

    result = run_intent_observer(
        project_root,
        once=True,
        poll_interval_seconds=0,
        max_dispatch_per_poll=1,
    )

    assert result.polls == 1
    assert result.dispatched_count == 1
    assert result.dispatches[0]["intent_id"] == "INT-001"
    assert result.dispatches[0]["feature"] == "REQ-F-TEST-001"
    assert result.stopped_reason == "once"


def test_multiple_polls_do_not_redispatch_handled_intent(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-TEST-001")
    _emit_intent(paths, intent_id="INT-001", affected_features=["REQ-F-TEST-001"])

    result = run_intent_observer(
        project_root,
        poll_interval_seconds=0,
        max_polls=2,
        max_dispatch_per_poll=1,
    )

    assert result.polls == 2
    assert result.dispatched_count == 1
    assert result.dispatches[0]["intent_id"] == "INT-001"
    assert result.stopped_reason == "max_polls"


def test_late_intent_is_dispatched_on_subsequent_poll(tmp_path):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    paths = bootstrap_workspace(project_root, project_name="demo")
    _write_feature(paths, "REQ-F-LATE-001")

    def _after_poll(polls: int, _result: dict) -> None:
        if polls == 1:
            _emit_intent(paths, intent_id="INT-LATE-001", affected_features=["REQ-F-LATE-001"])

    result = run_intent_observer(
        project_root,
        poll_interval_seconds=0,
        max_polls=2,
        max_dispatch_per_poll=1,
        _after_poll=_after_poll,
    )

    assert result.polls == 2
    assert result.dispatched_count == 1
    assert result.dispatches[0]["intent_id"] == "INT-LATE-001"
    assert result.dispatches[0]["feature"] == "REQ-F-LATE-001"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"poll_interval_seconds": -1}, "poll_interval_seconds"),
        ({"max_polls": 0}, "max_polls"),
        ({"idle_polls_before_stop": 0}, "idle_polls_before_stop"),
        ({"max_dispatch_per_poll": 0}, "max_dispatch_per_poll"),
    ],
)
def test_invalid_arguments_raise_value_error(tmp_path, kwargs, message):
    project_root = tmp_path / "demo"
    _write_intent(project_root)
    bootstrap_workspace(project_root, project_name="demo")

    with pytest.raises(ValueError, match=message):
        run_intent_observer(project_root, **kwargs)
