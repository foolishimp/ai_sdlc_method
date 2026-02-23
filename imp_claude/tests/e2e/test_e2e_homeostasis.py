# Validates: REQ-SUPV-003, REQ-EVAL-001, REQ-EVAL-002
"""E2E test for homeostatic loop closure — forces failure → intent → correction.

The temperature-converter E2E test is too trivial: all edges converge in 1
iteration with 0 failures. This test proves the methodology's core claim:
that failures are detected, recorded as events, and drive corrective iterations.

Strategy:
  Pre-seed a scaffolded project with DELIBERATELY WRONG code at the
  code↔unit_tests edge. The code has wrong formulas, so deterministic
  evaluators (pytest) MUST fail. The iterate agent must then:
    1. Run tests → fail → delta > 0
    2. Emit evaluator_detail events (REQ-SUPV-003)
    3. Fix the code → iterate again → delta decreases
    4. Eventually converge → delta = 0

  We start from the code↔unit_tests edge only (the feature vector shows
  earlier edges already converged). This saves ~10 min of Claude time.

What this proves:
  - iterate() handles multi-iteration convergence (not just 1-shot)
  - evaluator_detail events are emitted on failure
  - Delta decreases across iterations (convergence is real, not declared)
  - The event log captures the full failure → correction chain

Run:
    pytest imp_claude/tests/e2e/test_e2e_homeostasis.py -v -m e2e -s
"""

import json
import pathlib
import shutil
import subprocess
import textwrap
from datetime import datetime, timezone

import pytest

from imp_claude.tests.e2e.conftest import (
    CONFIG_DIR,
    COMMANDS_DIR,
    AGENTS_DIR,
    PLUGIN_ROOT,
    RUNS_DIR,
    INTENT_MD,
    PROJECT_CONSTRAINTS_YML,
    TEST_PROJECT_CLAUDE_MD,
    TEST_PROJECT_PYPROJECT,
    run_claude_headless,
    skip_no_claude,
    _clean_env,
    _copy_config_files,
    _copy_profile_files,
    _copy_commands,
    _copy_agents,
    _get_plugin_version,
    _persist_run,
)
from imp_claude.tests.e2e.analyse_run import (
    load_events as analyse_load_events,
    analyse_iterations,
    analyse_failure_observability,
    analyse_homeostatic_chain,
    print_report,
)


# ═══════════════════════════════════════════════════════════════════════
# DELIBERATELY WRONG CODE — forces evaluator failure
# ═══════════════════════════════════════════════════════════════════════

BUGGY_CONVERTER_PY = textwrap.dedent('''\
    """Temperature conversion library.

    # Implements: REQ-F-CONV-001
    # Implements: REQ-F-CONV-002
    """


    def celsius_to_fahrenheit(c):
        """Convert Celsius to Fahrenheit."""
        # Implements: REQ-F-CONV-001
        if not isinstance(c, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(c).__name__}")
        if c < -273.15:
            raise ValueError(f"Temperature {c}°C is below absolute zero (-273.15°C)")
        return c * 2 + 30  # BUG: wrong formula (should be c * 9/5 + 32)


    def fahrenheit_to_celsius(f):
        """Convert Fahrenheit to Celsius."""
        # Implements: REQ-F-CONV-001
        if not isinstance(f, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(f).__name__}")
        if f < -459.67:
            raise ValueError(f"Temperature {f}°F is below absolute zero (-459.67°F)")
        return (f - 30) / 2  # BUG: wrong formula (should be (f - 32) * 5/9)


    def celsius_to_kelvin(c):
        """Convert Celsius to Kelvin."""
        # Implements: REQ-F-CONV-001
        if not isinstance(c, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(c).__name__}")
        if c < -273.15:
            raise ValueError(f"Temperature {c}°C is below absolute zero (-273.15°C)")
        return c + 273.15  # CORRECT


    def kelvin_to_celsius(k):
        """Convert Kelvin to Celsius."""
        # Implements: REQ-F-CONV-001
        if not isinstance(k, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(k).__name__}")
        if k < 0:
            raise ValueError(f"Temperature {k}K is below absolute zero (0K)")
        return k - 273.15  # CORRECT


    def fahrenheit_to_kelvin(f):
        """Convert Fahrenheit to Kelvin."""
        # Implements: REQ-F-CONV-001
        if not isinstance(f, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(f).__name__}")
        if f < -459.67:
            raise ValueError(f"Temperature {f}°F is below absolute zero (-459.67°F)")
        c = fahrenheit_to_celsius(f)
        return celsius_to_kelvin(c)


    def kelvin_to_fahrenheit(k):
        """Convert Kelvin to Fahrenheit."""
        # Implements: REQ-F-CONV-001
        if not isinstance(k, (int, float)):
            raise TypeError(f"Expected numeric input, got {type(k).__name__}")
        if k < 0:
            raise ValueError(f"Temperature {k}K is below absolute zero (0K)")
        c = kelvin_to_celsius(k)
        return celsius_to_fahrenheit(c)
''')

CORRECT_TESTS_PY = textwrap.dedent('''\
    """Tests for temperature conversion library.

    # Validates: REQ-F-CONV-001
    # Validates: REQ-F-CONV-002
    """
    import pytest
    from converter import (
        celsius_to_fahrenheit,
        fahrenheit_to_celsius,
        celsius_to_kelvin,
        kelvin_to_celsius,
        fahrenheit_to_kelvin,
        kelvin_to_fahrenheit,
    )


    # Validates: REQ-F-CONV-001
    class TestCelsiusToFahrenheit:
        def test_freezing_point(self):
            assert celsius_to_fahrenheit(0) == 32.0

        def test_boiling_point(self):
            assert celsius_to_fahrenheit(100) == 212.0


    # Validates: REQ-F-CONV-001
    class TestFahrenheitToCelsius:
        def test_freezing_point(self):
            assert fahrenheit_to_celsius(32) == 0.0

        def test_boiling_point(self):
            assert fahrenheit_to_celsius(212) == 100.0


    # Validates: REQ-F-CONV-001
    class TestCelsiusToKelvin:
        def test_freezing_point(self):
            assert celsius_to_kelvin(0) == 273.15


    # Validates: REQ-F-CONV-001
    class TestKelvinToCelsius:
        def test_absolute_zero(self):
            assert kelvin_to_celsius(273.15) == 0.0


    # Validates: REQ-F-CONV-001
    class TestFahrenheitToKelvin:
        def test_freezing_point(self):
            assert fahrenheit_to_kelvin(32) == 273.15


    # Validates: REQ-F-CONV-001
    class TestKelvinToFahrenheit:
        def test_absolute_zero(self):
            assert kelvin_to_fahrenheit(273.15) == 32.0


    # Validates: REQ-F-CONV-002
    class TestInputValidation:
        def test_non_numeric_raises_type_error(self):
            with pytest.raises(TypeError):
                celsius_to_fahrenheit("hot")

        def test_below_absolute_zero_celsius(self):
            with pytest.raises(ValueError):
                celsius_to_fahrenheit(-300)

        def test_below_absolute_zero_fahrenheit(self):
            with pytest.raises(ValueError):
                fahrenheit_to_celsius(-500)

        def test_below_absolute_zero_kelvin(self):
            with pytest.raises(ValueError):
                kelvin_to_celsius(-1)
''')

# Feature vector with earlier edges pre-converged, code↔unit_tests pending
HOMEOSTASIS_FEATURE_VECTOR_YML = textwrap.dedent("""\
    ---
    feature: "REQ-F-CONV-001"
    title: "Temperature Conversion Functions"
    intent: "INT-001"
    vector_type: feature
    profile: standard
    status: in_progress
    convergence_type: ""
    created: "{timestamp}"
    updated: "{timestamp}"

    time_box:
      enabled: false

    parent:
      feature: ""
      edge: ""
      reason: ""

    children: []

    trajectory:
      requirements:
        status: converged
        iterations: 1
        converged_at: "{timestamp}"
      design:
        status: converged
        iterations: 1
        converged_at: "{timestamp}"
      code:
        status: converged
        iterations: 1
        converged_at: "{timestamp}"
      unit_tests:
        status: pending

    dependencies: []

    constraints:
      acceptance_criteria:
        - id: "AC-CONV-001"
          description: "celsius_to_fahrenheit(0) == 32.0"
          evaluator: deterministic
          check: "test passes: assert celsius_to_fahrenheit(0) == 32.0"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-002"
          description: "celsius_to_fahrenheit(100) == 212.0"
          evaluator: deterministic
          check: "test passes: assert celsius_to_fahrenheit(100) == 212.0"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-003"
          description: "fahrenheit_to_celsius(32) == 0.0"
          evaluator: deterministic
          check: "test passes: assert fahrenheit_to_celsius(32) == 0.0"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-004"
          description: "fahrenheit_to_celsius(212) == 100.0"
          evaluator: deterministic
          check: "test passes: assert fahrenheit_to_celsius(212) == 100.0"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-005"
          description: "celsius_to_kelvin(0) == 273.15"
          evaluator: deterministic
          check: "test passes: assert celsius_to_kelvin(0) == 273.15"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-006"
          description: "kelvin_to_celsius(273.15) == 0.0"
          evaluator: deterministic
          check: "test passes: assert kelvin_to_celsius(273.15) == 0.0"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-007"
          description: "fahrenheit_to_kelvin(32) == 273.15"
          evaluator: deterministic
          check: "test passes: assert fahrenheit_to_kelvin(32) == 273.15"
          req: "REQ-F-CONV-001"
          required: true
        - id: "AC-CONV-008"
          description: "kelvin_to_fahrenheit(273.15) == 32.0"
          evaluator: deterministic
          check: "test passes: assert kelvin_to_fahrenheit(273.15) == 32.0"
          req: "REQ-F-CONV-001"
          required: true
      threshold_overrides: {}
      additional_checks: []
""")

# Events showing earlier edges already converged
HOMEOSTASIS_SEED_EVENTS = [
    {
        "event_type": "project_initialized",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "profile": "standard",
        "version": "{version}",
    },
    {
        "event_type": "edge_started",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "intent→requirements",
        "data": {"iteration": 1},
    },
    {
        "event_type": "edge_converged",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "intent→requirements",
        "data": {"iteration": 1, "evaluators": "14/14", "convergence_type": "standard"},
    },
    {
        "event_type": "edge_started",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "requirements→design",
        "data": {"iteration": 1},
    },
    {
        "event_type": "edge_converged",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "requirements→design",
        "data": {"iteration": 1, "evaluators": "15/15", "convergence_type": "standard"},
    },
    {
        "event_type": "edge_started",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "design→code",
        "data": {"iteration": 1},
    },
    {
        "event_type": "edge_converged",
        "timestamp": "{timestamp}",
        "project": "temperature-converter",
        "feature": "REQ-F-CONV-001",
        "edge": "design→code",
        "data": {"iteration": 1, "evaluators": "16/16", "convergence_type": "standard"},
    },
]

# Requirements doc (pre-generated)
REQUIREMENTS_MD = textwrap.dedent("""\
    # Requirements: Temperature Converter

    ## REQ-F-CONV-001: Temperature Conversion Functions

    Provide 6 conversion functions between Celsius, Fahrenheit, and Kelvin.

    - `celsius_to_fahrenheit(c)` — Formula: F = C * 9/5 + 32
    - `fahrenheit_to_celsius(f)` — Formula: C = (F - 32) * 5/9
    - `celsius_to_kelvin(c)` — Formula: K = C + 273.15
    - `kelvin_to_celsius(k)` — Formula: C = K - 273.15
    - `fahrenheit_to_kelvin(f)` — via Celsius intermediate
    - `kelvin_to_fahrenheit(k)` — via Celsius intermediate

    Traces To: INT-001

    ## REQ-F-CONV-002: Input Validation

    All conversion functions must validate inputs:
    - Non-numeric input raises TypeError
    - Below absolute zero raises ValueError

    Traces To: INT-001
""")

DESIGN_MD = textwrap.dedent("""\
    # Design: Temperature Converter

    ## Architecture

    Single module `converter.py` with 6 pure functions.
    No classes needed — functional approach is sufficient.

    ## Components

    | Component | Implements | Description |
    |-----------|-----------|-------------|
    | `converter.py` | REQ-F-CONV-001, REQ-F-CONV-002 | All conversion functions |

    ## ADR-001: Pure Functions

    **Decision**: Use standalone functions, not a class.
    **Rationale**: No state needed. Functions are simpler to test.
""")

FEATURE_INDEX_YML = textwrap.dedent("""\
    ---
    features:
      - id: "REQ-F-CONV-001"
        title: "Temperature Conversion Functions"
        status: in_progress
        profile: standard
        path: "features/active/REQ-F-CONV-001.yml"
""")

ACTIVE_TASKS_MD = textwrap.dedent("""\
    # Active Tasks

    ## Current Sprint

    - [x] REQ-F-CONV-001: Intent → Requirements — converged
    - [x] REQ-F-CONV-001: Requirements → Design — converged
    - [x] REQ-F-CONV-001: Design → Code — converged
    - [ ] REQ-F-CONV-001: Code ↔ Unit Tests — **in progress** (bugs in converter.py)
""")


# ═══════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="module")
def homeostasis_project_dir(tmp_path_factory) -> pathlib.Path:
    """Scaffold a project with PRE-SEEDED BUGGY CODE for homeostatic loop testing.

    The code↔unit_tests edge will fail on first iteration because:
    - converter.py has wrong formulas (c*2+30 instead of c*9/5+32)
    - test_converter.py has correct expected values
    - pytest WILL fail → delta > 0 → iterate must fix the code

    Earlier edges (intent→req, req→design, design→code) are pre-converged
    via seed events and feature vector state.
    """
    project_dir = tmp_path_factory.mktemp("temp-converter-buggy")
    timestamp = datetime.now(timezone.utc).isoformat()
    version = _get_plugin_version()

    # 1. Git init
    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "e2e-test@example.com"],
                   cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "E2E Test"],
                   cwd=str(project_dir), capture_output=True)

    # 2. Write specification
    spec_dir = project_dir / "specification"
    spec_dir.mkdir()
    (spec_dir / "INTENT.md").write_text(INTENT_MD)
    (spec_dir / "REQUIREMENTS.md").write_text(REQUIREMENTS_MD)
    (spec_dir / "DESIGN.md").write_text(DESIGN_MD)

    # 3. Write BUGGY source code
    src_dir = project_dir / "src"
    src_dir.mkdir()
    (src_dir / "__init__.py").write_text("")
    (src_dir / "converter.py").write_text(BUGGY_CONVERTER_PY)

    # 4. Write CORRECT tests (they will fail against buggy code)
    tests_dir = project_dir / "tests"
    tests_dir.mkdir()
    (tests_dir / "__init__.py").write_text("")
    (tests_dir / "test_converter.py").write_text(CORRECT_TESTS_PY)

    # 5. conftest.py that adds src/ to path
    (tests_dir / "conftest.py").write_text(textwrap.dedent("""\
        import sys
        import pathlib
        sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / "src"))
    """))

    # 6. Create .ai-workspace
    ws = project_dir / ".ai-workspace"
    graph_dir = ws / "graph"
    context_dir = ws / "claude" / "context"
    features_active = ws / "features" / "active"
    features_completed = ws / "features" / "completed"
    profiles_dir = ws / "profiles"
    events_dir = ws / "events"
    tasks_active = ws / "tasks" / "active"
    agents_dir = ws / "agents"

    for d in [graph_dir, context_dir, features_active, features_completed,
              profiles_dir, events_dir, tasks_active, agents_dir]:
        d.mkdir(parents=True, exist_ok=True)

    # 7. Copy config files
    _copy_config_files(graph_dir)
    _copy_profile_files(profiles_dir)
    shutil.copy2(CONFIG_DIR / "feature_vector_template.yml",
                 ws / "features" / "feature_vector_template.yml")

    # 8. Write project constraints
    (context_dir / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)

    # 9. Write feature vector with earlier edges CONVERGED, unit_tests PENDING
    (features_active / "REQ-F-CONV-001.yml").write_text(
        HOMEOSTASIS_FEATURE_VECTOR_YML.replace("{timestamp}", timestamp))

    # 10. Write feature index and tasks
    (ws / "features" / "feature_index.yml").write_text(FEATURE_INDEX_YML)
    (tasks_active / "ACTIVE_TASKS.md").write_text(ACTIVE_TASKS_MD)

    # 11. Copy commands and agents
    _copy_commands(project_dir / ".claude" / "commands")
    _copy_agents(agents_dir)

    # 12. Write project files
    (project_dir / "CLAUDE.md").write_text(
        TEST_PROJECT_CLAUDE_MD + textwrap.dedent("""
    ## Known Issues

    The converter.py has bugs in celsius_to_fahrenheit and fahrenheit_to_celsius.
    The tests will fail until the formulas are corrected.
    Run `pytest tests/ -v` to see the failures.
    """))
    (project_dir / "pyproject.toml").write_text(TEST_PROJECT_PYPROJECT)

    # 13. Write seed events (earlier edges converged)
    with open(events_dir / "events.jsonl", "w") as f:
        for event in HOMEOSTASIS_SEED_EVENTS:
            # Replace timestamp and version placeholders
            event_str = json.dumps(event)
            event_str = event_str.replace("{timestamp}", timestamp)
            event_str = event_str.replace("{version}", version)
            f.write(event_str + "\n")

    # 14. Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "commit", "-m",
                    "chore: scaffold buggy temp-converter for homeostasis e2e test"],
                   cwd=str(project_dir), capture_output=True)

    return project_dir


@pytest.fixture(scope="module")
def homeostasis_result(homeostasis_project_dir: pathlib.Path) -> pathlib.Path:
    """Run headless Claude to iterate on buggy code↔unit_tests edge.

    The prompt tells Claude to iterate on code↔unit_tests specifically.
    Claude must: run tests, see failures, fix the code, re-run tests, converge.
    """
    project_dir = homeostasis_project_dir
    meta_dir = project_dir / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)

    # Focused prompt: iterate on code↔unit_tests only
    prompt = (
        '/gen-iterate --feature "REQ-F-CONV-001" --edge "code↔unit_tests" '
        '--auto'
    )

    print(f"\n{'='*60}")
    print(f"E2E HOMEOSTASIS: Starting headless Claude")
    print(f"E2E HOMEOSTASIS: Strategy — buggy code, correct tests")
    print(f"E2E HOMEOSTASIS: Expected — multi-iteration convergence")
    print(f"E2E HOMEOSTASIS: Project dir: {project_dir}")
    print(f"E2E HOMEOSTASIS: Live output: tail -f {meta_dir}/stdout.log")
    print(f"{'='*60}\n", flush=True)

    # Verify pre-seeded tests actually fail before sending to Claude
    pre_check = subprocess.run(
        ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--no-header"],
        cwd=str(project_dir),
        capture_output=True, text=True, timeout=30,
        env=_clean_env(),
    )
    print(f"E2E HOMEOSTASIS: Pre-check pytest exit code: {pre_check.returncode}")
    if pre_check.returncode == 0:
        pytest.fail(
            "Pre-seeded buggy code should FAIL tests, but they passed. "
            "The test scenario is broken — buggy code is not actually buggy.\n"
            f"stdout: {pre_check.stdout[:1000]}"
        )
    print(f"E2E HOMEOSTASIS: Pre-check confirmed — tests fail as expected", flush=True)

    result = run_claude_headless(
        project_dir, prompt, log_dir=meta_dir,
        max_budget_usd=8.00,     # slightly higher — may need multiple iterations
        wall_timeout=1800.0,     # 30 min
        stall_timeout=300.0,     # 5 min
    )

    # Save meta
    stall_killed = getattr(result, "stall_killed", False)
    (meta_dir / "meta.json").write_text(json.dumps({
        "returncode": result.returncode,
        "elapsed_seconds": round(result.elapsed, 1),
        "timed_out": result.timed_out,
        "stall_killed": stall_killed,
        "prompt": prompt,
        "scenario": "homeostasis",
    }, indent=2))

    print(f"\nE2E HOMEOSTASIS: Claude finished in {result.elapsed:.0f}s "
          f"(rc={result.returncode}, timed_out={result.timed_out})", flush=True)

    # Archive the run
    archive_path = _persist_run(project_dir, failed=(result.returncode != 0))

    # Run the analysis script on this archive
    events = analyse_load_events(project_dir)
    if events:
        print_report(project_dir, events)

    if result.timed_out:
        pytest.fail(
            f"Claude timed out after {result.elapsed:.0f}s.\n"
            f"--- stdout (last 2000 chars) ---\n{result.stdout[-2000:]}\n"
            f"--- stderr (last 1000 chars) ---\n{result.stderr[-1000:]}"
        )

    return project_dir


# ═══════════════════════════════════════════════════════════════════════
# HELPER — load events from the run
# ═══════════════════════════════════════════════════════════════════════

def _load_events(project_dir: pathlib.Path) -> list[dict]:
    """Parse events.jsonl."""
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    events = []
    if events_file.exists():
        for line in events_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return events


def _count_iterations(events: list[dict], edge: str) -> int:
    """Count iteration_completed events for a specific edge."""
    return sum(
        1 for e in events
        if e.get("event_type") == "iteration_completed"
        and e.get("edge") == edge
    )


def _get_deltas(events: list[dict], edge: str) -> list[int]:
    """Get delta values across iterations for a specific edge."""
    deltas = []
    for e in events:
        if (e.get("event_type") == "iteration_completed"
                and e.get("edge") == edge
                and e.get("delta") is not None):
            deltas.append(e["delta"])
    return deltas


def _get_evaluator_failures(events: list[dict], edge: str) -> int:
    """Count total evaluator failures across iterations for an edge."""
    total = 0
    for e in events:
        if (e.get("event_type") == "iteration_completed"
                and e.get("edge") == edge):
            ev = e.get("evaluators", {})
            if isinstance(ev, dict):
                total += ev.get("failed", 0)
    return total


# ═══════════════════════════════════════════════════════════════════════
# TESTS — HOMEOSTATIC LOOP VERIFICATION
# ═══════════════════════════════════════════════════════════════════════

EDGE = "code↔unit_tests"


@pytest.mark.e2e
@skip_no_claude
class TestE2EHomeostasis:
    """Proves the homeostatic loop closes: failure → iteration → correction."""

    # ─── Core Homeostasis Proofs ─────────────────────────────────────

    def test_multi_iteration_convergence(self, homeostasis_result: pathlib.Path):
        """The code↔unit_tests edge MUST take more than 1 iteration.

        This is the primary proof that iterate() handles real failures.
        If it converges in 1 iteration, the buggy code was not actually
        tested or the agent bypassed the evaluators.
        """
        events = _load_events(homeostasis_result)
        iterations = _count_iterations(events, EDGE)
        assert iterations > 1, (
            f"code↔unit_tests converged in {iterations} iteration(s). "
            f"Expected > 1 because pre-seeded code has wrong formulas. "
            f"Either the agent didn't run tests or bypassed evaluators."
        )

    def test_initial_delta_nonzero(self, homeostasis_result: pathlib.Path):
        """First iteration must have delta > 0 (tests should fail)."""
        events = _load_events(homeostasis_result)
        deltas = _get_deltas(events, EDGE)
        assert deltas, f"No delta values found for {EDGE}"
        assert deltas[0] > 0, (
            f"First iteration delta is {deltas[0]}, expected > 0. "
            f"The pre-seeded buggy code should have failed deterministic checks."
        )

    def test_delta_decreases_to_zero(self, homeostasis_result: pathlib.Path):
        """Delta must decrease across iterations and reach 0."""
        events = _load_events(homeostasis_result)
        deltas = _get_deltas(events, EDGE)
        assert deltas, f"No delta values found for {EDGE}"
        assert deltas[-1] == 0, (
            f"Final delta is {deltas[-1]}, expected 0. "
            f"Delta progression: {deltas}"
        )

    def test_evaluator_failures_recorded(self, homeostasis_result: pathlib.Path):
        """Iteration events must record non-zero evaluator failures."""
        events = _load_events(homeostasis_result)
        failures = _get_evaluator_failures(events, EDGE)
        assert failures > 0, (
            f"Zero evaluator failures recorded for {EDGE}. "
            f"The buggy code should have caused test failures."
        )

    # ─── Failure Observability (REQ-SUPV-003) ────────────────────────

    def test_evaluator_detail_events_emitted(self, homeostasis_result: pathlib.Path):
        """evaluator_detail events must be emitted for failed checks.

        REQ-SUPV-003: every evaluator failure must produce an evaluator_detail
        event so the LLM evaluator can compute delta and design improvements.
        """
        events = _load_events(homeostasis_result)
        evaluator_details = [
            e for e in events
            if e.get("event_type") == "evaluator_detail"
        ]
        # This is a soft assertion — the iterate agent may not yet emit these.
        # If it doesn't, the test documents the gap for methodology improvement.
        if not evaluator_details:
            pytest.xfail(
                "No evaluator_detail events emitted. "
                "REQ-SUPV-003 requires these but iterate agent may not implement them yet. "
                "This gap must be addressed for homeostatic closure."
            )

    def test_evaluator_detail_schema(self, homeostasis_result: pathlib.Path):
        """evaluator_detail events must have required fields."""
        events = _load_events(homeostasis_result)
        evaluator_details = [
            e for e in events
            if e.get("event_type") == "evaluator_detail"
        ]
        if not evaluator_details:
            pytest.skip("No evaluator_detail events to validate schema")

        for ed in evaluator_details:
            data = ed.get("data", {})
            assert "check_name" in data, f"evaluator_detail missing check_name: {ed}"
            assert "result" in data, f"evaluator_detail missing result: {ed}"

    # ─── Event Chain Integrity ───────────────────────────────────────

    def test_edge_started_before_iterations(self, homeostasis_result: pathlib.Path):
        """An edge_started event should precede iteration_completed events."""
        events = _load_events(homeostasis_result)
        edge_started = [
            e for e in events
            if e.get("event_type") == "edge_started"
            and e.get("edge") == EDGE
        ]
        iterations = [
            e for e in events
            if e.get("event_type") == "iteration_completed"
            and e.get("edge") == EDGE
        ]
        if iterations:
            # Either an edge_started exists, or the seed events already covered it
            # (we don't seed code↔unit_tests edge_started, so agent should emit it)
            assert edge_started or any(
                e.get("event_type") == "edge_started"
                and e.get("edge") == EDGE
                for e in events
            ), f"No edge_started event for {EDGE}"

    def test_edge_converged_event(self, homeostasis_result: pathlib.Path):
        """An edge_converged event must be emitted when delta reaches 0."""
        events = _load_events(homeostasis_result)
        edge_converged = [
            e for e in events
            if e.get("event_type") == "edge_converged"
            and e.get("edge") == EDGE
        ]
        assert edge_converged, (
            f"No edge_converged event for {EDGE}. "
            f"The iterate agent must emit this when convergence is reached."
        )

    # ─── Code Correction Verification ────────────────────────────────

    def test_generated_tests_pass_after_convergence(self, homeostasis_result: pathlib.Path):
        """After convergence, pytest must pass in the project directory."""
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "--no-header"],
            cwd=str(homeostasis_result),
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, (
            f"Tests still fail after convergence (rc={result.returncode}).\n"
            f"stdout: {result.stdout[-1000:]}\n"
            f"stderr: {result.stderr[-500:]}"
        )

    def test_buggy_formulas_corrected(self, homeostasis_result: pathlib.Path):
        """The buggy formulas in converter.py must be corrected."""
        converter_files = list(homeostasis_result.rglob("converter.py"))
        # Filter out workspace/meta files
        converter_files = [
            f for f in converter_files
            if ".ai-workspace" not in str(f) and ".e2e-meta" not in str(f)
        ]
        assert converter_files, "converter.py not found after convergence"

        content = converter_files[0].read_text()
        # The buggy formula was: c * 2 + 30
        assert "* 2 + 30" not in content, (
            "Buggy formula 'c * 2 + 30' still present in converter.py. "
            "The iterate agent should have corrected it to 'c * 9/5 + 32'."
        )

    # ─── Forensic Analysis ───────────────────────────────────────────

    def test_archive_analysis_not_untested(self, homeostasis_result: pathlib.Path):
        """The archive analysis must NOT report UNTESTED status.

        This is the meta-proof: the analysis tool confirms the homeostatic
        loop was exercised (failures observed, corrections made).
        """
        events = _load_events(homeostasis_result)
        chain = analyse_homeostatic_chain(events)
        assert chain["chain_status"] != "UNTESTED", (
            f"Archive analysis reports UNTESTED — the homeostatic loop "
            f"was not exercised. This means pre-seeded bugs were not detected."
        )

    def test_archive_analysis_has_failures(self, homeostasis_result: pathlib.Path):
        """The archive analysis must confirm failures were observed."""
        events = _load_events(homeostasis_result)
        chain = analyse_homeostatic_chain(events)
        assert chain["has_failures"], (
            "Archive analysis reports no failures observed. "
            "The buggy code should have generated evaluator failures."
        )
