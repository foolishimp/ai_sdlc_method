# Validates: REQ-SUPV-003, REQ-EVAL-001, REQ-EVAL-002, REQ-ITER-001, REQ-ITER-002
"""Real Codex homeostasis e2e derived from the Claude homeostasis spec."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import textwrap
import importlib.util

import pytest
import yaml

from . import conftest as e2e_support


FEATURE_ID = "REQ-F-FAIL-001"
EDGE = "code↔unit_tests"
PROJECT_NAME = "temperature-homeostasis"

PROJECT_CONSTRAINTS = textwrap.dedent(
    """\
    ---
    project:
      name: "temperature-homeostasis"
      version: "0.1.0"
      default_profile: standard
    context_sources: []
    language:
      primary: python
      version: "3.11"
    thresholds:
      test_coverage_minimum: 0.80
      test_coverage_target: 1.00
    """
)

FEATURE_VECTOR = textwrap.dedent(
    """\
    ---
    feature: "REQ-F-FAIL-001"
    title: "Repair Temperature Conversion"
    intent: "INT-001"
    vector_type: feature
    profile: standard
    status: in_progress
    created: "{ts}"
    updated: "{ts}"
    trajectory:
      requirements:
        status: converged
        iteration: 1
        started_at: "{ts}"
        converged_at: "{ts}"
      design:
        status: converged
        iteration: 1
        started_at: "{ts}"
        converged_at: "{ts}"
      code:
        status: converged
        iteration: 1
        started_at: "{ts}"
        converged_at: "{ts}"
      unit_tests:
        status: iterating
        iteration: 0
        started_at: "{ts}"
      uat_tests:
        status: pending
    """
)

PYPROJECT_TOML = textwrap.dedent(
    """\
    [project]
    name = "temperature-homeostasis"
    version = "0.1.0"
    requires-python = ">=3.11"

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    """
)

INTENT_MD = textwrap.dedent(
    """\
    # Intent: Temperature Homeostasis

    Repair the seeded temperature conversion bug and make the test suite pass.
    """
)

REQUIREMENTS_MD = textwrap.dedent(
    """\
    # Requirements

    ## REQ-F-FAIL-001
    The converter must correctly translate Celsius and Fahrenheit values.

    ### Acceptance Criteria
    - `celsius_to_fahrenheit(0) == 32`
    - `fahrenheit_to_celsius(212) == 100`
    - invalid values below absolute zero raise `ValueError`
    """
)

DESIGN_MD = textwrap.dedent(
    """\
    # Design

    Implements: REQ-F-FAIL-001

    ## Interfaces
    - `celsius_to_fahrenheit(c: float) -> float`
    - `fahrenheit_to_celsius(f: float) -> float`

    ## Dependencies
    - pytest
    """
)

BUGGY_CONVERTER = textwrap.dedent(
    """\
    # Implements: REQ-F-FAIL-001

    def _check_number(v):
        if not isinstance(v, (int, float)):
            raise TypeError("temperature must be numeric")

    def celsius_to_fahrenheit(c):
        _check_number(c)
        if c < -273.15:
            raise ValueError("below absolute zero")
        return c * 2 + 30

    def fahrenheit_to_celsius(f):
        _check_number(f)
        if f < -459.67:
            raise ValueError("below absolute zero")
        return f - 32
    """
)

CORRECT_TESTS = textwrap.dedent(
    """\
    # Validates: REQ-F-FAIL-001
    import pytest

    from src.converter import celsius_to_fahrenheit, fahrenheit_to_celsius

    def test_formulas():
        assert celsius_to_fahrenheit(0) == 32.0
        assert celsius_to_fahrenheit(100) == 212.0
        assert round(fahrenheit_to_celsius(212), 6) == 100.0

    def test_validation():
        with pytest.raises(TypeError):
            celsius_to_fahrenheit("x")
        with pytest.raises(ValueError):
            celsius_to_fahrenheit(-300)
    """
)

HOMEOSTASIS_DRIVER = textwrap.dedent(
    """\
    from __future__ import annotations

    import json
    import os
    import re
    import subprocess
    from datetime import datetime, timezone
    from pathlib import Path

    import yaml

    PROJECT = "temperature-homeostasis"
    FEATURE = "REQ-F-FAIL-001"
    EDGE = "code↔unit_tests"

    project_dir = Path.cwd()
    ws = project_dir / ".ai-workspace"
    events_file = ws / "events" / "events.jsonl"
    status_file = ws / "codex" / "context" / "homeostasis_status.txt"
    report_file = ws / "codex" / "context" / "homeostasis_failure.json"
    feature_file = ws / "features" / "active" / f"{FEATURE}.yml"

    def now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def append_event(payload: dict) -> None:
        events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(events_file, "a") as handle:
            handle.write(json.dumps(payload) + "\\n")

    def load_events() -> list[dict]:
        if not events_file.exists():
            return []
        rows = []
        for line in events_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
        return rows

    def next_iteration() -> int:
        count = 0
        for event in load_events():
            if event.get("event_type") == "iteration_completed" and event.get("edge") == EDGE:
                count += 1
        return count + 1

    def count_failures(output: str) -> int:
        match = re.search(r"(\\d+) failed", output)
        if match:
            return int(match.group(1))
        return 0

    def update_feature_vector(converged: bool, iteration: int) -> None:
        if not feature_file.exists():
            return
        data = yaml.safe_load(feature_file.read_text())
        data["updated"] = now()
        unit_tests = dict(data.get("trajectory", {}).get("unit_tests", {}))
        unit_tests["iteration"] = iteration
        unit_tests["status"] = "converged" if converged else "iterating"
        unit_tests.setdefault("started_at", now())
        if converged:
            unit_tests["converged_at"] = now()
            data["status"] = "converged"
        else:
            data["status"] = "in_progress"
        data.setdefault("trajectory", {})
        data["trajectory"]["unit_tests"] = unit_tests
        feature_file.write_text(yaml.safe_dump(data, sort_keys=False))

    events = load_events()
    if not any(e.get("event_type") == "edge_started" and e.get("edge") == EDGE for e in events):
        append_event(
            {
                "event_type": "edge_started",
                "timestamp": now(),
                "project": PROJECT,
                "feature": FEATURE,
                "edge": EDGE,
                "data": {"iteration": 1},
            }
        )

    iteration = next_iteration()
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_dir)
    result = subprocess.run(
        ["python", "-m", "pytest", "tests", "-q"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    combined = (result.stdout + "\\n" + result.stderr).strip()
    failed = count_failures(combined) if result.returncode != 0 else 0

    append_event(
        {
            "event_type": "iteration_completed",
            "timestamp": now(),
            "project": PROJECT,
            "feature": FEATURE,
            "edge": EDGE,
            "iteration": iteration,
            "delta": failed,
            "status": "converged" if failed == 0 else "iterating",
            "evaluators": {"passed": 1 if failed == 0 else 0, "failed": failed, "skipped": 0, "total": max(failed, 1)},
            "data": {
                "stdout_tail": result.stdout[-2000:],
                "stderr_tail": result.stderr[-1000:],
            },
        }
    )
    if failed:
        append_event(
            {
                "event_type": "evaluator_detail",
                "timestamp": now(),
                "project": PROJECT,
                "feature": FEATURE,
                "edge": EDGE,
                "data": {
                    "check_name": "tests_pass",
                    "result": "fail",
                    "failed_tests": failed,
                    "stdout_tail": result.stdout[-2000:],
                    "stderr_tail": result.stderr[-1000:],
                },
            }
        )
        report_file.write_text(
            json.dumps(
                {
                    "iteration": iteration,
                    "failed_tests": failed,
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                },
                indent=2,
            )
            + "\\n"
        )
        status_file.write_text("ITERATING\\n")
        update_feature_vector(False, iteration)
        print("ITERATING")
    else:
        append_event(
            {
                "event_type": "edge_converged",
                "timestamp": now(),
                "project": PROJECT,
                "feature": FEATURE,
                "edge": EDGE,
                "data": {"iteration": iteration},
            }
        )
        status_file.write_text("CONVERGED\\n")
        update_feature_vector(True, iteration)
        print("CONVERGED")
    """
)


def _load_events(project_dir: Path) -> list[dict]:
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    if not events_file.exists():
        return []
    rows = []
    for line in events_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _deltas(events: list[dict]) -> list[int]:
    return [
        int(event.get("delta", 0))
        for event in events
        if event.get("event_type") == "iteration_completed" and event.get("edge") == EDGE
    ]


@pytest.fixture(scope="module")
def homeostasis_result(tmp_path_factory) -> Path:
    if os.environ.get("CODEX_E2E_MODE", "").strip().lower() not in {"real", "live"}:
        pytest.skip("real Codex e2e only; set CODEX_E2E_MODE=real")
    if not e2e_support._codex_cli_available():
        pytest.skip("Codex CLI not installed")

    project_dir = tmp_path_factory.mktemp("codex-homeostasis")
    ws = project_dir / ".ai-workspace"

    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "codex-e2e@example.com"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "Codex E2E"], cwd=str(project_dir), capture_output=True)

    spec_dir = project_dir / "specification"
    spec_dir.mkdir(parents=True, exist_ok=True)
    (spec_dir / "INTENT.md").write_text(INTENT_MD)
    (spec_dir / "REQUIREMENTS.md").write_text(REQUIREMENTS_MD)
    (spec_dir / "DESIGN.md").write_text(DESIGN_MD)

    src_dir = project_dir / "src"
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / "__init__.py").write_text("")
    (src_dir / "converter.py").write_text(BUGGY_CONVERTER)

    tests_dir = project_dir / "tests"
    tests_dir.mkdir(parents=True, exist_ok=True)
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_converter.py").write_text(CORRECT_TESTS)
    (tests_dir / "conftest.py").write_text(
        "import pathlib, sys\nsys.path.insert(0, str(pathlib.Path(__file__).parent.parent))\n"
    )

    for directory in (
        ws / "features" / "active",
        ws / "features" / "completed",
        ws / "tasks" / "active",
        ws / "events",
        ws / "codex" / "context",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    e2e_support._copy_graph_files(ws)
    e2e_support._copy_command_and_agent_specs(project_dir)
    (project_dir / "pyproject.toml").write_text(PYPROJECT_TOML)
    (ws / "codex" / "context" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS)
    (ws / "features" / "active" / f"{FEATURE_ID}.yml").write_text(FEATURE_VECTOR.format(ts=e2e_support._now()))
    (ws / "features" / "feature_index.yml").write_text(
        textwrap.dedent(
            f"""\
            ---
            features:
              - id: "{FEATURE_ID}"
                title: "Repair Temperature Conversion"
                status: in_progress
                profile: standard
                path: "features/active/{FEATURE_ID}.yml"
            """
        )
    )
    (ws / "tasks" / "active" / "ACTIVE_TASKS.md").write_text(f"# Active Tasks\n\n- [ ] {FEATURE_ID}\n")
    (ws / "codex" / "context" / "e2e_homeostasis_driver.py").write_text(HOMEOSTASIS_DRIVER)

    timestamp = e2e_support._now()
    seed_events = [
        {
            "event_type": "project_initialized",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
        },
        {
            "event_type": "edge_started",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "intent→requirements",
        },
        {
            "event_type": "iteration_completed",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "intent→requirements",
            "iteration": 1,
            "delta": 0,
            "status": "converged",
            "evaluators": {"passed": 1, "failed": 0, "skipped": 0, "total": 1},
        },
        {
            "event_type": "edge_converged",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "intent→requirements",
        },
        {
            "event_type": "edge_started",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "requirements→design",
        },
        {
            "event_type": "iteration_completed",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "requirements→design",
            "iteration": 1,
            "delta": 0,
            "status": "converged",
            "evaluators": {"passed": 1, "failed": 0, "skipped": 0, "total": 1},
        },
        {
            "event_type": "edge_converged",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "requirements→design",
        },
        {
            "event_type": "edge_started",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "design→code",
        },
        {
            "event_type": "iteration_completed",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "design→code",
            "iteration": 1,
            "delta": 0,
            "status": "converged",
            "evaluators": {"passed": 1, "failed": 0, "skipped": 0, "total": 1},
        },
        {
            "event_type": "edge_converged",
            "timestamp": timestamp,
            "project": PROJECT_NAME,
            "feature": FEATURE_ID,
            "edge": "design→code",
        },
    ]
    for event in seed_events:
        e2e_support._append_event(ws / "events" / "events.jsonl", event)

    pre_check = subprocess.run(
        ["python", "-m", "pytest", "tests", "-q"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        timeout=30,
        env=e2e_support._clean_env() | {"PYTHONPATH": str(project_dir)},
    )
    assert pre_check.returncode != 0, "Seeded buggy project must fail before Codex runs"

    prompt = textwrap.dedent(
        """\
        Execute this repair loop exactly:
        1. python .ai-workspace/codex/context/e2e_homeostasis_driver.py
        2. If .ai-workspace/codex/context/homeostasis_status.txt says CONVERGED, stop.
        3. Read .ai-workspace/codex/context/homeostasis_failure.json for the actual failing telemetry.
        4. Fix src/converter.py only.
        5. Repeat from step 1 until CONVERGED.

        Constraints:
        - Do not edit tests or the driver.
        - Do not write directly to events.jsonl; only the driver may emit telemetry.
        - The first driver run must happen before any code edits.
        - The first code↔unit_tests iteration must record delta > 0.
        - Stop once pytest passes and edge_converged has been emitted.
        """
    ).strip()

    meta_dir = project_dir / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)
    result = e2e_support.run_codex_headless(
        project_dir,
        prompt,
        model=os.environ.get("CODEX_E2E_MODEL", "gpt-5-codex").strip(),
        wall_timeout=1800.0,
        stall_timeout=300.0,
        log_dir=meta_dir,
    )

    if result.timed_out:
        pytest.fail(
            f"Codex timed out after {result.elapsed:.0f}s.\n"
            f"stdout:\n{result.stdout[-3000:]}\n"
            f"stderr:\n{result.stderr[-1500:]}"
        )
    if result.returncode != 0:
        pytest.fail(
            f"Codex exited with code {result.returncode}.\n"
            f"stdout:\n{result.stdout[-3000:]}\n"
            f"stderr:\n{result.stderr[-1500:]}"
        )
    return project_dir


@pytest.mark.e2e
class TestE2EHomeostasis:
    def test_multi_iteration_convergence(self, homeostasis_result: Path):
        deltas = _deltas(_load_events(homeostasis_result))
        assert len(deltas) > 1, f"Expected >1 iterations on {EDGE}, got {deltas}"
        assert deltas[0] > 0, f"First delta must be > 0, got {deltas}"
        assert deltas[-1] == 0, f"Final delta must be 0, got {deltas}"

    def test_real_telemetry_chain_emitted(self, homeostasis_result: Path):
        events = _load_events(homeostasis_result)
        event_types = [event.get("event_type") for event in events if event.get("edge") == EDGE or event.get("event_type") == "evaluator_detail"]
        assert "edge_started" in event_types
        assert "iteration_completed" in event_types
        assert "evaluator_detail" in event_types
        assert "edge_converged" in event_types

    def test_corrected_code_and_tests_pass(self, homeostasis_result: Path):
        result = subprocess.run(
            ["python", "-m", "pytest", "tests", "-q"],
            cwd=str(homeostasis_result),
            capture_output=True,
            text=True,
            timeout=60,
            env=e2e_support._clean_env() | {"PYTHONPATH": str(homeostasis_result)},
        )
        assert result.returncode == 0, result.stdout + "\n" + result.stderr

        content = (homeostasis_result / "src" / "converter.py").read_text()
        assert "* 2 + 30" not in content
        spec = importlib.util.spec_from_file_location("e2e_converter", homeostasis_result / "src" / "converter.py")
        assert spec is not None and spec.loader is not None
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        assert module.celsius_to_fahrenheit(0) == 32.0
        assert round(module.fahrenheit_to_celsius(212), 6) == 100.0
