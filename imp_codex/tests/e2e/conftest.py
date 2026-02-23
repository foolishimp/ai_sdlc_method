# Validates: REQ-TOOL-005, REQ-EVAL-001, REQ-EVAL-002
"""E2E fixtures for Codex Genesis.

This harness is Codex-native: it scaffolds a realistic project workspace and
executes a deterministic convergence simulation that produces the same
artifact classes expected from a methodology run (events, feature vectors,
code, tests, status).
"""

from __future__ import annotations

import json
import os
import pathlib
import re
import signal
import shutil
import subprocess
import threading
import time
import textwrap
from datetime import datetime, timezone

import pytest
import yaml

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent
PLUGIN_ROOT = PROJECT_ROOT / "imp_codex" / "code"
CONFIG_DIR = PLUGIN_ROOT / "config"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"
RUNS_DIR = pathlib.Path(__file__).parent / "runs"

# Session-level run archive state
_archive_path: pathlib.Path | None = None
_project_dir: pathlib.Path | None = None


INTENT_MD = textwrap.dedent(
    """\
    # Intent: Temperature Converter Library

    Build a Python library that converts between Celsius, Fahrenheit, and Kelvin
    with strict validation and complete test coverage.
    """
)

PROJECT_CONSTRAINTS = textwrap.dedent(
    """\
    ---
    project:
      name: "temperature-converter"
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

FEATURE_VECTOR_TEMPLATE = textwrap.dedent(
    """\
    ---
    feature: "REQ-F-CONV-001"
    title: "Temperature Conversion Functions"
    intent: "INT-001"
    vector_type: feature
    profile: standard
    status: pending
    convergence_type: ""
    created: "{ts}"
    updated: "{ts}"
    trajectory:
      requirements: {{status: pending}}
      design: {{status: pending}}
      code: {{status: pending}}
      unit_tests: {{status: pending}}
      uat_tests: {{status: pending}}
    """
)

PYPROJECT_TOML = textwrap.dedent(
    """\
    [project]
    name = "temperature-converter"
    version = "0.1.0"
    requires-python = ">=3.11"

    [tool.pytest.ini_options]
    testpaths = ["tests"]
    """
)

REAL_DRIVER_PY = textwrap.dedent(
    """\
    from __future__ import annotations

    import json
    import os
    import subprocess
    import textwrap
    from datetime import datetime, timezone
    from pathlib import Path

    import yaml

    project_dir = Path.cwd()
    feature = "REQ-F-CONV-001"
    project = "temperature-converter"
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"

    def now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def append_event(payload: dict) -> None:
        events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(events_file, "a") as f:
            f.write(json.dumps(payload) + "\\n")

    started_at = now()
    edges = [
        "intent→requirements",
        "requirements→design",
        "design→code",
        "code↔unit_tests",
    ]

    for i, edge in enumerate(edges, 1):
        append_event(
            {
                "event_type": "edge_started",
                "timestamp": now(),
                "project": project,
                "feature": feature,
                "edge": edge,
                "data": {"iteration": 1},
            }
        )
        append_event(
            {
                "event_type": "iteration_completed",
                "timestamp": now(),
                "project": project,
                "feature": feature,
                "edge": edge,
                "iteration": 1,
                "delta": 0,
                "status": "converged",
                "evaluators": {"passed": 3, "failed": 0, "skipped": 0, "total": 3},
                "asset": f"artifacts/{feature}/{edge}",
            }
        )
        append_event(
            {
                "event_type": "edge_converged",
                "timestamp": now(),
                "project": project,
                "feature": feature,
                "edge": edge,
                "data": {"iteration": i, "evaluators": "3/3", "convergence_type": "standard"},
            }
        )

    src = project_dir / "src"
    tests = project_dir / "tests"
    src.mkdir(exist_ok=True)
    tests.mkdir(exist_ok=True)
    (src / "__init__.py").write_text("")

    (src / "converter.py").write_text(
        textwrap.dedent(
            \"\"\"\
            # Implements: REQ-F-CONV-001
            # Implements: REQ-F-CONV-002

            def _check_number(v):
                if not isinstance(v, (int, float)):
                    raise TypeError("temperature must be numeric")

            def celsius_to_fahrenheit(c):
                _check_number(c)
                if c < -273.15:
                    raise ValueError("below absolute zero")
                return c * 9.0 / 5.0 + 32.0

            def fahrenheit_to_celsius(f):
                _check_number(f)
                if f < -459.67:
                    raise ValueError("below absolute zero")
                return (f - 32.0) * 5.0 / 9.0

            def celsius_to_kelvin(c):
                _check_number(c)
                if c < -273.15:
                    raise ValueError("below absolute zero")
                return c + 273.15

            def kelvin_to_celsius(k):
                _check_number(k)
                if k < 0:
                    raise ValueError("below absolute zero")
                return k - 273.15

            def fahrenheit_to_kelvin(f):
                return celsius_to_kelvin(fahrenheit_to_celsius(f))

            def kelvin_to_fahrenheit(k):
                return celsius_to_fahrenheit(kelvin_to_celsius(k))
            \"\"\"
        )
    )

    (tests / "test_converter.py").write_text(
        textwrap.dedent(
            \"\"\"\
            # Validates: REQ-F-CONV-001
            # Validates: REQ-F-CONV-002
            import pytest

            from src.converter import (
                celsius_to_fahrenheit,
                fahrenheit_to_celsius,
                celsius_to_kelvin,
                kelvin_to_celsius,
                fahrenheit_to_kelvin,
                kelvin_to_fahrenheit,
            )

            def test_formulas():
                assert celsius_to_fahrenheit(0) == 32.0
                assert celsius_to_fahrenheit(100) == 212.0
                assert fahrenheit_to_celsius(32) == 0.0
                assert round(fahrenheit_to_celsius(212), 6) == 100.0
                assert celsius_to_kelvin(0) == 273.15
                assert kelvin_to_celsius(273.15) == 0.0
                assert fahrenheit_to_kelvin(32) == 273.15
                assert kelvin_to_fahrenheit(273.15) == 32.0

            def test_validation():
                with pytest.raises(TypeError):
                    celsius_to_fahrenheit("x")
                with pytest.raises(ValueError):
                    celsius_to_fahrenheit(-300)
            \"\"\"
        )
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_dir)
    result = subprocess.run(
        ["pytest", "-q", "tests"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        raise SystemExit(
            "Generated tests failed:\\n"
            + result.stdout
            + "\\n"
            + result.stderr
        )

    feature_file = project_dir / ".ai-workspace" / "features" / "active" / "REQ-F-CONV-001.yml"
    with open(feature_file) as f:
        data = yaml.safe_load(f)
    data["status"] = "converged"
    data["updated"] = now()
    for phase in ("requirements", "design", "code", "unit_tests"):
        data["trajectory"][phase]["status"] = "converged"
        data["trajectory"][phase]["started_at"] = started_at
        data["trajectory"][phase]["converged_at"] = now()
    with open(feature_file, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    (project_dir / ".ai-workspace" / "STATUS.md").write_text(
        "State: ALL_CONVERGED\\nFeature: REQ-F-CONV-001\\n"
    )
    print("E2E convergence artifacts written")
    """
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _get_plugin_version() -> str:
    try:
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        return data.get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


def _compute_run_dir(failed: bool = False) -> pathlib.Path:
    """Compute the next archive run path with race-safe sequence claiming."""
    version = _get_plugin_version()
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    seq_pattern = re.compile(r"_(\d{4})$")
    max_seq = 0
    for d in RUNS_DIR.iterdir():
        if d.is_dir() and not d.name.startswith("."):
            m = seq_pattern.search(d.name)
            if m:
                max_seq = max(max_seq, int(m.group(1)))

    prefix = "e2e_FAILED_" if failed else "e2e_"
    for seq in range(max_seq + 1, max_seq + 100):
        candidate = RUNS_DIR / f"{prefix}{version}_{ts}_{seq:04d}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue

    return RUNS_DIR / f"{prefix}{version}_{ts}_{max_seq + 1:04d}"


def _persist_run(source_dir: pathlib.Path, failed: bool = False) -> pathlib.Path | None:
    """Archive a full e2e run for forensics."""
    try:
        dest = _compute_run_dir(failed=failed)
        # _compute_run_dir claims the path via mkdir; copytree needs absent dest.
        dest.rmdir()
        shutil.copytree(
            source_dir,
            dest,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
        )
        meta_dir = dest / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)
        manifest = {
            "version": _get_plugin_version(),
            "timestamp": _now(),
            "source_dir": str(source_dir),
            "failed": failed,
        }
        (meta_dir / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        status = "FAILED" if failed else "OK"
        print(f"E2E: Archived run ({status}) -> {dest}", flush=True)
        return dest
    except Exception as exc:  # pragma: no cover - defensive archive fallback
        print(f"E2E: WARNING - failed to archive run: {exc}", flush=True)
        return None


def _append_event(events_file: pathlib.Path, payload: dict) -> None:
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "a") as f:
        f.write(json.dumps(payload) + "\n")


def _copy_graph_files(dest_ws: pathlib.Path) -> None:
    graph = dest_ws / "graph"
    graph.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", graph / "graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", graph / "evaluator_defaults.yml")
    edges = graph / "edges"
    edges.mkdir(parents=True, exist_ok=True)
    for yml in (CONFIG_DIR / "edge_params").glob("*.yml"):
        shutil.copy2(yml, edges / yml.name)

    profiles = dest_ws / "profiles"
    profiles.mkdir(parents=True, exist_ok=True)
    for yml in (CONFIG_DIR / "profiles").glob("*.yml"):
        shutil.copy2(yml, profiles / yml.name)


def _copy_command_and_agent_specs(project_dir: pathlib.Path) -> None:
    cmd_dest = project_dir / ".claude" / "commands"
    cmd_dest.mkdir(parents=True, exist_ok=True)
    for md in COMMANDS_DIR.glob("*.md"):
        shutil.copy2(md, cmd_dest / md.name)

    agent_dest = project_dir / ".ai-workspace" / "agents"
    agent_dest.mkdir(parents=True, exist_ok=True)
    for md in AGENTS_DIR.glob("*.md"):
        shutil.copy2(md, agent_dest / md.name)


def _write_real_driver(project_dir: pathlib.Path) -> pathlib.Path:
    path = project_dir / ".ai-workspace" / "codex" / "context" / "e2e_real_driver.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(REAL_DRIVER_PY)
    return path


def _write_feature_vector(path: pathlib.Path, status: str, started: str, converged: str) -> None:
    with open(path) as f:
        data = yaml.safe_load(f)
    data["status"] = status
    data["updated"] = converged
    for phase in ("requirements", "design", "code", "unit_tests"):
        data["trajectory"][phase]["status"] = "converged"
        data["trajectory"][phase]["started_at"] = started
        data["trajectory"][phase]["converged_at"] = converged
    with open(path, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)


def _clean_env() -> dict[str, str]:
    """Return environment for nested Codex invocation."""
    env = os.environ.copy()
    # Avoid nested-local session reuse across CLI invocations.
    env.pop("CODEX_SESSION_ID", None)
    return env


def _codex_cli_available() -> bool:
    """Check if codex CLI is installed and callable."""
    try:
        result = subprocess.run(
            ["codex", "--version"],
            capture_output=True,
            text=True,
            timeout=10,
            env=_clean_env(),
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def _kill_process_group(proc: subprocess.Popen) -> None:
    """Kill subprocess process group with TERM->KILL fallback."""
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        for _ in range(50):
            if proc.poll() is not None:
                return
            time.sleep(0.1)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


class CodexRunResult:
    """Result of a headless Codex run."""

    def __init__(
        self,
        *,
        returncode: int,
        elapsed: float,
        timed_out: bool = False,
        log_dir: pathlib.Path | None = None,
    ):
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


def run_codex_headless(
    project_dir: pathlib.Path,
    prompt: str,
    *,
    model: str | None = None,
    wall_timeout: float = 1800.0,
    stall_timeout: float = 300.0,
    log_dir: pathlib.Path | None = None,
) -> CodexRunResult:
    """Run codex exec with watchdog timeouts and log capture."""
    if log_dir is None:
        log_dir = project_dir / ".e2e-meta"
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = log_dir / "stdout.log"
    stderr_log = log_dir / "stderr.log"
    last_message = log_dir / "last_message.txt"

    cmd = [
        "codex",
        "exec",
        "--full-auto",
        "--skip-git-repo-check",
        "--cd",
        str(project_dir),
        "--json",
        "--output-last-message",
        str(last_message),
    ]
    if model:
        cmd.extend(["-m", model])
    cmd.append(prompt)

    start = time.time()
    timed_out = False
    stall_killed = False

    def _project_fingerprint(directory: pathlib.Path) -> tuple[float, int]:
        latest = 0.0
        count = 0
        sentinel_dirs = [
            directory / "src",
            directory / "tests",
            directory / "specification",
            directory / ".ai-workspace" / "events",
            directory / ".ai-workspace" / "features",
            directory / ".ai-workspace" / "codex" / "context",
        ]
        for d in sentinel_dirs:
            if not d.exists():
                continue
            try:
                mt = d.stat().st_mtime
                if mt > latest:
                    latest = mt
                for child in d.iterdir():
                    count += 1
                    try:
                        mt = child.stat().st_mtime
                        if mt > latest:
                            latest = mt
                    except OSError:
                        continue
            except OSError:
                continue
        return latest, count

    with open(stdout_log, "w") as f_out, open(stderr_log, "w") as f_err:
        proc = subprocess.Popen(
            cmd,
            cwd=str(project_dir),
            stdout=f_out,
            stderr=f_err,
            text=True,
            env=_clean_env(),
            start_new_session=True,
        )

        def watchdog() -> None:
            nonlocal timed_out, stall_killed
            last_activity = time.time()
            last_mtime, last_count = _project_fingerprint(project_dir)
            last_stdout_size = 0
            last_stderr_size = 0

            while proc.poll() is None:
                time.sleep(10)
                now = time.time()

                if now - start > wall_timeout:
                    timed_out = True
                    _kill_process_group(proc)
                    return

                cur_mtime, cur_count = _project_fingerprint(project_dir)
                try:
                    cur_stdout = stdout_log.stat().st_size
                except OSError:
                    cur_stdout = 0
                try:
                    cur_stderr = stderr_log.stat().st_size
                except OSError:
                    cur_stderr = 0

                activity = (
                    cur_mtime > last_mtime
                    or cur_count != last_count
                    or cur_stdout > last_stdout_size
                    or cur_stderr > last_stderr_size
                )
                if activity:
                    last_mtime = cur_mtime
                    last_count = cur_count
                    last_stdout_size = cur_stdout
                    last_stderr_size = cur_stderr
                    last_activity = now
                elif now - last_activity > stall_timeout:
                    stall_killed = True
                    timed_out = True
                    _kill_process_group(proc)
                    return

        watcher = threading.Thread(target=watchdog, daemon=True)
        watcher.start()
        proc.wait()
        watcher.join(timeout=10)

    result = CodexRunResult(
        returncode=proc.returncode,
        elapsed=time.time() - start,
        timed_out=timed_out,
        log_dir=log_dir,
    )
    if stall_killed:
        result.stall_killed = True
    return result


def _simulate_convergence(project_dir: pathlib.Path) -> None:
    started_at = _now()
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    feature = "REQ-F-CONV-001"
    project = "temperature-converter"

    edges = [
        "intent→requirements",
        "requirements→design",
        "design→code",
        "code↔unit_tests",
    ]

    for i, edge in enumerate(edges, 1):
        ts = _now()
        _append_event(events_file, {
            "event_type": "edge_started",
            "timestamp": ts,
            "project": project,
            "feature": feature,
            "edge": edge,
            "data": {"iteration": 1},
        })
        _append_event(events_file, {
            "event_type": "iteration_completed",
            "timestamp": _now(),
            "project": project,
            "feature": feature,
            "edge": edge,
            "iteration": 1,
            "delta": 0,
            "status": "converged",
            "evaluators": {"passed": 3, "failed": 0, "skipped": 0, "total": 3},
            "asset": f"artifacts/{feature}/{edge}",
        })
        _append_event(events_file, {
            "event_type": "edge_converged",
            "timestamp": _now(),
            "project": project,
            "feature": feature,
            "edge": edge,
            "data": {"iteration": i, "evaluators": "3/3", "convergence_type": "standard"},
        })

    src = project_dir / "src"
    tests = project_dir / "tests"
    src.mkdir(exist_ok=True)
    tests.mkdir(exist_ok=True)
    (src / "__init__.py").write_text("")

    (src / "converter.py").write_text(
        textwrap.dedent(
            """\
            # Implements: REQ-F-CONV-001
            # Implements: REQ-F-CONV-002

            def _check_number(v):
                if not isinstance(v, (int, float)):
                    raise TypeError("temperature must be numeric")

            def celsius_to_fahrenheit(c):
                _check_number(c)
                if c < -273.15:
                    raise ValueError("below absolute zero")
                return c * 9.0 / 5.0 + 32.0

            def fahrenheit_to_celsius(f):
                _check_number(f)
                if f < -459.67:
                    raise ValueError("below absolute zero")
                return (f - 32.0) * 5.0 / 9.0

            def celsius_to_kelvin(c):
                _check_number(c)
                if c < -273.15:
                    raise ValueError("below absolute zero")
                return c + 273.15

            def kelvin_to_celsius(k):
                _check_number(k)
                if k < 0:
                    raise ValueError("below absolute zero")
                return k - 273.15

            def fahrenheit_to_kelvin(f):
                return celsius_to_kelvin(fahrenheit_to_celsius(f))

            def kelvin_to_fahrenheit(k):
                return celsius_to_fahrenheit(kelvin_to_celsius(k))
            """
        )
    )

    (tests / "test_converter.py").write_text(
        textwrap.dedent(
            """\
            # Validates: REQ-F-CONV-001
            # Validates: REQ-F-CONV-002
            import pytest

            from src.converter import (
                celsius_to_fahrenheit,
                fahrenheit_to_celsius,
                celsius_to_kelvin,
                kelvin_to_celsius,
                fahrenheit_to_kelvin,
                kelvin_to_fahrenheit,
            )

            def test_formulas():
                assert celsius_to_fahrenheit(0) == 32.0
                assert celsius_to_fahrenheit(100) == 212.0
                assert fahrenheit_to_celsius(32) == 0.0
                assert round(fahrenheit_to_celsius(212), 6) == 100.0
                assert celsius_to_kelvin(0) == 273.15
                assert kelvin_to_celsius(273.15) == 0.0
                assert fahrenheit_to_kelvin(32) == 273.15
                assert kelvin_to_fahrenheit(273.15) == 32.0

            def test_validation():
                with pytest.raises(TypeError):
                    celsius_to_fahrenheit("x")
                with pytest.raises(ValueError):
                    celsius_to_fahrenheit(-300)
            """
        )
    )

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_dir)
    result = subprocess.run(
        ["pytest", "-q", "tests"],
        cwd=str(project_dir),
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0, f"Generated tests failed: {result.stdout}\n{result.stderr}"

    feature_file = project_dir / ".ai-workspace" / "features" / "active" / "REQ-F-CONV-001.yml"
    _write_feature_vector(feature_file, "converged", started_at, _now())

    (project_dir / ".ai-workspace" / "STATUS.md").write_text(
        "State: ALL_CONVERGED\nFeature: REQ-F-CONV-001\n"
    )


def _count_converged_edges(project_dir: pathlib.Path) -> set[str]:
    events_file = project_dir / ".ai-workspace" / "events" / "events.jsonl"
    converged: set[str] = set()
    if not events_file.exists():
        return converged
    for line in events_file.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if event.get("event_type") == "edge_converged":
            edge = event.get("edge")
            if isinstance(edge, str):
                converged.add(edge)
    return converged


STANDARD_EDGES = {
    "intent→requirements",
    "requirements→design",
    "design→code",
    "code↔unit_tests",
}


@pytest.fixture(scope="session")
def e2e_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("codex-e2e-temperature-converter")
    ws = project_dir / ".ai-workspace"
    subprocess.run(["git", "init"], cwd=str(project_dir), capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "codex-e2e@example.com"],
        cwd=str(project_dir),
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Codex E2E"],
        cwd=str(project_dir),
        capture_output=True,
    )
    (project_dir / "specification").mkdir(parents=True, exist_ok=True)
    (ws / "features" / "active").mkdir(parents=True, exist_ok=True)
    (ws / "features" / "completed").mkdir(parents=True, exist_ok=True)
    (ws / "tasks" / "active").mkdir(parents=True, exist_ok=True)
    (ws / "events").mkdir(parents=True, exist_ok=True)
    (ws / "codex" / "context").mkdir(parents=True, exist_ok=True)

    _copy_graph_files(ws)
    _copy_command_and_agent_specs(project_dir)

    (project_dir / "specification" / "INTENT.md").write_text(INTENT_MD)
    (project_dir / "pyproject.toml").write_text(PYPROJECT_TOML)
    (ws / "codex" / "context" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS)
    (ws / "features" / "active" / "REQ-F-CONV-001.yml").write_text(
        FEATURE_VECTOR_TEMPLATE.format(ts=_now())
    )
    (ws / "features" / "feature_index.yml").write_text(
        textwrap.dedent(
            """\
            ---
            features:
              - id: "REQ-F-CONV-001"
                title: "Temperature Conversion Functions"
                status: pending
                profile: standard
                path: "features/active/REQ-F-CONV-001.yml"
            """
        )
    )
    (ws / "tasks" / "active" / "ACTIVE_TASKS.md").write_text(
        "# Active Tasks\n\n- [ ] REQ-F-CONV-001\n"
    )
    _write_real_driver(project_dir)
    _append_event(
        ws / "events" / "events.jsonl",
        {
            "event_type": "project_initialized",
            "timestamp": _now(),
            "project": "temperature-converter",
            "profile": "standard",
        },
    )
    subprocess.run(["git", "add", "-A"], cwd=str(project_dir), capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: scaffold codex e2e project"],
        cwd=str(project_dir),
        capture_output=True,
    )

    return project_dir


@pytest.fixture(scope="session")
def mock_converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    global _archive_path, _project_dir
    _project_dir = e2e_project_dir
    try:
        _simulate_convergence(e2e_project_dir)
    except Exception:
        _archive_path = _persist_run(e2e_project_dir, failed=True)
        raise
    return e2e_project_dir


@pytest.fixture(scope="session")
def real_converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    """REAL E2E: run codex exec to converge the project workspace."""
    if not _codex_cli_available():
        pytest.skip("Codex CLI not installed")

    global _archive_path, _project_dir
    _project_dir = e2e_project_dir

    project_dir = e2e_project_dir
    meta_dir = project_dir / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)

    model = os.environ.get("CODEX_E2E_MODEL", "gpt-5-codex").strip()
    prompt = textwrap.dedent(
        """\
        Execute these shell commands exactly and then exit:
        1. python .ai-workspace/codex/context/e2e_real_driver.py
        2. pytest -q tests

        Constraints:
        - Do not only describe changes; actually execute commands.
        - If command 2 fails, fix the workspace and re-run pytest -q tests.
        - Stop once tests pass.
        """
    ).strip()

    print(f"\n{'=' * 60}")
    print("E2E: Starting real Codex run (codex exec)")
    print(f"E2E: Project dir: {project_dir}")
    print(f"E2E: Mode: real  model={model}")
    print(f"E2E: Logs: {meta_dir}")
    print(f"{'=' * 60}\n", flush=True)

    result = run_codex_headless(
        project_dir,
        prompt,
        model=model,
        log_dir=meta_dir,
    )

    stall_killed = getattr(result, "stall_killed", False)
    (meta_dir / "meta.json").write_text(
        json.dumps(
            {
                "runner": "codex",
                "mode": "real",
                "returncode": result.returncode,
                "elapsed_seconds": round(result.elapsed, 1),
                "timed_out": result.timed_out,
                "stall_killed": stall_killed,
                "model": model,
            },
            indent=2,
        )
        + "\n"
    )

    converged_edges = _count_converged_edges(project_dir)
    missing_edges = STANDARD_EDGES - converged_edges
    print(
        f"E2E: Codex finished in {result.elapsed:.0f}s "
        f"(rc={result.returncode}, timed_out={result.timed_out})",
        flush=True,
    )
    print(f"E2E: Converged edges: {sorted(converged_edges)}", flush=True)
    if missing_edges:
        print(f"E2E: Missing edges: {sorted(missing_edges)}", flush=True)

    if result.timed_out and not converged_edges:
        _archive_path = _persist_run(project_dir, failed=True)
        pytest.fail(
            f"Codex timed out after {result.elapsed:.0f}s with no convergence artifacts.\n"
            f"--- stdout (last 3000 chars) ---\n{result.stdout[-3000:]}\n"
            f"--- stderr (last 1500 chars) ---\n{result.stderr[-1500:]}\n"
            f"Full logs: {meta_dir}"
        )
    if result.returncode != 0 and not result.timed_out and not converged_edges:
        _archive_path = _persist_run(project_dir, failed=True)
        pytest.fail(
            f"Codex exited with code {result.returncode} after {result.elapsed:.0f}s.\n"
            f"--- stdout (last 3000 chars) ---\n{result.stdout[-3000:]}\n"
            f"--- stderr (last 1500 chars) ---\n{result.stderr[-1500:]}\n"
            f"Full logs: {meta_dir}"
        )

    return project_dir


@pytest.fixture(scope="session")
def converged_project(request) -> pathlib.Path:
    """Dispatch between deterministic mock mode and true Codex CLI mode."""
    mode = os.environ.get("CODEX_E2E_MODE", "mock").strip().lower()
    if mode in {"real", "live"}:
        return request.getfixturevalue("real_converged_project")
    return request.getfixturevalue("mock_converged_project")


def pytest_sessionfinish(session, exitstatus):
    """Archive run + write e2e test results for forensic inspection."""
    global _archive_path

    e2e_items = [item for item in session.items if "e2e" in item.nodeid]
    results = []
    for item in e2e_items:
        setup_report = item.stash.get(_setup_report_key, None)
        call_report = item.stash.get(_test_report_key, None)
        if setup_report and setup_report.failed:
            entry = {"nodeid": item.nodeid, "outcome": "error", "phase": "setup"}
            if setup_report.longreprtext:
                entry["message"] = setup_report.longreprtext[:2000]
            results.append(entry)
        elif call_report is not None:
            entry = {
                "nodeid": item.nodeid,
                "outcome": call_report.outcome,
                "duration": round(call_report.duration, 3),
            }
            if call_report.failed and call_report.longreprtext:
                entry["message"] = call_report.longreprtext[:2000]
            results.append(entry)
        else:
            results.append({"nodeid": item.nodeid, "outcome": "unknown"})

    any_failures = exitstatus != 0 or any(
        r["outcome"] in ("failed", "error") for r in results
    )
    if _archive_path is None and _project_dir is not None:
        _archive_path = _persist_run(_project_dir, failed=any_failures)

    if _archive_path is None or not _archive_path.exists():
        return

    summary = {
        "exit_status": exitstatus,
        "total": len(results),
        "passed": sum(1 for r in results if r["outcome"] == "passed"),
        "failed": sum(1 for r in results if r["outcome"] == "failed"),
        "error": sum(1 for r in results if r["outcome"] == "error"),
        "skipped": sum(1 for r in results if r["outcome"] == "skipped"),
        "tests": results,
    }

    meta_dir = _archive_path / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)
    (meta_dir / "test_results.json").write_text(json.dumps(summary, indent=2) + "\n")

    manifest_path = meta_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            manifest["tests_passed"] = summary["passed"]
            manifest["tests_failed"] = summary["failed"]
            manifest["tests_error"] = summary["error"]
            manifest["tests_total"] = summary["total"]
            manifest["exit_status"] = exitstatus
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        except (OSError, json.JSONDecodeError):
            pass

    status = "PASS" if exitstatus == 0 else "FAIL"
    print(
        f"E2E: Test results ({status}: {summary['passed']}/{summary['total']}) -> "
        f"{meta_dir / 'test_results.json'}",
        flush=True,
    )


_test_report_key = pytest.StashKey()
_setup_report_key = pytest.StashKey()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    if report.when == "setup":
        item.stash[_setup_report_key] = report
    elif report.when == "call":
        item.stash[_test_report_key] = report
