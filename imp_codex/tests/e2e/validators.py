# Validates: REQ-TOOL-005, REQ-EVAL-001
"""Validation helpers for Codex Genesis E2E artifacts."""

from __future__ import annotations

import json
import os
import pathlib
import re
import subprocess
from datetime import datetime
from typing import Any


STANDARD_PROFILE_EDGES = [
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
]


def load_events(project_dir: pathlib.Path) -> list[dict[str, Any]]:
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    assert events_file.exists(), f"events.jsonl not found at {events_file}"
    events: list[dict[str, Any]] = []
    with open(events_file) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise AssertionError(f"Malformed JSON line {i}: {e}") from e
    return events


def validate_event_common_fields(events: list[dict[str, Any]]) -> None:
    required = {"event_type", "timestamp", "project"}
    for i, event in enumerate(events):
        missing = required - set(event.keys())
        assert not missing, f"Event {i} missing required fields: {missing}"


def validate_timestamps_monotonic(events: list[dict[str, Any]]) -> None:
    parsed: list[datetime] = []
    for event in events:
        ts = event.get("timestamp")
        if not ts:
            continue
        parsed.append(datetime.fromisoformat(ts.replace("Z", "+00:00")))
    for i in range(1, len(parsed)):
        assert parsed[i] >= parsed[i - 1], "Event timestamps moved backward"


def validate_required_event_types(events: list[dict[str, Any]]) -> None:
    required = {"project_initialized", "edge_started", "iteration_completed", "edge_converged"}
    found = {e.get("event_type") for e in events}
    missing = required - found
    assert not missing, f"Missing required event types: {missing}"


def validate_iteration_sequences(events: list[dict[str, Any]]) -> None:
    seq: dict[tuple[str, str], list[int]] = {}
    for event in events:
        if event.get("event_type") != "iteration_completed":
            continue
        feature = str(event.get("feature", ""))
        edge = str(event.get("edge", ""))
        it = int(event.get("iteration", 0))
        seq.setdefault((feature, edge), []).append(it)
    for key, vals in seq.items():
        for i in range(1, len(vals)):
            assert vals[i] >= vals[i - 1], f"Non-sequential iterations for {key}: {vals}"


def validate_delta_decreases_to_zero(events: list[dict[str, Any]]) -> None:
    last_delta: dict[tuple[str, str], int] = {}
    converged: set[tuple[str, str]] = set()
    for event in events:
        et = event.get("event_type")
        feature = str(event.get("feature", ""))
        edge = str(event.get("edge", ""))
        key = (feature, edge)
        if et == "iteration_completed":
            last_delta[key] = int(event.get("delta", 0))
        if et == "edge_converged":
            converged.add(key)
    for key in converged:
        assert last_delta.get(key, 0) == 0, f"Converged edge {key} has non-zero delta"


def validate_evaluator_counts(events: list[dict[str, Any]]) -> None:
    it_events = [e for e in events if e.get("event_type") == "iteration_completed"]
    assert it_events, "No iteration_completed events found"
    for event in it_events:
        evaluators = event.get("evaluators", {})
        assert isinstance(evaluators, dict), "evaluators must be an object"
        assert "total" in evaluators, "iteration event missing evaluators.total"


def validate_all_edges_converged(events: list[dict[str, Any]], feature_id: str) -> None:
    converged = {
        e.get("edge", "")
        for e in events
        if e.get("event_type") == "edge_converged" and e.get("feature") == feature_id
    }
    missing = set(STANDARD_PROFILE_EDGES) - converged
    assert not missing, f"Missing converged edges: {missing}"


def load_feature_vector(project_dir: pathlib.Path, feature_id: str) -> dict[str, Any]:
    import yaml

    path = project_dir / ".ai-workspace" / "features" / "active" / f"{feature_id}.yml"
    if not path.exists():
        path = project_dir / ".ai-workspace" / "features" / "completed" / f"{feature_id}.yml"
    assert path.exists(), f"Feature vector not found: {feature_id}"
    with open(path) as f:
        data = yaml.safe_load(f)
    assert isinstance(data, dict), "Feature vector must parse to object"
    return data


def validate_feature_vector_converged(fv: dict[str, Any]) -> None:
    assert fv.get("status") == "converged", "Feature vector status is not converged"
    trajectory = fv.get("trajectory", {})
    for phase in ("requirements", "design", "code", "unit_tests"):
        assert trajectory.get(phase, {}).get("status") == "converged", f"{phase} not converged"


def validate_feature_vector_required_fields(fv: dict[str, Any]) -> None:
    for field in ("feature", "title", "status", "trajectory"):
        assert field in fv and fv[field], f"Missing required field: {field}"


def validate_trajectory_timestamps(fv: dict[str, Any]) -> None:
    trajectory = fv.get("trajectory", {})
    for phase in ("requirements", "design", "code", "unit_tests"):
        phase_data = trajectory.get(phase, {})
        assert phase_data.get("started_at"), f"{phase} missing started_at"
        assert phase_data.get("converged_at"), f"{phase} missing converged_at"


def validate_requirements_populated(fv: dict[str, Any]) -> None:
    feature = str(fv.get("feature", ""))
    assert feature.startswith("REQ-F-"), f"Unexpected feature id format: {feature}"


def find_python_files(project_dir: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    all_py = [
        p for p in project_dir.rglob("*.py")
        if ".ai-workspace" not in p.parts and "__pycache__" not in p.parts
    ]
    code_files = [p for p in all_py if "test" not in p.name.lower()]
    test_files = [p for p in all_py if "test" in p.name.lower()]
    return code_files, test_files


def extract_req_tags(files: list[pathlib.Path]) -> dict[str, set[str]]:
    implements: set[str] = set()
    validates: set[str] = set()
    impl_pattern = re.compile(r"Implements:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")
    val_pattern = re.compile(r"Validates:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")
    for f in files:
        content = f.read_text(errors="replace")
        implements.update(impl_pattern.findall(content))
        validates.update(val_pattern.findall(content))
    return {"implements": implements, "validates": validates}


def validate_generated_tests_pass(project_dir: pathlib.Path) -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_dir)
    result = subprocess.run(
        ["pytest", "-q", "tests"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, (
        f"Generated tests failed\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )


def validate_code_traceability(project_dir: pathlib.Path, required_reqs: set[str]) -> None:
    code_files, test_files = find_python_files(project_dir)
    tags_code = extract_req_tags(code_files)
    tags_test = extract_req_tags(test_files)
    found = tags_code["implements"] | tags_test["validates"]
    missing = required_reqs - found
    assert not missing, f"Missing REQ tags in code/test files: {missing}"


def validate_req_key_consistency(project_dir: pathlib.Path, required_reqs: set[str]) -> None:
    fv = load_feature_vector(project_dir, "REQ-F-CONV-001")
    assert str(fv.get("feature", "")) in required_reqs, "Feature vector key not in required set"


def validate_event_feature_consistency(events: list[dict[str, Any]], expected_features: set[str]) -> None:
    event_features = {
        str(e.get("feature"))
        for e in events
        if "feature" in e and e.get("feature") is not None
    }
    missing = expected_features - event_features
    assert not missing, f"Expected features missing from event stream: {missing}"
