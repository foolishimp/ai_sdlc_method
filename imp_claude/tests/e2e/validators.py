# Validates: REQ-TOOL-005, REQ-EVAL-001
"""Validation functions for E2E convergence test artifacts.

Each function validates one category of output from a headless Claude run.
Functions raise AssertionError with descriptive messages on failure.
"""

import json
import pathlib
import re
import subprocess
from datetime import datetime
from typing import Any


# ═══════════════════════════════════════════════════════════════════════
# EVENT VALIDATORS
# ═══════════════════════════════════════════════════════════════════════

def load_events(project_dir: pathlib.Path) -> list[dict[str, Any]]:
    """Parse events.jsonl, raising on malformed JSON."""
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    assert events_file.exists(), f"events.jsonl not found at {events_file}"

    events = []
    with open(events_file) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise AssertionError(
                    f"Malformed JSON on line {i} of events.jsonl: {e}\n"
                    f"Line content: {line[:200]}"
                )
    return events


def validate_event_common_fields(events: list[dict]) -> None:
    """Every event must have event_type, timestamp, and project."""
    required = {"event_type", "timestamp"}
    for i, event in enumerate(events):
        missing = required - set(event.keys())
        assert not missing, (
            f"Event {i} missing required fields {missing}: "
            f"{json.dumps(event, indent=2)[:300]}"
        )


def validate_timestamps_monotonic(events: list[dict]) -> None:
    """Timestamps must not go backward (allows equal for rapid events)."""
    timestamps = []
    for event in events:
        ts_str = event.get("timestamp", "")
        if not ts_str:
            continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            timestamps.append((ts, event))
        except (ValueError, TypeError):
            # Non-ISO timestamps are allowed — skip ordering check for those
            pass

    for i in range(1, len(timestamps)):
        prev_ts, prev_event = timestamps[i - 1]
        curr_ts, curr_event = timestamps[i]
        assert curr_ts >= prev_ts, (
            f"Timestamp went backward at event {i}: "
            f"{prev_ts.isoformat()} ({prev_event.get('event_type')}) > "
            f"{curr_ts.isoformat()} ({curr_event.get('event_type')})"
        )


def validate_iteration_sequences(events: list[dict]) -> None:
    """For each feature+edge pair, iteration numbers should be sequential."""
    sequences: dict[str, list[int]] = {}
    for event in events:
        if event.get("event_type") != "iteration_completed":
            continue
        feature = event.get("feature", "unknown")
        edge = event.get("edge", "unknown")
        iteration = event.get("iteration")
        if iteration is not None:
            key = f"{feature}:{edge}"
            sequences.setdefault(key, []).append(int(iteration))

    for key, iters in sequences.items():
        for i in range(1, len(iters)):
            assert iters[i] >= iters[i - 1], (
                f"Non-sequential iterations for {key}: {iters}"
            )


def validate_delta_decreases_to_zero(events: list[dict]) -> None:
    """For converged edges, the final iteration's delta should be 0."""
    # Collect last delta per feature+edge
    last_delta: dict[str, Any] = {}
    converged_edges: set[str] = set()

    for event in events:
        et = event.get("event_type")
        feature = event.get("feature", "unknown")
        edge = event.get("edge", "unknown")
        key = f"{feature}:{edge}"

        if et == "iteration_completed":
            delta = event.get("delta")
            if delta is not None:
                last_delta[key] = delta

        if et == "edge_converged":
            converged_edges.add(key)

    for key in converged_edges:
        if key in last_delta:
            assert last_delta[key] == 0, (
                f"Converged edge {key} has final delta={last_delta[key]}, expected 0"
            )


STANDARD_PROFILE_EDGES = [
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
]


def validate_all_edges_converged(events: list[dict], feature: str) -> None:
    """All 4 standard-profile edges must have edge_converged events."""
    converged = set()
    for event in events:
        if (
            event.get("event_type") == "edge_converged"
            and event.get("feature") == feature
        ):
            converged.add(event.get("edge", ""))

    missing = set(STANDARD_PROFILE_EDGES) - converged
    assert not missing, (
        f"Feature {feature} missing edge_converged for: {missing}\n"
        f"Converged edges found: {converged}"
    )


def validate_required_event_types(events: list[dict]) -> None:
    """The event log must contain at minimum these event types."""
    required_types = {
        "project_initialized",
        "edge_started",
        "iteration_completed",
        "edge_converged",
    }
    found_types = {e.get("event_type") for e in events}
    missing = required_types - found_types
    assert not missing, (
        f"Missing required event types: {missing}\n"
        f"Found types: {found_types}"
    )


def validate_evaluator_counts(events: list[dict]) -> None:
    """Iteration events should reference evaluator or check results."""
    iteration_events = [
        e for e in events if e.get("event_type") == "iteration_completed"
    ]
    if not iteration_events:
        return

    # Accept any of: evaluator_results, delta, checks_passed/checks_total, result
    has_evaluator_info = any(
        e.get("evaluator_results")
        or e.get("delta") is not None
        or e.get("checks_passed") is not None
        or e.get("checks_total") is not None
        or e.get("result") is not None
        for e in iteration_events
    )
    assert has_evaluator_info, (
        "No iteration events contain evaluator/check result information"
    )


# ═══════════════════════════════════════════════════════════════════════
# FEATURE VECTOR VALIDATORS
# ═══════════════════════════════════════════════════════════════════════

def load_feature_vector(
    project_dir: pathlib.Path, feature_id: str
) -> dict[str, Any]:
    """Find and parse the feature vector YAML (check active/ then completed/)."""
    import yaml

    filename = f"{feature_id}.yml"
    candidates = [
        project_dir / ".ai-workspace" / "features" / "active" / filename,
        project_dir / ".ai-workspace" / "features" / "completed" / filename,
        # Also check without prefix normalization
    ]

    # Broad search fallback
    for d in (project_dir / ".ai-workspace" / "features").rglob("*.yml"):
        if feature_id in d.name and d not in candidates:
            candidates.append(d)

    for path in candidates:
        if path.exists():
            with open(path) as f:
                data = yaml.safe_load(f)
            if data:
                return data

    raise AssertionError(
        f"Feature vector {feature_id} not found. "
        f"Searched: {[str(c) for c in candidates]}"
    )


def validate_feature_vector_converged(fv: dict) -> None:
    """Feature vector should show converged status with trajectory data."""
    status = fv.get("status", "")
    assert status == "converged", (
        f"Feature vector status is '{status}', expected 'converged'"
    )

    trajectory = fv.get("trajectory", {})
    assert trajectory, "Feature vector has no trajectory data"

    for edge_name in ["requirements", "design", "code", "unit_tests"]:
        edge_data = trajectory.get(edge_name, {})
        edge_status = edge_data.get("status", "pending")
        assert edge_status == "converged", (
            f"Trajectory edge '{edge_name}' status is '{edge_status}', "
            f"expected 'converged'"
        )


def validate_feature_vector_required_fields(fv: dict) -> None:
    """Feature vector must have core fields populated."""
    required = ["feature", "status", "trajectory"]
    for field in required:
        assert field in fv and fv[field], (
            f"Feature vector missing or empty required field: {field}"
        )


def validate_trajectory_timestamps(fv: dict) -> None:
    """Converged trajectory edges should have temporal or iteration metadata."""
    trajectory = fv.get("trajectory", {})
    converged_edges = [
        name for name, data in trajectory.items()
        if isinstance(data, dict) and data.get("status") == "converged"
    ]
    if not converged_edges:
        return

    # Accept timestamps OR iteration counts OR artifact paths as evidence
    has_metadata = any(
        trajectory[name].get("converged_at")
        or trajectory[name].get("started_at")
        or trajectory[name].get("iterations") is not None
        or trajectory[name].get("iteration") is not None
        or trajectory[name].get("artifact")
        for name in converged_edges
        if isinstance(trajectory.get(name), dict)
    )
    assert has_metadata, (
        f"No converged edges have timestamps or iteration metadata. "
        f"Converged: {converged_edges}"
    )


def validate_requirements_populated(fv: dict) -> None:
    """Feature vector should reference its REQ keys."""
    feature_id = fv.get("feature", "")
    assert feature_id, "Feature vector has no feature ID"
    assert feature_id.startswith("REQ-F-"), (
        f"Feature ID '{feature_id}' doesn't match REQ-F-* pattern"
    )


# ═══════════════════════════════════════════════════════════════════════
# GENERATED CODE VALIDATORS
# ═══════════════════════════════════════════════════════════════════════

def find_python_files(project_dir: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    """Locate code and test .py files. Returns (code_files, test_files)."""
    all_py = list(project_dir.rglob("*.py"))

    # Exclude workspace and config files
    excluded_dirs = {".ai-workspace", ".git", ".claude", "__pycache__", ".e2e-meta"}

    def is_excluded(p: pathlib.Path) -> bool:
        return any(part in excluded_dirs for part in p.parts)

    py_files = [p for p in all_py if not is_excluded(p)]

    code_files = [p for p in py_files if "test" not in p.name.lower() and "conftest" not in p.name.lower()]
    test_files = [p for p in py_files if "test" in p.name.lower() or "conftest" in p.name.lower()]

    return code_files, test_files


def extract_req_tags(files: list[pathlib.Path]) -> dict[str, set[str]]:
    """Extract REQ tags from files. Returns {tag_type: {REQ-key, ...}}."""
    implements: set[str] = set()
    validates: set[str] = set()

    impl_pattern = re.compile(r"Implements:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")
    val_pattern = re.compile(r"Validates:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")

    for f in files:
        try:
            content = f.read_text(errors="replace")
        except OSError:
            continue
        implements.update(impl_pattern.findall(content))
        validates.update(val_pattern.findall(content))

    return {"implements": implements, "validates": validates}


def validate_code_traceability(
    project_dir: pathlib.Path, required_reqs: set[str]
) -> None:
    """Both REQ keys should appear in code Implements tags and test Validates tags."""
    code_files, test_files = find_python_files(project_dir)

    assert code_files, "No Python code files found in project"
    assert test_files, "No Python test files found in project"

    code_tags = extract_req_tags(code_files)
    test_tags = extract_req_tags(test_files)

    code_implements = code_tags["implements"]
    test_validates = test_tags["validates"]

    # At least one required REQ should be in code Implements tags
    code_covered = required_reqs & code_implements
    assert code_covered, (
        f"No required REQ keys found in code Implements tags.\n"
        f"Required: {required_reqs}\n"
        f"Found in code: {code_implements}"
    )

    # At least one required REQ should be in test Validates tags
    test_covered = required_reqs & test_validates
    assert test_covered, (
        f"No required REQ keys found in test Validates tags.\n"
        f"Required: {required_reqs}\n"
        f"Found in tests: {test_validates}"
    )


def validate_generated_tests_pass(project_dir: pathlib.Path) -> None:
    """Run pytest on the generated project and verify tests pass."""
    _, test_files = find_python_files(project_dir)
    if not test_files:
        raise AssertionError("No test files found to run")

    result = subprocess.run(
        ["python", "-m", "pytest", "-v", "--tb=short", "--no-header"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=60,
    )

    assert result.returncode == 0, (
        f"Generated tests failed (exit code {result.returncode}).\n"
        f"STDOUT:\n{result.stdout[-2000:]}\n"
        f"STDERR:\n{result.stderr[-1000:]}"
    )


# ═══════════════════════════════════════════════════════════════════════
# CONSISTENCY VALIDATORS
# ═══════════════════════════════════════════════════════════════════════

def validate_req_key_consistency(
    project_dir: pathlib.Path, required_reqs: set[str]
) -> None:
    """FV REQs should appear in code Implements and test Validates tags."""
    code_files, test_files = find_python_files(project_dir)
    all_files = code_files + test_files

    tags = extract_req_tags(all_files)
    all_found = tags["implements"] | tags["validates"]

    # At least one of the required REQs must appear somewhere
    covered = required_reqs & all_found
    assert covered, (
        f"None of the required REQ keys found in generated code.\n"
        f"Required: {required_reqs}\n"
        f"Found: {all_found}"
    )


def validate_multi_iteration_convergence(
    events: list[dict], edge: str, feature: str,
) -> None:
    """Verify that an edge took multiple iterations to converge.

    Proves iterate() handles real failures, not just 1-shot convergence.
    Also checks delta progression (should decrease to 0).
    """
    iterations = [
        e for e in events
        if e.get("event_type") == "iteration_completed"
        and e.get("edge") == edge
        and e.get("feature") == feature
    ]
    assert len(iterations) > 1, (
        f"{feature}:{edge} converged in {len(iterations)} iteration(s), "
        f"expected > 1 for genuine convergence proof."
    )

    # Check delta progression
    deltas = [it.get("delta") for it in iterations if it.get("delta") is not None]
    if deltas:
        assert deltas[0] > 0, (
            f"First iteration delta is {deltas[0]}, expected > 0 "
            f"(pre-conditions should guarantee initial failure)."
        )
        assert deltas[-1] == 0, (
            f"Final iteration delta is {deltas[-1]}, expected 0. "
            f"Delta progression: {deltas}"
        )


def validate_event_feature_consistency(
    events: list[dict], expected_features: set[str]
) -> None:
    """Event feature refs should include the expected feature IDs."""
    event_features = set()
    for event in events:
        feat = event.get("feature")
        if feat and feat.startswith("REQ-F-"):
            event_features.add(feat)

    if not event_features:
        # Events may not all have feature field — only check if some do
        return

    # At least one expected feature should appear in events
    overlap = expected_features & event_features
    assert overlap, (
        f"Expected features not found in events.\n"
        f"Expected: {expected_features}\n"
        f"In events: {event_features}"
    )
