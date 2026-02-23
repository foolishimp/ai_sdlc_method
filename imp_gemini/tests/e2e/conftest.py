# Validates: REQ-TOOL-005, REQ-EVAL-001
import json
import os
import pathlib
import shutil
import subprocess
import textwrap
import time
from datetime import datetime, timezone
import pytest
import yaml

# Path Constants
PROJECT_ROOT = pathlib.Path("/Users/jim/src/apps/ai_sdlc_method")
IMP_GEMINI = PROJECT_ROOT / "imp_gemini"
PLUGIN_ROOT = IMP_GEMINI / "code"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
COMMANDS_DIR = PLUGIN_ROOT / "commands"
AGENTS_DIR = PLUGIN_ROOT / "agents"
RUNS_DIR = pathlib.Path(__file__).parent / "runs"

# Module-level state: archive path set by converged_project fixture,
# read by pytest_sessionfinish to write test results into the archive.
_archive_path: pathlib.Path | None = None


# ═══════════════════════════════════════════════════════════════════════
# RUN ARCHIVE HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _get_plugin_version() -> str:
    """Read version from plugin.json. Falls back to 'unknown'."""
    try:
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        return data.get("version", "unknown")
    except (OSError, json.JSONDecodeError):
        return "unknown"


def _compute_run_dir(failed: bool = False) -> pathlib.Path:
    """Compute next runs/<version>_<datetime>_<seq> path.

    Sequence = max existing sequence number + 1 (monotonic even after cleanup).
    Failed runs get FAILED_ prefix.
    """
    import re
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
    seq = max_seq + 1

    prefix = "FAILED_" if failed else ""
    name = f"{prefix}{version}_{ts}_{seq:04d}"
    return RUNS_DIR / name


def _persist_run(source_dir: pathlib.Path, failed: bool = False) -> pathlib.Path | None:
    """Copy project dir to runs/ archive. Best-effort — warns on failure.

    Excludes .git and __pycache__ directories.
    Writes run_manifest.json into the archive's .e2e-meta/ directory.
    Returns the archive path on success, None on failure.
    """
    try:
        dest = _compute_run_dir(failed=failed)
        shutil.copytree(
            source_dir, dest,
            ignore=shutil.ignore_patterns(".git", "__pycache__"),
        )
        # Write manifest
        meta_dir = dest / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)
        manifest = {
            "version": _get_plugin_version(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_dir": str(source_dir),
            "failed": failed,
        }
        (meta_dir / "run_manifest.json").write_text(
            json.dumps(manifest, indent=2) + "\n"
        )
        status = "FAILED" if failed else "OK"
        print(f"E2E: Archived run ({status}) → {dest}", flush=True)
        return dest
    except Exception as exc:
        print(f"E2E: WARNING — failed to archive run: {exc}", flush=True)
        return None

# Content Templates
INTENT_MD = textwrap.dedent("""
    # Intent: Temperature Converter Library
    We need a Python library that converts between Celsius, Fahrenheit, and Kelvin.
    ### REQ-F-CONV-001: Temperature Conversion Functions
    ### REQ-F-CONV-002: Input Validation
""")

PROJECT_CONSTRAINTS_YML = textwrap.dedent("""
    project:
      name: "temperature-converter"
      version: "0.1.0"
      default_profile: standard
      mode: interactive
      valence: medium
    language:
      primary: python
      version: "3.12"
    tools:
      test_runner:
        command: "pytest"
        args: "-v"
        pass_criterion: "exit code 0"
    thresholds:
      test_coverage_minimum: 0.80
    standards:
      style_guide: "PEP 8"
      req_tag_format:
        code: "Implements: REQ-F-CONV-{SEQ}"
        tests: "Validates: REQ-F-CONV-{SEQ}"
    constraint_dimensions:
      ecosystem_compatibility:
        language: "python"
        version: "3.12"
      deployment_target:
        platform: "library"
      security_model:
        authentication: "none"
      build_system:
        tool: "pip"
""")

# ═══════════════════════════════════════════════════════════════════════
# HEADLESS RUNNER — SUBPROCESS WITH WATCHDOG
# ═══════════════════════════════════════════════════════════════════════

class GeminiRunResult:
    """Result of a headless Gemini run."""
    def __init__(self, *, returncode: int, elapsed: float, timed_out: bool = False, log_dir: pathlib.Path | None = None):
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

def _kill_process_group(proc: subprocess.Popen) -> None:
    import signal
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGTERM)
        for _ in range(50):
            if proc.poll() is not None: return
            time.sleep(0.1)
        os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try: proc.kill()
        except ProcessLookupError: pass

def run_gemini_headless(
    project_dir: pathlib.Path,
    prompt: str,
    *,
    model: str = "gemini-2.0-flash",
    wall_timeout: float = 1800.0,
    stall_timeout: float = 300.0,
    log_dir: pathlib.Path | None = None,
) -> GeminiRunResult:
    """Run gemini -p with wall timeout and stall detection (Actor-like watchdog)."""
    import subprocess
    import threading
    
    if log_dir is None: log_dir = project_dir / ".e2e-meta"
    log_dir.mkdir(parents=True, exist_ok=True)

    stdout_log = log_dir / "stdout.log"
    stderr_log = log_dir / "stderr.log"

    # Using -y/--yolo to avoid interactive prompts in headless mode
    # --include-directories ensures the agent can see the temp project dir
    cmd = [
        "gemini", "-p", prompt,
        "--model", model,
        "--yolo",
        "--raw-output",
        "--accept-raw-output-risk",
        "--include-directories", str(project_dir)
    ]

    start = time.time()
    timed_out = False
    stall_killed = False

    def _project_fingerprint(directory: pathlib.Path) -> tuple[float, int]:
        latest = 0.0
        count = 0
        sentinel_dirs = [
            directory / "src",
            directory / "tests",
            directory / ".ai-workspace" / "events",
            directory / ".ai-workspace" / "features",
        ]
        for d in sentinel_dirs:
            if not d.exists(): continue
            try:
                mt = d.stat().st_mtime
                if mt > latest: latest = mt
                for child in d.iterdir():
                    count += 1
                    try:
                        mt = child.stat().st_mtime
                        if mt > latest: latest = mt
                    except OSError: continue
            except OSError: continue
        return latest, count

    with open(stdout_log, "w") as f_out, open(stderr_log, "w") as f_err:
        proc = subprocess.Popen(
            cmd, cwd=str(project_dir),
            stdout=f_out, stderr=f_err,
            text=True, start_new_session=True,
        )

        def watchdog():
            nonlocal timed_out, stall_killed
            last_activity = time.time()
            last_mtime, last_count = _project_fingerprint(project_dir)
            last_stderr_size = 0

            while proc.poll() is None:
                time.sleep(10)
                now = time.time()
                if now - start > wall_timeout:
                    timed_out = True
                    _kill_process_group(proc)
                    return

                cur_mtime, cur_count = _project_fingerprint(project_dir)
                try: cur_stderr = stderr_log.stat().st_size
                except OSError: cur_stderr = 0

                if (cur_mtime > last_mtime or cur_count != last_count or cur_stderr > last_stderr_size):
                    last_mtime, last_count, last_stderr_size = cur_mtime, cur_count, cur_stderr
                    last_activity = now
                elif now - last_activity > stall_timeout:
                    stall_killed, timed_out = True, True
                    _kill_process_group(proc)
                    return

        watcher = threading.Thread(target=watchdog, daemon=True)
        watcher.start()
        proc.wait()
        watcher.join(timeout=10)

    return GeminiRunResult(returncode=proc.returncode, elapsed=time.time() - start, timed_out=timed_out, log_dir=log_dir)

def _gemini_cli_available() -> bool:
    """Check if gemini CLI is installed."""
    try:
        result = subprocess.run(
            ["gemini", "--version"],
            capture_output=True, text=True, timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

skip_no_gemini = pytest.mark.skipif(
    not _gemini_cli_available(),
    reason="Gemini CLI not installed",
)

# Mock Runner to simulate Gemini CLI behavior
class MockGeminiRunner:
    def __init__(self, project_dir):
        self.project_dir = project_dir
        self.ws_dir = project_dir / ".ai-workspace"
        self.events_file = self.ws_dir / "events" / "events.jsonl"

    def _emit_event(self, event_type, **kwargs):
        ev = {"event_type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "project": "temperature-converter"}
        ev.update(kwargs)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.events_file, "a") as f:
            f.write(json.dumps(ev) + "\n")

    def _update_feature_vector(self, feature_id, edge, status="converged"):
        fv_path = self.ws_dir / "features" / "active" / f"{feature_id}.yml"
        with open(fv_path, "r") as f:
            data = yaml.safe_load(f)
        
        if "trajectory" not in data: data["trajectory"] = {}
        target = edge.replace("↔", "→").split("→")[-1]
        data["trajectory"][target] = {
            "status": status,
            "converged_at": datetime.now(timezone.utc).isoformat(),
            "iteration": 1,
            "delta": 0 if status == "converged" else 1
        }
        if all(data["trajectory"].get(e, {}).get("status") == "converged" for e in ["requirements", "design", "code", "unit_tests"]):
            data["status"] = "converged"
        
        with open(fv_path, "w") as f:
            yaml.dump(data, f)

    def run_auto(self, feature_id):
        # Simulate /gen-start --auto
        edges = ["intent→requirements", "requirements→design", "design→code", "code↔unit_tests"]
        for edge in edges:
            self._emit_event("edge_started", feature=feature_id, edge=edge)
            # Simulate work
            if "code" in edge or "unit_tests" in edge:
                self._generate_artifacts(feature_id)
            
            self._emit_event("iteration_completed", feature=feature_id, edge=edge, iteration=1, delta=0, status="converged")
            self._emit_event("edge_converged", feature=feature_id, edge=edge)
            self._update_feature_vector(feature_id, edge, "converged")

    def _generate_artifacts(self, feature_id):
        src_dir = self.project_dir / "src"
        test_dir = self.project_dir / "tests"
        src_dir.mkdir(exist_ok=True)
        test_dir.mkdir(exist_ok=True)
        
        (src_dir / "converter.py").write_text(textwrap.dedent(f"""
            # Implements: {feature_id}
            def celsius_to_fahrenheit(c): return c * 9/5 + 32
        """))
        (test_dir / "test_converter.py").write_text(textwrap.dedent(f"""
            # Validates: {feature_id}
            from src.converter import celsius_to_fahrenheit
            def test_celsius_to_fahrenheit(): assert celsius_to_fahrenheit(0) == 32.0
        """))

@pytest.fixture(scope="session")
def e2e_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-e2e")
    ws = project_dir / ".ai-workspace"
    
    # 1. Scaffolding
    for d in ["graph/edges", "profiles", "features/active", "events", "gemini_genesis", "spec"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    
    # 2. Copy configs
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"):
        shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"):
        shutil.copy2(yml, ws / "profiles" / yml.name)
    
    # 3. Write Templates
    (ws / "spec" / "INTENT.md").write_text(INTENT_MD)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text(PROJECT_CONSTRAINTS_YML)
    
    # 4. Initial Feature Vector
    fv_data = {
        "feature": "REQ-F-CONV-001",
        "status": "pending",
        "trajectory": {}
    }
    with open(ws / "features" / "active" / "REQ-F-CONV-001.yml", "w") as f:
        yaml.dump(fv_data, f)
    
    # 5. Initial Event
    ev = {"event_type": "project_initialized", "timestamp": datetime.now(timezone.utc).isoformat(), "project": "temperature-converter"}
    with open(ws / "events" / "events.jsonl", "w") as f:
        f.write(json.dumps(ev) + "\n")
        
    # 6. Copy code directory for agentic discovery
    dest_code = project_dir / "code"
    shutil.copytree(IMP_GEMINI / "code", dest_code, dirs_exist_ok=True)

    # 7. Disable human required checks in edge configs to allow full automation
    for yml in (ws / "graph/edges").glob("*.yml"):
        content = yml.read_text()
        if "type: human" in content:
            new_content = content.replace("required: true", "required: false")
            yml.write_text(new_content)

    return project_dir

@pytest.fixture(scope="session")
def mock_converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    runner = MockGeminiRunner(e2e_project_dir)
    runner.run_auto("REQ-F-CONV-001")
    
    global _archive_path
    _archive_path = _persist_run(e2e_project_dir, failed=False)
    
    return e2e_project_dir

@pytest.fixture(scope="session")
def real_converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    """REAL E2E: Run Gemini CLI headless to converge the project."""
    project_dir = e2e_project_dir
    prompt = (
        "You are the autonomous AI SDLC methodology engine. Your goal is to converge feature 'REQ-F-CONV-001' in 'temperature-converter'. "
        "The project is ALREADY INITIALISED. "
        "Traverse these edges in order: intent→requirements, requirements→design, design→code, code↔unit_tests. "
        "1. For each edge, follow 'code/agents/gen-iterate.md'. "
        "2. PROTOCOL: After EVERY edge traversal, you MUST manually append THREE JSON events to '.ai-workspace/events/events.jsonl' in order: 'edge_started', 'iteration_completed', and 'edge_converged'. "
        "   Example: printf '{\"event_type\": \"edge_converged\", \"project\": \"temperature-converter\", \"feature\": \"REQ-F-CONV-001\", \"edge\": \"intent→requirements\", \"timestamp\": \"2026-02-23T12:00:00Z\"}\\n' >> .ai-workspace/events/events.jsonl\n"
        "3. YAML UPDATE: Update '.ai-workspace/features/active/REQ-F-CONV-001.yml' with the COMPLETE content. You MUST include the 'trajectory' section with 'status: converged' for every traversed edge. "
        "   Example trajectory entry: requirements: {status: converged, iteration: 1, converged_at: \"2026-02-23T12:00:00Z\"}\n"
        "4. CONSTRUCTION: Create 'src/converter.py' and 'tests/test_converter.py' in project root with 'Implements: REQ-F-CONV-001' and 'Validates: REQ-F-CONV-001' tags. "
        "5. CONTINUE until all 4 edges are converged AND the top-level feature status is 'converged'."
    )
    
    result = run_gemini_headless(project_dir, prompt)
    
    global _archive_path
    _archive_path = _persist_run(project_dir, failed=(result.returncode != 0))
    
    return project_dir

# ═══════════════════════════════════════════════════════════════════════
# TEST RESULTS CAPTURE
# ═══════════════════════════════════════════════════════════════════════

def pytest_sessionfinish(session, exitstatus):
    """Write test results into the run archive for forensic analysis."""
    if _archive_path is None or not _archive_path.exists():
        return

    results = []
    for item in session.items:
        report = item.stash.get(_test_report_key, None)
        if report is None:
            results.append({"nodeid": item.nodeid, "outcome": "unknown"})
        else:
            entry = {
                "nodeid": item.nodeid,
                "outcome": report.outcome,
                "duration": round(report.duration, 3),
            }
            if report.failed and report.longreprtext:
                entry["message"] = report.longreprtext[:2000]
            results.append(entry)

    summary = {
        "exit_status": exitstatus,
        "total": len(results),
        "passed": sum(1 for r in results if r["outcome"] == "passed"),
        "failed": sum(1 for r in results if r["outcome"] == "failed"),
        "skipped": sum(1 for r in results if r["outcome"] == "skipped"),
        "tests": results,
    }

    meta_dir = _archive_path / ".e2e-meta"
    meta_dir.mkdir(exist_ok=True)
    (meta_dir / "test_results.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    # Update run_manifest with final verdict
    manifest_path = meta_dir / "run_manifest.json"
    if manifest_path.exists():
        try:
            manifest = json.loads(manifest_path.read_text())
            manifest["tests_passed"] = summary["passed"]
            manifest["tests_failed"] = summary["failed"]
            manifest["tests_total"] = summary["total"]
            manifest["exit_status"] = exitstatus
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        except (OSError, json.JSONDecodeError):
            pass

    status = "PASS" if exitstatus == 0 else "FAIL"
    print(f"E2E: Test results ({status}: {summary['passed']}/{summary['total']}) "
          f"→ {meta_dir / 'test_results.json'}", flush=True)


# Stash key for storing per-test reports
_test_report_key = pytest.StashKey()


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Capture test call-phase reports for pytest_sessionfinish."""
    outcome = yield
    report = outcome.get_result()
    if report.when == "call":
        item.stash[_test_report_key] = report
