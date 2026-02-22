# Validates: REQ-TOOL-005, REQ-EVAL-001
"""Fixtures and content templates for E2E convergence tests.

Session-scoped: Claude runs ONCE, all tests validate the same output.
Uses subprocess with wall timeout and budget cap (--max-budget-usd).
"""

import json
import os
import pathlib
import shutil
import subprocess
import textwrap
import threading
import time

import pytest

# ═══════════════════════════════════════════════════════════════════════
# PATH CONSTANTS
# ═══════════════════════════════════════════════════════════════════════

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
PLUGIN_ROOT = (
    PROJECT_ROOT
    / "imp_claude"
    / "code"
    / ".claude-plugin"
    / "plugins"
    / "aisdlc-methodology"
    / "v2"
)
CONFIG_DIR = PLUGIN_ROOT / "config"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"

# ═══════════════════════════════════════════════════════════════════════
# CONTENT TEMPLATES
# ═══════════════════════════════════════════════════════════════════════

INTENT_MD = textwrap.dedent("""\
    # Intent: Temperature Converter Library

    ## Problem Statement

    We need a Python library that converts between Celsius, Fahrenheit,
    and Kelvin temperature scales. The library must be correct, well-tested,
    and provide clear error messages for invalid inputs.

    ## Requirements

    ### REQ-F-CONV-001: Temperature Conversion Functions

    Provide 6 conversion functions:
    - `celsius_to_fahrenheit(c)` — Formula: F = C * 9/5 + 32
    - `fahrenheit_to_celsius(f)` — Formula: C = (F - 32) * 5/9
    - `celsius_to_kelvin(c)` — Formula: K = C + 273.15
    - `kelvin_to_celsius(k)` — Formula: C = K - 273.15
    - `fahrenheit_to_kelvin(f)` — via Celsius intermediate
    - `kelvin_to_fahrenheit(k)` — via Celsius intermediate

    Acceptance criteria:
    - celsius_to_fahrenheit(0) == 32.0
    - celsius_to_fahrenheit(100) == 212.0
    - fahrenheit_to_celsius(32) == 0.0
    - fahrenheit_to_celsius(212) == 100.0
    - celsius_to_kelvin(0) == 273.15
    - kelvin_to_celsius(273.15) == 0.0
    - fahrenheit_to_kelvin(32) == 273.15
    - kelvin_to_fahrenheit(273.15) == 32.0

    ### REQ-F-CONV-002: Input Validation

    All conversion functions must validate inputs:
    - Non-numeric input raises TypeError with descriptive message
    - Below absolute zero raises ValueError:
      - Celsius below -273.15
      - Fahrenheit below -459.67
      - Kelvin below 0

    ## Scope

    - Pure Python, no external dependencies
    - Single module
    - 100% test coverage for conversion logic
""")

PROJECT_CONSTRAINTS_YML = textwrap.dedent("""\
    ---
    project:
      name: "temperature-converter"
      version: "0.1.0"
      default_profile: standard

    context_sources: []

    language:
      primary: python
      version: "3.12"
      secondary: []

    tools:
      syntax_checker:
        command: "python -m py_compile"
        args: ""
        pass_criterion: "exit code 0"
      test_runner:
        command: "pytest"
        args: "-v --tb=short"
        pass_criterion: "exit code 0"
      coverage:
        command: "pytest"
        args: "--cov --cov-report=term-missing"
        pass_criterion: "coverage percentage >= $thresholds.test_coverage_minimum"
      linter:
        required: false
        command: "ruff check"
        args: "."
        pass_criterion: "exit code 0, zero violations"
      formatter:
        required: false
        command: "ruff format"
        args: "--check ."
        pass_criterion: "exit code 0"
      type_checker:
        required: false
        command: "mypy"
        args: "--strict src/"
        pass_criterion: "exit code 0"

    thresholds:
      test_coverage_minimum: 0.80
      test_coverage_target: 1.00
      critical_path_coverage: 1.00
      max_function_complexity: 10
      max_function_lines: 50
      max_class_lines: 300
      test_execution_timeout_seconds: 30

    standards:
      style_guide: "PEP 8"
      docstrings: recommended
      type_hints: recommended
      test_structure: "AAA"
      req_tag_format:
        code: "Implements: REQ-F-CONV-{SEQ}"
        tests: "Validates: REQ-F-CONV-{SEQ}"

    constraint_dimensions:
      ecosystem_compatibility:
        language: "python"
        version: "3.12"
        runtime: ""
        frameworks: []
        compatibility_notes: "Pure Python, no external dependencies"
      deployment_target:
        platform: "library"
        cloud_provider: ""
        environment_tiers: []
        notes: "Distributed as a Python package"
      security_model:
        authentication: ""
        authorisation: ""
        data_protection: ""
        compliance: []
        notes: "Not applicable — pure computation library"
      build_system:
        tool: "pip"
        module_structure: "single-module"
        ci_integration: ""
        notes: "Simple pyproject.toml"

    architecture:
      patterns: []
      dependency_rules:
        - "No external dependencies"
      forbidden:
        - "Global mutable state"

    evaluator_overrides:
      edges:
        "intent→requirements":
          evaluators: [agent]
        "requirements→design":
          evaluators: [agent]
        "design→uat_tests":
          evaluators: [agent]
""")

FEATURE_VECTOR_YML = textwrap.dedent("""\
    ---
    feature: "REQ-F-CONV-001"
    title: "Temperature Conversion Functions"
    intent: "INT-001"
    vector_type: feature
    profile: standard
    status: pending
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
        status: pending
      design:
        status: pending
      code:
        status: pending
      unit_tests:
        status: pending
      uat_tests:
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

FEATURE_INDEX_YML = textwrap.dedent("""\
    ---
    features:
      - id: "REQ-F-CONV-001"
        title: "Temperature Conversion Functions"
        status: pending
        profile: standard
        path: "features/active/REQ-F-CONV-001.yml"
""")

ACTIVE_TASKS_MD = textwrap.dedent("""\
    # Active Tasks

    ## Current Sprint

    - [ ] REQ-F-CONV-001: Temperature Conversion Functions — pending
""")

TEST_PROJECT_CLAUDE_MD = textwrap.dedent("""\
    # CLAUDE.md — Temperature Converter

    ## Project Overview

    A Python library for temperature conversions between Celsius, Fahrenheit, and Kelvin.

    ## Structure

    ```
    src/                    # Source code
    tests/                  # Test files
    specification/INTENT.md # Requirements
    .ai-workspace/          # Methodology workspace
    ```

    ## Commands

    ```bash
    # Run tests
    pytest tests/ -v

    # Check syntax
    python -m py_compile src/*.py
    ```

    ## Requirements

    - REQ-F-CONV-001: 6 conversion functions with exact mathematical formulas
    - REQ-F-CONV-002: Input validation (TypeError for non-numeric, ValueError for below absolute zero)

    ## Development

    - Pure Python, no external dependencies
    - Tag code with `# Implements: REQ-F-CONV-*`
    - Tag tests with `# Validates: REQ-F-CONV-*`
""")

TEST_PROJECT_PYPROJECT = textwrap.dedent("""\
    [project]
    name = "temperature-converter"
    version = "0.1.0"
    requires-python = ">=3.10"

    [tool.pytest.ini_options]
    testpaths = ["tests"]
""")


# ═══════════════════════════════════════════════════════════════════════
# SKIP GUARDS
# ═══════════════════════════════════════════════════════════════════════

def _clean_env() -> dict[str, str]:
    """Return env dict with CLAUDECODE unset (allows nested invocation).

    The claude CLI checks for CLAUDECODE in the environment and refuses to
    start if set (nesting guard). When running e2e tests from within a Claude
    Code session, we must strip this variable.
    """
    env = os.environ.copy()
    env.pop("CLAUDECODE", None)
    return env


def _claude_cli_available() -> bool:
    """Check if claude CLI is installed."""
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=10,
            env=_clean_env(),
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


skip_no_claude = pytest.mark.skipif(
    not _claude_cli_available(),
    reason="Claude CLI not installed",
)


# ═══════════════════════════════════════════════════════════════════════
# HELPERS — SCAFFOLDING
# ═══════════════════════════════════════════════════════════════════════

def _copy_config_files(dest_graph_dir: pathlib.Path) -> None:
    """Copy graph topology, evaluator defaults, edge params, and profiles."""
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", dest_graph_dir / "graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", dest_graph_dir / "evaluator_defaults.yml")
    edges_dir = dest_graph_dir / "edges"
    edges_dir.mkdir(parents=True, exist_ok=True)
    for yml in (CONFIG_DIR / "edge_params").glob("*.yml"):
        shutil.copy2(yml, edges_dir / yml.name)


def _copy_profile_files(dest_profiles_dir: pathlib.Path) -> None:
    dest_profiles_dir.mkdir(parents=True, exist_ok=True)
    for yml in (CONFIG_DIR / "profiles").glob("*.yml"):
        shutil.copy2(yml, dest_profiles_dir / yml.name)


def _copy_commands(dest_commands_dir: pathlib.Path) -> None:
    dest_commands_dir.mkdir(parents=True, exist_ok=True)
    for md in COMMANDS_DIR.glob("*.md"):
        shutil.copy2(md, dest_commands_dir / md.name)


def _copy_agents(dest_dir: pathlib.Path) -> None:
    dest_dir.mkdir(parents=True, exist_ok=True)
    for md in AGENTS_DIR.glob("*.md"):
        shutil.copy2(md, dest_dir / md.name)


def _write_initial_event(events_file: pathlib.Path, project_name: str) -> None:
    from datetime import datetime, timezone
    event = {
        "event_type": "project_initialized",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "project": project_name,
        "profile": "standard",
        "version": "2.8.0",
    }
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "w") as f:
        f.write(json.dumps(event) + "\n")


# ═══════════════════════════════════════════════════════════════════════
# HEADLESS RUNNER — SUBPROCESS WITH WALL TIMEOUT + BUDGET CAP
# ═══════════════════════════════════════════════════════════════════════

class ClaudeRunResult:
    """Result of a headless Claude run."""

    def __init__(self, *, returncode: int, elapsed: float,
                 timed_out: bool = False, log_dir: pathlib.Path | None = None):
        self.returncode = returncode
        self.elapsed = elapsed
        self.timed_out = timed_out
        self.log_dir = log_dir

    @property
    def stdout(self) -> str:
        if self.log_dir and (self.log_dir / "stdout.log").exists():
            return (self.log_dir / "stdout.log").read_text(errors="replace")
        return ""

    @property
    def stderr(self) -> str:
        if self.log_dir and (self.log_dir / "stderr.log").exists():
            return (self.log_dir / "stderr.log").read_text(errors="replace")
        return ""


def run_claude_headless(
    project_dir: pathlib.Path,
    prompt: str,
    *,
    model: str = "sonnet",
    max_budget_usd: float = 5.00,
    wall_timeout: float = 1800.0,
    log_dir: pathlib.Path | None = None,
) -> ClaudeRunResult:
    """Run claude -p with wall timeout and budget cap.

    Note: claude -p buffers all output until completion, so stall detection
    based on output bytes doesn't work. We rely on --max-budget-usd + wall_timeout.
    Strips CLAUDECODE env var to allow nested invocation.
    """
    if log_dir is None:
        log_dir = project_dir / ".e2e-meta"
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = log_dir / "stdout.log"
    stderr_log = log_dir / "stderr.log"

    cmd = [
        "claude", "-p",
        "--model", model,
        "--max-budget-usd", str(max_budget_usd),
        "--dangerously-skip-permissions",
        prompt,
    ]

    env = _clean_env()
    start = time.time()
    timed_out = False

    with open(stdout_log, "w") as f_out, open(stderr_log, "w") as f_err:
        proc = subprocess.Popen(
            cmd, cwd=str(project_dir),
            stdout=f_out, stderr=f_err,
            text=True, env=env,
        )

        def watchdog():
            nonlocal timed_out
            while proc.poll() is None:
                time.sleep(10)
                if time.time() - start > wall_timeout:
                    timed_out = True
                    proc.kill()
                    return

        watcher = threading.Thread(target=watchdog, daemon=True)
        watcher.start()
        proc.wait()
        watcher.join(timeout=5)

    elapsed = time.time() - start
    return ClaudeRunResult(
        returncode=proc.returncode,
        elapsed=elapsed,
        timed_out=timed_out,
        log_dir=log_dir,
    )


# ═══════════════════════════════════════════════════════════════════════
# SESSION-SCOPED FIXTURES
# ═══════════════════════════════════════════════════════════════════════

@pytest.fixture(scope="session")
def e2e_project_dir(tmp_path_factory) -> pathlib.Path:
    """Create a fully scaffolded test project for Claude to converge."""
    from datetime import datetime, timezone

    project_dir = tmp_path_factory.mktemp("temperature-converter")
    timestamp = datetime.now(timezone.utc).isoformat()

    # 1. Git init + config
    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, check=True)
    subprocess.run(["git", "config", "user.email", "e2e-test@example.com"],
                   cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "config", "user.name", "E2E Test"],
                   cwd=str(project_dir), capture_output=True)

    # 2. Write specification/INTENT.md
    spec_dir = project_dir / "specification"
    spec_dir.mkdir()
    (spec_dir / "INTENT.md").write_text(INTENT_MD)

    # 3. Create .ai-workspace directory tree
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

    # 4. Copy config files from plugin
    _copy_config_files(graph_dir)
    _copy_profile_files(profiles_dir)

    # 5. Copy feature vector template
    shutil.copy2(CONFIG_DIR / "feature_vector_template.yml",
                 ws / "features" / "feature_vector_template.yml")

    # 6. Write project_constraints.yml
    (context_dir / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)

    # 7. Write feature vector
    (features_active / "REQ-F-CONV-001.yml").write_text(
        FEATURE_VECTOR_YML.replace("{timestamp}", timestamp))

    # 8. Write feature_index.yml and ACTIVE_TASKS.md
    (ws / "features" / "feature_index.yml").write_text(FEATURE_INDEX_YML)
    (tasks_active / "ACTIVE_TASKS.md").write_text(ACTIVE_TASKS_MD)

    # 9. Copy commands to .claude/commands/
    _copy_commands(project_dir / ".claude" / "commands")

    # 10. Copy agent files for discoverability
    _copy_agents(agents_dir)

    # 11. Write CLAUDE.md and pyproject.toml
    (project_dir / "CLAUDE.md").write_text(TEST_PROJECT_CLAUDE_MD)
    (project_dir / "pyproject.toml").write_text(TEST_PROJECT_PYPROJECT)

    # 12. Create empty src/ and tests/ directories
    (project_dir / "src").mkdir(exist_ok=True)
    (project_dir / "tests").mkdir(exist_ok=True)

    # 13. Write initial event
    _write_initial_event(events_dir / "events.jsonl", "temperature-converter")

    # 14. Initial commit
    subprocess.run(["git", "add", "-A"], cwd=str(project_dir), capture_output=True)
    subprocess.run(["git", "commit", "-m", "chore: scaffold temperature converter for e2e test"],
                   cwd=str(project_dir), capture_output=True)

    return project_dir


def _count_converged_edges(project_dir: pathlib.Path) -> set[str]:
    """Read events.jsonl and return set of converged edge names."""
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    converged = set()
    if events_file.exists():
        for line in events_file.read_text().splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
                if event.get("event_type") == "edge_converged":
                    converged.add(event.get("edge", ""))
            except json.JSONDecodeError:
                pass
    return converged


STANDARD_EDGES = {
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
}


@pytest.fixture(scope="session")
def converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    """Run headless Claude to converge the test project.

    Session-scoped: runs ONCE, all 22+ tests validate the same output.

    Uses --max-budget-usd as the primary safeguard with a 30-minute wall timeout.
    Cost: ~$2-5 per run (sonnet model, 4 standard-profile edges).
    """
    project_dir = e2e_project_dir
    meta_dir = project_dir / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)

    prompt = '/aisdlc-start --auto --feature "REQ-F-CONV-001"'

    print(f"\n{'='*60}")
    print(f"E2E: Starting headless Claude (subprocess + watchdog)")
    print(f"E2E: Project dir: {project_dir}")
    print(f"E2E: Live output: tail -f {meta_dir}/stdout.log")
    print(f"{'='*60}\n", flush=True)

    result = run_claude_headless(
        project_dir, prompt, log_dir=meta_dir,
    )

    # Save meta
    (meta_dir / "meta.json").write_text(json.dumps({
        "returncode": result.returncode,
        "elapsed_seconds": round(result.elapsed, 1),
        "timed_out": result.timed_out,
        "prompt": prompt,
    }, indent=2))

    print(f"\nE2E: Claude finished in {result.elapsed:.0f}s "
          f"(rc={result.returncode}, timed_out={result.timed_out})", flush=True)

    # Check which edges converged
    converged_edges = _count_converged_edges(project_dir)
    missing_edges = STANDARD_EDGES - converged_edges
    print(f"E2E: Converged edges: {converged_edges}", flush=True)
    if missing_edges:
        print(f"E2E: Missing edges: {missing_edges}", flush=True)

    if result.timed_out and not converged_edges:
        pytest.fail(
            f"Claude killed (wall timeout) after {result.elapsed:.0f}s "
            f"with no convergence artifacts.\n"
            f"--- stdout (last 2000 chars) ---\n{result.stdout[-2000:]}\n"
            f"--- stderr (last 1000 chars) ---\n{result.stderr[-1000:]}\n"
            f"Full logs: {meta_dir}"
        )
    elif result.timed_out and converged_edges:
        print(f"E2E: Wall timeout but {len(converged_edges)}/4 edges converged — "
              f"proceeding with validation.", flush=True)

    if result.returncode != 0 and not result.timed_out and not converged_edges:
        pytest.fail(
            f"Claude exited with code {result.returncode} "
            f"after {result.elapsed:.0f}s with no convergence artifacts.\n"
            f"--- stdout (last 3000 chars) ---\n{result.stdout[-3000:]}\n"
            f"--- stderr (last 1000 chars) ---\n{result.stderr[-1000:]}\n"
            f"Full logs: {meta_dir}"
        )

    return project_dir
