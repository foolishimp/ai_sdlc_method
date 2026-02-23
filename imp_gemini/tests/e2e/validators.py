# Validates: REQ-TOOL-005, REQ-EVAL-001
import json
import pathlib
import re
import subprocess
from datetime import datetime
from typing import Any

def load_events(project_dir: pathlib.Path) -> list[dict[str, Any]]:
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    assert events_file.exists(), f"events.jsonl not found at {events_file}"
    events = []
    with open(events_file) as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line: continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError as e:
                raise AssertionError(f"Malformed JSON on line {i} of events.jsonl: {e}")
    return events

def validate_event_common_fields(events: list[dict]) -> None:
    required = {"event_type", "timestamp"}
    for i, event in enumerate(events):
        missing = required - set(event.keys())
        assert not missing, f"Event {i} missing required fields {missing}"

def validate_timestamps_monotonic(events: list[dict]) -> None:
    timestamps = []
    for event in events:
        ts_str = event.get("timestamp", "")
        if not ts_str: continue
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            timestamps.append(ts)
        except (ValueError, TypeError): pass
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i-1], f"Timestamp went backward at event {i}"

def validate_iteration_sequences(events: list[dict]) -> None:
    sequences: dict[str, list[int]] = {}
    for event in events:
        if event.get("event_type") != "iteration_completed": continue
        key = f"{event.get('feature')}:{event.get('edge')}"
        iteration = event.get("iteration")
        if iteration is not None:
            sequences.setdefault(key, []).append(int(iteration))
    for key, iters in sequences.items():
        for i in range(1, len(iters)):
            assert iters[i] >= iters[i-1], f"Non-sequential iterations for {key}"

def validate_delta_decreases_to_zero(events: list[dict]) -> None:
    last_delta: dict[str, Any] = {}
    converged_edges: set[str] = set()
    for event in events:
        key = f"{event.get('feature')}:{event.get('edge')}"
        if event.get("event_type") == "iteration_completed":
            delta = event.get("delta")
            if delta is not None: last_delta[key] = delta
        if event.get("event_type") == "edge_converged":
            converged_edges.add(key)
    for key in converged_edges:
        if key in last_delta:
            assert last_delta[key] == 0, f"Converged edge {key} has final delta={last_delta[key]}"

def validate_all_edges_converged(events: list[dict], feature: str) -> None:
    expected = {"intent→requirements", "requirements→design", "design→code", "code↔unit_tests"}
    converged = {e.get("edge", "") for e in events if e.get("event_type") == "edge_converged" and e.get("feature") == feature}
    missing = expected - converged
    assert not missing, f"Feature {feature} missing edge_converged for: {missing}"

def validate_required_event_types(events: list[dict]) -> None:
    required = {"project_initialized", "edge_started", "iteration_completed", "edge_converged"}
    found = {e.get("event_type") for e in events}
    assert required.issubset(found), f"Missing required event types. Found: {found}"

def validate_evaluator_counts(events: list[dict]) -> None:
    iteration_events = [e for e in events if e.get("event_type") == "iteration_completed"]
    if not iteration_events: return
    has_info = any(e.get("evaluators") or e.get("delta") is not None for e in iteration_events)
    assert has_info, "No iteration events contain evaluator/check result information"

def load_feature_vector(project_dir: pathlib.Path, feature_id: str) -> dict[str, Any]:
    import yaml
    path = project_dir / ".ai-workspace" / "features" / "active" / f"{feature_id}.yml"
    if not path.exists():
        path = project_dir / ".ai-workspace" / "features" / "completed" / f"{feature_id}.yml"
    assert path.exists(), f"Feature vector {feature_id} not found"
    with open(path) as f:
        return yaml.safe_load(f)

def validate_feature_vector_converged(fv: dict) -> None:
    assert fv.get("status") == "converged"
    traj = fv.get("trajectory", {})
    for edge in ["requirements", "design", "code", "unit_tests"]:
        assert traj.get(edge, {}).get("status") == "converged"

def validate_feature_vector_required_fields(fv: dict) -> None:
    for field in ["feature", "status", "trajectory"]:
        assert fv.get(field)

def validate_trajectory_timestamps(fv: dict) -> None:
    traj = fv.get("trajectory", {})
    has_meta = any(v.get("converged_at") or v.get("started_at") or v.get("iteration") is not None 
                   for v in traj.values() if isinstance(v, dict) and v.get("status") == "converged")
    assert has_meta

def validate_requirements_populated(fv: dict) -> None:
    assert fv.get("feature", "").startswith("REQ-F-")

def find_python_files(project_dir: pathlib.Path) -> tuple[list[pathlib.Path], list[pathlib.Path]]:
    all_py = list(project_dir.rglob("*.py"))
    excluded = {".ai-workspace", ".git", "__pycache__", ".e2e-meta"}
    py_files = [p for p in all_py if not any(part in excluded for part in p.parts)]
    code_files = [p for p in py_files if "test" not in p.name.lower() and "conftest" not in p.name.lower()]
    test_files = [p for p in py_files if "test" in p.name.lower() or "conftest" in p.name.lower()]
    return code_files, test_files

def extract_req_tags(files: list[pathlib.Path]) -> dict[str, set[str]]:
    implements, validates = set(), set()
    impl_p = re.compile(r"Implements:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")
    val_p = re.compile(r"Validates:\s*(REQ-[A-Z]+-[A-Z]+-\d+)")
    for f in files:
        try:
            content = f.read_text(errors="replace")
            implements.update(impl_p.findall(content))
            validates.update(val_p.findall(content))
        except OSError: continue
    return {"implements": implements, "validates": validates}

def validate_code_traceability(project_dir: pathlib.Path, required_reqs: set[str]) -> None:
    code_files, test_files = find_python_files(project_dir)
    assert code_files and test_files
    assert required_reqs & extract_req_tags(code_files)["implements"]
    assert required_reqs & extract_req_tags(test_files)["validates"]

def validate_generated_tests_pass(project_dir: pathlib.Path) -> None:
    result = subprocess.run(["python3", "-m", "pytest", "-v"], cwd=str(project_dir), capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, f"Tests failed:\n{result.stdout}\n{result.stderr}"

def validate_req_key_consistency(project_dir: pathlib.Path, required_reqs: set[str]) -> None:
    code_f, test_f = find_python_files(project_dir)
    tags = extract_req_tags(code_f + test_f)
    assert required_reqs & (tags["implements"] | tags["validates"])

def validate_event_feature_consistency(events: list[dict], expected_features: set[str]) -> None:
    found = {e.get("feature") for e in events if e.get("feature", "").startswith("REQ-F-")}
    if found: assert expected_features & found
