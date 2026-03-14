# Validates: REQ-TOOL-011, REQ-EVAL-001, REQ-LIFE-002, REQ-SUPV-003
"""Sandbox-based E2E test framework.

Implements Codex E2E definition (2026-03-14):
  1. Create a fresh versioned sandbox from a template
  2. Install Genesis using the installer for the candidate version
  3. Run the real E2E/UAT suite against the installed sandbox, not the source tree
  4. Preserve the resulting .ai-workspace as the incident artifact set
  5. Do forensic diagnosis against that artifact set
  6. Produce bug reports traced across intent → req → design → code → tests → events → monitor

Environment and installer provenance:
  version, commit, installer args, timestamps, test command line.

Sandbox .ai-workspace is immutable evidence once run completes.
"""

from __future__ import annotations

import dataclasses
import json
import os
import pathlib
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import threading
import time
from collections import Counter
from datetime import datetime, timezone
from typing import Optional

import pytest

# ===========================================================================
# Path constants
# ===========================================================================

PROJECT_ROOT = pathlib.Path(__file__).parent.parent.parent.parent  # ai_sdlc_method/
INSTALLER = PROJECT_ROOT / "imp_claude" / "code" / "installers" / "gen-setup.py"
RUNS_DIR = pathlib.Path(__file__).parent / "runs"
PLUGIN_ROOT = (
    PROJECT_ROOT / "imp_claude" / "code" / ".claude-plugin" / "plugins" / "genesis"
)


# ===========================================================================
# Helpers
# ===========================================================================


def _get_plugin_version() -> str:
    try:
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        return data.get("version", "unknown")
    except Exception:
        return "unknown"


def _capture_git_info(repo_path: pathlib.Path) -> tuple[str, str]:
    """Return (commit_hash, branch_name). Returns ('unknown','unknown') on failure."""
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(repo_path), capture_output=True, text=True, timeout=5
        ).stdout.strip()
        branch = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=str(repo_path), capture_output=True, text=True, timeout=5
        ).stdout.strip()
        return commit or "unknown", branch or "unknown"
    except Exception:
        return "unknown", "unknown"


def _clean_env() -> dict[str, str]:
    """Strip Claude nesting guards from environment."""
    env = os.environ.copy()
    for key in ["CLAUDECODE", "CLAUDE_CODE_SSE_PORT", "CLAUDE_CODE_ENTRYPOINT"]:
        env.pop(key, None)
    return env


def _claude_cli_available() -> bool:
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


# ===========================================================================
# Provenance Capture
# ===========================================================================


@dataclasses.dataclass
class InstallerProvenance:
    """Complete provenance record for a Genesis installation.

    Captures everything needed to reproduce the run:
    version, source commit, installer args, timestamps, Python/platform details.
    """
    sandbox_path: str
    version: str              # from plugin.json
    git_commit: str           # git rev-parse HEAD of source repo
    git_branch: str           # git rev-parse --abbrev-ref HEAD
    installer_path: str       # absolute path to gen-setup.py
    installer_args: list      # full argv used to invoke installer
    installer_source: str     # "local:<path>" or "github:..."
    timestamp_start: str      # ISO 8601 before installer runs
    timestamp_end: str        # ISO 8601 after installer completes
    installer_exit_code: int
    python_version: str       # sys.version
    platform: str             # sys.platform
    test_command: list        # sys.argv at test start

    def to_dict(self) -> dict:
        return dataclasses.asdict(self)


# ===========================================================================
# Sandbox templates
# ===========================================================================

SANDBOX_TEMPLATE_PYPROJECT = textwrap.dedent("""\
    [project]
    name = "hello-sandbox"
    version = "0.1.0"
    requires-python = ">=3.10"
    description = "Genesis sandbox E2E test project"

    [tool.pytest.ini_options]
    testpaths = ["tests"]
""")

SANDBOX_TEMPLATE_INTENT = textwrap.dedent("""\
    # Intent: Hello Sandbox

    ## Problem

    We need a minimal sandbox project to validate Genesis installation and operation.

    ## Goals

    - REQ-F-HELLO-001: The system shall provide a greet(name) function returning "Hello, {name}!"
    - REQ-F-HELLO-002: The system shall validate that name is a non-empty string

    ## Success Criteria

    - greet("World") == "Hello, World!"
    - greet("") raises ValueError
    - greet(42) raises TypeError
""")

SANDBOX_TEMPLATE_CLAUDE_MD = textwrap.dedent("""\
    # CLAUDE.md — Hello Sandbox

    This is a sandbox project for testing Genesis installation and operation.

    ## Commands

    ```bash
    pytest tests/ -v
    ```
""")

SANDBOX_FEATURE_VECTOR = textwrap.dedent("""\
    ---
    id: "REQ-F-HELLO-001"
    title: "Hello World greeting function"
    status: pending
    profile: poc
    satisfies:
      - REQ-F-HELLO-001
      - REQ-F-HELLO-002
    trajectory:
      requirements:
        status: converged
      design:
        status: pending
      code:
        status: pending
      unit_tests:
        status: pending
    dependencies: []
    constraints:
      acceptance_criteria:
        - id: "AC-HELLO-001"
          description: "greet('World') returns 'Hello, World!'"
          evaluator: deterministic
          check: "pytest tests/ -k test_greet"
          req: "REQ-F-HELLO-001"
          required: true
        - id: "AC-HELLO-002"
          description: "greet('') raises ValueError"
          evaluator: deterministic
          check: "pytest tests/ -k test_greet_empty"
          req: "REQ-F-HELLO-002"
          required: true
      threshold_overrides: {}
      additional_checks: []
""")


# ===========================================================================
# Sandbox Factory
# ===========================================================================


class SandboxFactory:
    """Creates versioned, named sandbox directories for E2E testing."""

    def __init__(self, runs_dir: pathlib.Path = RUNS_DIR):
        self.runs_dir = runs_dir

    def allocate_directory(self) -> pathlib.Path:
        """Allocate next sandbox.e2etst_{ts}_{seq:04d} directory atomically."""
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
        self.runs_dir.mkdir(parents=True, exist_ok=True)

        seq_pat = re.compile(r"sandbox\.e2etst_\d{8}T\d{6}_(\d{4})$")
        max_seq = 0
        for d in self.runs_dir.iterdir():
            if d.is_dir():
                m = seq_pat.match(d.name)
                if m:
                    max_seq = max(max_seq, int(m.group(1)))

        for attempt in range(max_seq + 1, max_seq + 100):
            candidate = self.runs_dir / f"sandbox.e2etst_{ts}_{attempt:04d}"
            try:
                candidate.mkdir()
                return candidate
            except FileExistsError:
                continue

        raise RuntimeError("Cannot allocate sandbox directory after 100 attempts")

    def scaffold_template(self, sandbox_dir: pathlib.Path) -> None:
        """Write minimal template project files before installer runs."""
        (sandbox_dir / "pyproject.toml").write_text(SANDBOX_TEMPLATE_PYPROJECT)
        (sandbox_dir / "CLAUDE.md").write_text(SANDBOX_TEMPLATE_CLAUDE_MD)

        spec_dir = sandbox_dir / "specification"
        spec_dir.mkdir()
        (spec_dir / "INTENT.md").write_text(SANDBOX_TEMPLATE_INTENT)

        (sandbox_dir / "src").mkdir()
        (sandbox_dir / "tests").mkdir()

        # Git init so installer can install hooks
        subprocess.run(
            ["git", "init", "-q"],
            cwd=str(sandbox_dir), capture_output=True, timeout=10
        )
        subprocess.run(
            ["git", "config", "user.email", "sandbox@test.example"],
            cwd=str(sandbox_dir), capture_output=True, timeout=5
        )
        subprocess.run(
            ["git", "config", "user.name", "Sandbox Test"],
            cwd=str(sandbox_dir), capture_output=True, timeout=5
        )


# ===========================================================================
# Installed Sandbox
# ===========================================================================


class InstalledSandbox:
    """A sandbox directory with Genesis installed.

    Created by SandboxInstaller.install(). Provides access to the
    workspace, engine, and event log.
    """

    def __init__(
        self,
        sandbox_dir: pathlib.Path,
        provenance: InstallerProvenance,
        installer_stdout: str,
        installer_stderr: str,
    ):
        self.sandbox_dir = sandbox_dir
        self.provenance = provenance
        self.installer_stdout = installer_stdout
        self.installer_stderr = installer_stderr

    @property
    def workspace_dir(self) -> pathlib.Path:
        return self.sandbox_dir / ".ai-workspace"

    @property
    def events_file(self) -> pathlib.Path:
        return self.workspace_dir / "events" / "events.jsonl"

    @property
    def engine_dir(self) -> pathlib.Path:
        return self.sandbox_dir / ".genesis" / "genesis"

    @property
    def commands_dir(self) -> pathlib.Path:
        return self.sandbox_dir / ".claude" / "commands"

    def load_events(self) -> list[dict]:
        """Load all events from the sandbox workspace."""
        if not self.events_file.exists():
            return []
        events = []
        for line in self.events_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return events

    def run_engine(
        self, args: list[str], timeout: int = 30
    ) -> subprocess.CompletedProcess:
        """Run the genesis engine installed in this sandbox via subprocess."""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(self.sandbox_dir / ".genesis")
        return subprocess.run(
            [sys.executable, "-m", "genesis"] + args,
            cwd=str(self.sandbox_dir),
            capture_output=True, text=True, timeout=timeout,
            env=env,
        )

    def freeze(self) -> "FrozenArtifactSet":
        """Freeze the workspace as immutable evidence."""
        return FrozenArtifactSet.create(self)


class SandboxInstaller:
    """Runs gen-setup.py against a sandbox directory using local source mode."""

    def __init__(self, project_root: pathlib.Path = PROJECT_ROOT):
        self.project_root = project_root
        self.installer = project_root / "imp_claude" / "code" / "installers" / "gen-setup.py"

    def install(self, sandbox_dir: pathlib.Path) -> InstalledSandbox:
        """Run installer with --source PROJECT_ROOT --target sandbox."""
        args = [
            sys.executable, str(self.installer),
            "--source", str(self.project_root),
            "--target", str(sandbox_dir),
        ]

        ts_start = datetime.now(timezone.utc).isoformat()
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=120,
        )
        ts_end = datetime.now(timezone.utc).isoformat()

        commit, branch = _capture_git_info(self.project_root)

        provenance = InstallerProvenance(
            sandbox_path=str(sandbox_dir),
            version=_get_plugin_version(),
            git_commit=commit,
            git_branch=branch,
            installer_path=str(self.installer),
            installer_args=args,
            installer_source=f"local:{self.project_root}",
            timestamp_start=ts_start,
            timestamp_end=ts_end,
            installer_exit_code=result.returncode,
            python_version=sys.version,
            platform=sys.platform,
            test_command=sys.argv[:],
        )

        meta_dir = sandbox_dir / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)
        (meta_dir / "provenance.json").write_text(
            json.dumps(provenance.to_dict(), indent=2)
        )
        (meta_dir / "installer_stdout.log").write_text(result.stdout)
        (meta_dir / "installer_stderr.log").write_text(result.stderr)

        return InstalledSandbox(
            sandbox_dir=sandbox_dir,
            provenance=provenance,
            installer_stdout=result.stdout,
            installer_stderr=result.stderr,
        )


# ===========================================================================
# Frozen Artifact Set
# ===========================================================================


@dataclasses.dataclass
class ArtifactManifest:
    """Manifest of a frozen workspace artifact set."""
    sandbox_path: str
    frozen_at: str
    events_line_count: int
    feature_vectors: list      # filenames found in features/active + completed
    review_files: list         # files under reviews/
    generated_code_files: list # files in src/
    generated_test_files: list # files in tests/
    provenance: dict           # copy of InstallerProvenance.to_dict()


class FrozenArtifactSet:
    """Immutable snapshot of a sandbox workspace after a run.

    Once created, the manifest is written to .e2e-meta/artifact_manifest.json.
    This is the canonical evidence artifact for forensic diagnosis.
    """

    def __init__(self, sandbox_dir: pathlib.Path, manifest: ArtifactManifest):
        self.sandbox_dir = sandbox_dir
        self.manifest = manifest

    @classmethod
    def create(cls, sandbox: InstalledSandbox) -> "FrozenArtifactSet":
        """Create frozen artifact set snapshot from an installed sandbox."""
        ws = sandbox.workspace_dir

        events_count = 0
        if sandbox.events_file.exists():
            events_count = sum(
                1 for line in sandbox.events_file.read_text().splitlines()
                if line.strip()
            )

        feature_vectors: list[str] = []
        for subdir in ["active", "completed"]:
            d = ws / "features" / subdir
            if d.exists():
                feature_vectors.extend(sorted(f.name for f in d.glob("*.yml")))

        reviews: list[str] = []
        reviews_dir = ws / "reviews"
        if reviews_dir.exists():
            for f in reviews_dir.rglob("*.yml"):
                reviews.append(str(f.relative_to(sandbox.sandbox_dir)))
            for f in reviews_dir.rglob("*.md"):
                reviews.append(str(f.relative_to(sandbox.sandbox_dir)))

        code_files: list[str] = []
        test_files: list[str] = []
        src_dir = sandbox.sandbox_dir / "src"
        tests_dir = sandbox.sandbox_dir / "tests"
        if src_dir.exists():
            code_files = sorted(f.name for f in src_dir.rglob("*.py"))
        if tests_dir.exists():
            test_files = sorted(f.name for f in tests_dir.rglob("*.py"))

        manifest = ArtifactManifest(
            sandbox_path=str(sandbox.sandbox_dir),
            frozen_at=datetime.now(timezone.utc).isoformat(),
            events_line_count=events_count,
            feature_vectors=feature_vectors,
            review_files=reviews,
            generated_code_files=code_files,
            generated_test_files=test_files,
            provenance=sandbox.provenance.to_dict(),
        )

        meta_dir = sandbox.sandbox_dir / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)
        (meta_dir / "artifact_manifest.json").write_text(
            json.dumps(dataclasses.asdict(manifest), indent=2)
        )

        return cls(sandbox.sandbox_dir, manifest)


# ===========================================================================
# Bug Report
# ===========================================================================


@dataclasses.dataclass
class BugReport:
    """A traced finding from forensic diagnosis.

    Chain: intent → req → design → code → tests → events → monitor
    Every field in the chain should be populated for critical/major bugs.
    """
    bug_id: str
    severity: str             # critical | major | minor | advisory
    title: str
    observation: str          # what was observed in the artifact set
    expected: str             # what should have been observed
    req_key: Optional[str]    # REQ-* that this violates
    design_ref: Optional[str] # ADR-* or design doc section
    code_location: Optional[str]  # file:function or file:line
    test_gap: Optional[str]   # test file::class::method that would catch this
    event_evidence: Optional[str]  # relevant events.jsonl lines or summary


# ===========================================================================
# Forensic Diagnosis
# ===========================================================================


@dataclasses.dataclass
class ForensicDiagnosis:
    """Structured forensic diagnosis of a sandbox run artifact set."""
    sandbox_path: str
    diagnosed_at: str
    total_events: int
    event_type_counts: dict       # {event_type: count}
    first_event: Optional[dict]
    last_event: Optional[dict]
    feature_vectors_found: list
    converged_features: list
    pending_features: list
    genesis_installed_event_present: bool
    installer_version: Optional[str]
    code_files_generated: list
    test_files_generated: list
    bugs: list                    # list of BugReport (serialised as dicts)


class ForensicAnalyzer:
    """Analyzes a frozen sandbox artifact set and produces a diagnosis.

    Writes forensic_diagnosis.md and forensic_diagnosis.json to .e2e-meta/.
    """

    def __init__(self, sandbox_dir: pathlib.Path):
        self.sandbox_dir = sandbox_dir
        self.workspace_dir = sandbox_dir / ".ai-workspace"

    def analyze(self) -> ForensicDiagnosis:
        events = self._load_events()
        features = self._load_feature_vectors()
        bugs = self._detect_bugs(events, features)

        event_types = Counter(e.get("event_type", "unknown") for e in events)

        converged = self._find_converged_features(features)
        pending = [f.get("id", "?") for f in features if f.get("id") not in converged]

        genesis_installed = any(
            e.get("event_type") == "genesis_installed" for e in events
        )
        installer_version: Optional[str] = None
        for e in events:
            if e.get("event_type") == "genesis_installed":
                installer_version = e.get("data", {}).get("version")
                break

        code_files = sorted(
            f.name for f in (self.sandbox_dir / "src").rglob("*.py")
        ) if (self.sandbox_dir / "src").exists() else []
        test_files = sorted(
            f.name for f in (self.sandbox_dir / "tests").rglob("*.py")
        ) if (self.sandbox_dir / "tests").exists() else []

        diagnosis = ForensicDiagnosis(
            sandbox_path=str(self.sandbox_dir),
            diagnosed_at=datetime.now(timezone.utc).isoformat(),
            total_events=len(events),
            event_type_counts=dict(event_types),
            first_event=events[0] if events else None,
            last_event=events[-1] if events else None,
            feature_vectors_found=[f.get("id", "?") for f in features],
            converged_features=converged,
            pending_features=pending,
            genesis_installed_event_present=genesis_installed,
            installer_version=installer_version,
            code_files_generated=code_files,
            test_files_generated=test_files,
            bugs=[dataclasses.asdict(b) for b in bugs],
        )

        meta_dir = self.sandbox_dir / ".e2e-meta"
        meta_dir.mkdir(exist_ok=True)
        self._write_forensic_md(diagnosis, bugs, meta_dir / "forensic_diagnosis.md")
        (meta_dir / "forensic_diagnosis.json").write_text(
            json.dumps(dataclasses.asdict(diagnosis), indent=2)
        )

        return diagnosis

    # -----------------------------------------------------------------------

    def _load_events(self) -> list[dict]:
        events_file = self.workspace_dir / "events" / "events.jsonl"
        if not events_file.exists():
            return []
        events = []
        for line in events_file.read_text().splitlines():
            line = line.strip()
            if line:
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
        return events

    def _load_feature_vectors(self) -> list[dict]:
        try:
            import yaml
        except ImportError:
            return []

        features = []
        for subdir in ["active", "completed"]:
            d = self.workspace_dir / "features" / subdir
            if not d.exists():
                continue
            for f in sorted(d.glob("*.yml")):
                try:
                    data = yaml.safe_load(f.read_text())
                    if data and isinstance(data, dict):
                        features.append(data)
                except Exception:
                    pass
        return features

    def _find_converged_features(self, features: list[dict]) -> list[str]:
        converged = []
        for f in features:
            fid = f.get("id", "?")
            status = f.get("status", "")
            if status == "converged":
                converged.append(fid)
                continue
            # Check trajectory: all edges converged
            traj = f.get("trajectory", {})
            if traj and all(
                e.get("status") == "converged" for e in traj.values()
                if isinstance(e, dict)
            ):
                converged.append(fid)
        return converged

    def _detect_bugs(
        self, events: list[dict], features: list[dict]
    ) -> list[BugReport]:
        bugs: list[BugReport] = []
        seq = [0]

        def next_id(severity: str) -> str:
            seq[0] += 1
            return f"BUG-{severity.upper()[:3]}-{seq[0]:03d}"

        events_file = self.workspace_dir / "events" / "events.jsonl"
        engine_main = self.sandbox_dir / ".genesis" / "genesis" / "__main__.py"
        commands_dir = self.sandbox_dir / ".claude" / "commands"

        # Bug: events.jsonl missing
        if not events_file.exists():
            bugs.append(BugReport(
                bug_id=next_id("critical"),
                severity="critical",
                title="events.jsonl not created by installer",
                observation=".ai-workspace/events/events.jsonl does not exist",
                expected="Installer creates events.jsonl as part of workspace setup",
                req_key="REQ-TOOL-007",
                design_ref="ADR-S-012 (event stream as model substrate)",
                code_location="gen-setup.py:setup_workspace()",
                test_gap="TestInstallerProvenance::test_workspace_structure_created",
                event_evidence="file absent",
            ))

        # Bug: events.jsonl empty
        elif len(events) == 0:
            bugs.append(BugReport(
                bug_id=next_id("critical"),
                severity="critical",
                title="Event log is empty after install",
                observation="events.jsonl exists but contains no events",
                expected="genesis_installed event should be present after successful install",
                req_key="REQ-TOOL-011",
                design_ref="ADR-S-012",
                code_location="gen-setup.py:emit_install_event()",
                test_gap="TestInstallerProvenance::test_genesis_installed_event_emitted",
                event_evidence="events.jsonl is empty",
            ))

        # Bug: no genesis_installed event
        elif not any(e.get("event_type") == "genesis_installed" for e in events):
            types_seen = [e.get("event_type") for e in events]
            bugs.append(BugReport(
                bug_id=next_id("critical"),
                severity="critical",
                title="No genesis_installed event emitted by installer",
                observation=f"events.jsonl has {len(events)} events but none are genesis_installed",
                expected="Installer emits genesis_installed on successful install (REQ-TOOL-011)",
                req_key="REQ-TOOL-011",
                design_ref="ADR-020 (installability contract)",
                code_location="gen-setup.py:emit_install_event()",
                test_gap="TestInstallerProvenance::test_genesis_installed_event_emitted",
                event_evidence=f"Event types seen: {types_seen}",
            ))

        # Bug: engine not installed
        if not engine_main.exists():
            bugs.append(BugReport(
                bug_id=next_id("critical"),
                severity="critical",
                title="Engine not installed to .genesis/genesis/",
                observation=".genesis/genesis/__main__.py not present",
                expected="Installer copies all ENGINE_FILES to .genesis/genesis/",
                req_key="REQ-TOOL-011",
                design_ref="ADR-020",
                code_location="gen-setup.py:setup_engine()",
                test_gap="TestInstallerProvenance::test_engine_files_installed",
                event_evidence=None,
            ))

        # Bug: commands not installed
        if not commands_dir.exists() or not list(commands_dir.glob("gen-*.md")):
            bugs.append(BugReport(
                bug_id=next_id("major"),
                severity="major",
                title="gen-* commands not installed",
                observation=f".claude/commands/ missing or has no gen-*.md files",
                expected="Installer copies all command files to .claude/commands/",
                req_key="REQ-TOOL-003",
                design_ref="ADR-012 (two-command UX layer)",
                code_location="gen-setup.py:setup_commands()",
                test_gap="TestInstallerProvenance::test_commands_installed",
                event_evidence=None,
            ))

        return bugs

    def _write_forensic_md(
        self,
        d: ForensicDiagnosis,
        bugs: list[BugReport],
        path: pathlib.Path,
    ) -> None:
        lines = [
            "# Forensic Diagnosis",
            "",
            f"**Sandbox**: `{d.sandbox_path}`",
            f"**Diagnosed**: {d.diagnosed_at}",
            "",
            "## Event Stream",
            "",
            f"- Total events: {d.total_events}",
            f"- genesis_installed: {'✅' if d.genesis_installed_event_present else '❌ MISSING'}",
            f"- Installer version: {d.installer_version or 'unknown'}",
            "",
            "**Event type counts**:",
            "",
        ]
        for et, count in sorted(d.event_type_counts.items()):
            lines.append(f"  - `{et}`: {count}")
        lines += [
            "",
            "## Feature Vectors",
            "",
            f"- Found: {d.feature_vectors_found or '(none)'}",
            f"- Converged: {d.converged_features or '(none)'}",
            f"- Pending: {d.pending_features or '(none)'}",
            "",
            "## Generated Artifacts",
            "",
            f"- Code files: {d.code_files_generated or '(none)'}",
            f"- Test files: {d.test_files_generated or '(none)'}",
            "",
            "## Bug Reports",
            "",
        ]
        if not bugs:
            lines.append("No bugs found. ✅")
        else:
            for bug in bugs:
                lines += [
                    f"### {bug.bug_id}: {bug.title}",
                    "",
                    f"**Severity**: `{bug.severity}`  ",
                    f"**Observation**: {bug.observation}  ",
                    f"**Expected**: {bug.expected}",
                    "",
                    "**Traceability chain**:",
                    f"- REQ: `{bug.req_key or 'N/A'}`",
                    f"- Design: `{bug.design_ref or 'N/A'}`",
                    f"- Code: `{bug.code_location or 'N/A'}`",
                    f"- Test gap: `{bug.test_gap or 'N/A'}`",
                    f"- Evidence: {bug.event_evidence or 'N/A'}",
                    "",
                ]
        path.write_text("\n".join(lines))


# ===========================================================================
# Headless runner for full E2E (Claude required)
# ===========================================================================


class _HeadlessResult:
    def __init__(
        self,
        returncode: int,
        elapsed: float,
        timed_out: bool,
        log_dir: pathlib.Path,
    ):
        self.returncode = returncode
        self.elapsed = elapsed
        self.timed_out = timed_out
        self.log_dir = log_dir

    @property
    def stdout(self) -> str:
        p = self.log_dir / "stdout.log"
        return p.read_text(errors="replace") if p.exists() else ""

    @property
    def stderr(self) -> str:
        p = self.log_dir / "stderr.log"
        return p.read_text(errors="replace") if p.exists() else ""


def _kill_pg(proc: subprocess.Popen) -> None:
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


def _run_headless(
    project_dir: pathlib.Path,
    prompt: str,
    *,
    model: str = "sonnet",
    max_budget_usd: float = 3.00,
    wall_timeout: float = 900.0,
    stall_timeout: float = 180.0,
) -> _HeadlessResult:
    """Run claude -p in the sandbox with wall timeout and budget cap."""
    log_dir = project_dir / ".e2e-meta"
    log_dir.mkdir(parents=True, exist_ok=True)
    stdout_log = log_dir / "claude_stdout.log"
    stderr_log = log_dir / "claude_stderr.log"

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

    def _ts_writer(stream, log_path: pathlib.Path) -> threading.Thread:
        def _run():
            with open(log_path, "w", buffering=1) as f:
                for raw in iter(stream.readline, ""):
                    ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
                    f.write(f"[{ts}] {raw}")
        t = threading.Thread(target=_run, daemon=True)
        t.start()
        return t

    proc = subprocess.Popen(
        cmd, cwd=str(project_dir),
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, env=env,
        start_new_session=True,
    )
    _ts_writer(proc.stdout, stdout_log)
    _ts_writer(proc.stderr, stderr_log)

    def watchdog():
        nonlocal timed_out
        last_activity = time.time()
        last_size = 0

        while proc.poll() is None:
            time.sleep(10)
            now = time.time()
            if now - start > wall_timeout:
                timed_out = True
                _kill_pg(proc)
                return
            try:
                cur_size = stderr_log.stat().st_size if stderr_log.exists() else 0
            except OSError:
                cur_size = last_size

            if cur_size != last_size:
                last_activity = now
                last_size = cur_size

            if now - last_activity > stall_timeout:
                timed_out = True
                _kill_pg(proc)
                return

    wd = threading.Thread(target=watchdog, daemon=True)
    wd.start()
    proc.wait()
    elapsed = time.time() - start

    return _HeadlessResult(
        returncode=proc.returncode or 0,
        elapsed=elapsed,
        timed_out=timed_out,
        log_dir=log_dir,
    )


# ===========================================================================
# Session-scoped fixtures
# ===========================================================================

_factory = SandboxFactory()
_installer = SandboxInstaller()


@pytest.fixture(scope="session")
def sandbox_dir() -> pathlib.Path:
    """Create a fresh named sandbox directory with template project files."""
    d = _factory.allocate_directory()
    _factory.scaffold_template(d)
    return d


@pytest.fixture(scope="session")
def installed_sandbox(sandbox_dir: pathlib.Path) -> InstalledSandbox:
    """Install Genesis into the sandbox using the real installer (local source mode)."""
    return _installer.install(sandbox_dir)


@pytest.fixture(scope="session")
def frozen_artifacts(installed_sandbox: InstalledSandbox) -> FrozenArtifactSet:
    """Freeze the sandbox workspace as immutable evidence."""
    return installed_sandbox.freeze()


@pytest.fixture(scope="session")
def forensic_diagnosis(installed_sandbox: InstalledSandbox) -> ForensicDiagnosis:
    """Run forensic analysis on the installed sandbox."""
    return ForensicAnalyzer(installed_sandbox.sandbox_dir).analyze()


# ===========================================================================
# Tests: Sandbox Creation
# ===========================================================================


class TestSandboxCreation:
    """Sandbox factory creates correctly named, isolated directories."""

    def test_naming_pattern(self, sandbox_dir: pathlib.Path):
        """Sandbox name follows sandbox.e2etst_{datetime}_{seq:04d}."""
        # Codex E2E criterion 1: fresh versioned sandbox
        pattern = re.compile(r"^sandbox\.e2etst_\d{8}T\d{6}_\d{4}$")
        assert pattern.match(sandbox_dir.name), (
            f"Name '{sandbox_dir.name}' does not match sandbox.e2etst_{{datetime}}_{{seq}}"
        )

    def test_location_is_under_runs_dir(self, sandbox_dir: pathlib.Path):
        """Sandbox is created under runs/, not /tmp."""
        assert RUNS_DIR in sandbox_dir.parents, (
            f"Sandbox '{sandbox_dir}' is not under RUNS_DIR '{RUNS_DIR}'"
        )

    def test_not_inside_source_code_dirs(self, sandbox_dir: pathlib.Path):
        """Sandbox is not inside the engine or installer source directories."""
        engine_dir = PROJECT_ROOT / "imp_claude" / "code" / "genesis"
        installer_dir = PROJECT_ROOT / "imp_claude" / "code" / "installers"
        assert engine_dir not in sandbox_dir.parents, "Sandbox inside engine source"
        assert installer_dir not in sandbox_dir.parents, "Sandbox inside installer source"

    def test_not_in_tmp(self, sandbox_dir: pathlib.Path):
        """Sandbox is a real named directory, not a /tmp ephemeral."""
        assert not str(sandbox_dir).startswith("/tmp"), "Sandbox must not be in /tmp"
        assert not str(sandbox_dir).startswith("/var/folders"), (
            "Sandbox must not be in macOS temp /var/folders"
        )

    def test_template_has_intent_with_req_keys(self, sandbox_dir: pathlib.Path):
        """Template specification/INTENT.md contains REQ keys."""
        intent = sandbox_dir / "specification" / "INTENT.md"
        assert intent.exists(), "specification/INTENT.md missing"
        assert "REQ-F-HELLO-001" in intent.read_text()

    def test_template_has_pyproject(self, sandbox_dir: pathlib.Path):
        """Template has pyproject.toml."""
        assert (sandbox_dir / "pyproject.toml").exists()

    def test_template_has_claude_md(self, sandbox_dir: pathlib.Path):
        """Template has CLAUDE.md (installer will inject bootloader)."""
        assert (sandbox_dir / "CLAUDE.md").exists()

    def test_template_has_git_repo(self, sandbox_dir: pathlib.Path):
        """Template is a git repository (installer installs hooks)."""
        assert (sandbox_dir / ".git").is_dir(), "No .git — installer hooks won't install"


# ===========================================================================
# Tests: Installer Provenance
# ===========================================================================


class TestInstallerProvenance:
    """Installer runs cleanly with full provenance capture."""

    def test_installer_exits_zero(self, installed_sandbox: InstalledSandbox):
        """Installer exits 0 with local source mode.

        Codex criterion 2: Install Genesis using the installer for the candidate version.
        """
        assert installed_sandbox.provenance.installer_exit_code == 0, (
            f"Installer failed (exit {installed_sandbox.provenance.installer_exit_code}).\n"
            f"stdout:\n{installed_sandbox.installer_stdout[-3000:]}\n"
            f"stderr:\n{installed_sandbox.installer_stderr[-1000:]}"
        )

    def test_provenance_json_written(self, installed_sandbox: InstalledSandbox):
        """provenance.json written to .e2e-meta/."""
        pf = installed_sandbox.sandbox_dir / ".e2e-meta" / "provenance.json"
        assert pf.exists(), ".e2e-meta/provenance.json not created"
        data = json.loads(pf.read_text())
        for field in ("version", "git_commit", "timestamp_start", "installer_exit_code"):
            assert field in data, f"provenance.json missing '{field}'"

    def test_version_captured(self, installed_sandbox: InstalledSandbox):
        """Provenance records the genesis version."""
        assert installed_sandbox.provenance.version not in ("unknown", ""), (
            "Version not captured in provenance"
        )

    def test_git_commit_captured(self, installed_sandbox: InstalledSandbox):
        """Provenance records the source git commit hash."""
        commit = installed_sandbox.provenance.git_commit
        assert commit != "unknown" and len(commit) >= 7, (
            f"Git commit not captured: '{commit}'"
        )

    def test_installer_source_is_local(self, installed_sandbox: InstalledSandbox):
        """Provenance shows local source mode (not network — reproducible)."""
        assert installed_sandbox.provenance.installer_source.startswith("local:"), (
            f"Expected local: source, got {installed_sandbox.provenance.installer_source}"
        )

    def test_timestamps_are_iso8601(self, installed_sandbox: InstalledSandbox):
        """Both timestamps are ISO 8601 format."""
        pat = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        assert pat.match(installed_sandbox.provenance.timestamp_start), (
            f"timestamp_start not ISO 8601: {installed_sandbox.provenance.timestamp_start}"
        )
        assert pat.match(installed_sandbox.provenance.timestamp_end), (
            f"timestamp_end not ISO 8601: {installed_sandbox.provenance.timestamp_end}"
        )

    def test_genesis_installed_event_emitted(self, installed_sandbox: InstalledSandbox):
        """Installer emits genesis_installed event to events.jsonl.

        Validates: REQ-TOOL-011 (installability), REQ-LIFE-002 (telemetry).
        """
        events = installed_sandbox.load_events()
        install_events = [e for e in events if e.get("event_type") == "genesis_installed"]
        assert install_events, (
            f"No genesis_installed event found in events.jsonl. "
            f"Event types: {[e.get('event_type') for e in events]}\n"
            f"Installer stdout:\n{installed_sandbox.installer_stdout[-2000:]}"
        )

    def test_genesis_installed_event_has_required_fields(
        self, installed_sandbox: InstalledSandbox
    ):
        """genesis_installed event carries version, engine_files, commands."""
        events = installed_sandbox.load_events()
        evt = next(
            (e for e in events if e.get("event_type") == "genesis_installed"), None
        )
        assert evt is not None
        data = evt.get("data", {})
        for field in ("version", "engine_files", "commands"):
            assert data.get(field) is not None, (
                f"genesis_installed.data.{field} missing or null"
            )

    def test_engine_main_installed(self, installed_sandbox: InstalledSandbox):
        """.genesis/genesis/__main__.py exists after install."""
        assert (installed_sandbox.engine_dir / "__main__.py").exists(), (
            ".genesis/genesis/__main__.py missing — engine not installed"
        )

    def test_engine_config_installed(self, installed_sandbox: InstalledSandbox):
        """Engine config directory contains edge params."""
        edge_params_dir = installed_sandbox.engine_dir / "config" / "edge_params"
        assert edge_params_dir.exists(), "Engine config/edge_params/ not installed"
        ymls = list(edge_params_dir.glob("*.yml"))
        assert len(ymls) >= 5, f"Only {len(ymls)} edge param files, expected >=5"

    def test_commands_installed(self, installed_sandbox: InstalledSandbox):
        """gen-start.md and gen-iterate.md present in .claude/commands/."""
        assert (installed_sandbox.commands_dir / "gen-start.md").exists(), (
            "gen-start.md not installed"
        )
        assert (installed_sandbox.commands_dir / "gen-iterate.md").exists(), (
            "gen-iterate.md not installed"
        )

    def test_workspace_structure_created(self, installed_sandbox: InstalledSandbox):
        """.ai-workspace/ has required subdirectories."""
        ws = installed_sandbox.workspace_dir
        for subpath in [
            "events",
            "features/active",
            "features/completed",
            "graph",
        ]:
            assert (ws / subpath).is_dir(), f".ai-workspace/{subpath}/ missing"

    def test_graph_topology_installed(self, installed_sandbox: InstalledSandbox):
        """graph_topology.yml present in .ai-workspace/graph/."""
        gt = installed_sandbox.workspace_dir / "graph" / "graph_topology.yml"
        assert gt.exists(), ".ai-workspace/graph/graph_topology.yml missing"

    def test_bootloader_injected_into_claude_md(self, installed_sandbox: InstalledSandbox):
        """Genesis Bootloader is injected into CLAUDE.md."""
        claude_md = installed_sandbox.sandbox_dir / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md missing after install"
        content = claude_md.read_text()
        assert "<!-- GENESIS_BOOTLOADER_START -->" in content, (
            "Bootloader not injected into CLAUDE.md"
        )

    def test_verify_command_passes(self, installed_sandbox: InstalledSandbox):
        """gen-setup.py verify exits 0 for a successful installation."""
        result = subprocess.run(
            [
                sys.executable, str(INSTALLER),
                "--source", str(PROJECT_ROOT),
                "--target", str(installed_sandbox.sandbox_dir),
                "verify",
            ],
            capture_output=True, text=True, timeout=60,
        )
        assert result.returncode == 0, (
            f"verify failed (exit {result.returncode}):\n{result.stdout[-3000:]}"
        )

    def test_installer_stdout_log_written(self, installed_sandbox: InstalledSandbox):
        """installer_stdout.log captured in .e2e-meta/."""
        log = installed_sandbox.sandbox_dir / ".e2e-meta" / "installer_stdout.log"
        assert log.exists() and log.stat().st_size > 0, (
            "Installer stdout not logged to .e2e-meta/"
        )


# ===========================================================================
# Tests: Engine in Sandbox
# ===========================================================================


class TestEngineInSandbox:
    """Engine runs correctly when invoked from the installed sandbox."""

    def test_engine_importable(self, installed_sandbox: InstalledSandbox):
        """Engine can be launched with PYTHONPATH=.genesis (no ImportError)."""
        result = installed_sandbox.run_engine(["--help"])
        assert "ImportError" not in result.stderr, (
            f"ImportError in engine:\n{result.stderr[:1000]}"
        )
        assert "ModuleNotFoundError" not in result.stderr, (
            f"ModuleNotFoundError:\n{result.stderr[:1000]}"
        )

    def test_engine_help_exits_cleanly(self, installed_sandbox: InstalledSandbox):
        """Engine --help exits 0 or 2 (argparse), not 1 (crash)."""
        result = installed_sandbox.run_engine(["--help"])
        assert result.returncode in (0, 2), (
            f"Engine --help crashed (exit {result.returncode}):\n{result.stderr[:500]}"
        )

    def test_engine_does_not_touch_source_tree(self, installed_sandbox: InstalledSandbox):
        """Engine stderr does not reference source tree paths when run from sandbox."""
        result = installed_sandbox.run_engine(
            ["check-tags", "--path", str(installed_sandbox.sandbox_dir / "src")]
        )
        # Engine should not reference the source code directory in its output
        source_code_path = str(PROJECT_ROOT / "imp_claude" / "code" / "genesis")
        assert source_code_path not in result.stderr, (
            f"Engine referenced source tree path '{source_code_path}' — "
            f"engine may be running from source, not sandbox"
        )

    def test_engine_workspace_is_sandbox(self, installed_sandbox: InstalledSandbox):
        """Engine config reads from sandbox .ai-workspace/graph/."""
        # The graph topology file should exist in the sandbox
        gt = installed_sandbox.workspace_dir / "graph" / "graph_topology.yml"
        assert gt.exists(), (
            "Engine cannot run from sandbox — .ai-workspace/graph/graph_topology.yml missing"
        )


# ===========================================================================
# Tests: Frozen Artifact Set
# ===========================================================================


class TestFrozenArtifactSet:
    """Artifact freezing creates a reproducible manifest of evidence.

    Codex criterion 4: Preserve .ai-workspace as immutable incident artifact set.
    """

    def test_manifest_file_created(self, frozen_artifacts: FrozenArtifactSet):
        """artifact_manifest.json written to .e2e-meta/."""
        mf = frozen_artifacts.sandbox_dir / ".e2e-meta" / "artifact_manifest.json"
        assert mf.exists(), ".e2e-meta/artifact_manifest.json not created"

    def test_manifest_has_frozen_at(self, frozen_artifacts: FrozenArtifactSet):
        """Manifest records when artifacts were frozen (ISO 8601)."""
        assert frozen_artifacts.manifest.frozen_at, "frozen_at not set"
        assert re.match(r"^\d{4}-\d{2}-\d{2}T", frozen_artifacts.manifest.frozen_at)

    def test_manifest_event_count_nonzero(self, frozen_artifacts: FrozenArtifactSet):
        """Manifest records at least 1 event (genesis_installed)."""
        assert frozen_artifacts.manifest.events_line_count >= 1, (
            f"Expected >=1 events at freeze, "
            f"got {frozen_artifacts.manifest.events_line_count}"
        )

    def test_manifest_has_provenance(self, frozen_artifacts: FrozenArtifactSet):
        """Manifest embeds installer provenance for reproducibility."""
        prov = frozen_artifacts.manifest.provenance
        assert prov, "Provenance absent from manifest"
        for field in ("version", "git_commit", "installer_exit_code"):
            assert field in prov, f"Provenance missing '{field}'"

    def test_manifest_is_json_readable(self, frozen_artifacts: FrozenArtifactSet):
        """artifact_manifest.json can be re-read and contains all key fields."""
        mf = frozen_artifacts.sandbox_dir / ".e2e-meta" / "artifact_manifest.json"
        data = json.loads(mf.read_text())
        for key in ("sandbox_path", "frozen_at", "events_line_count", "provenance"):
            assert key in data, f"artifact_manifest.json missing '{key}'"

    def test_manifest_sandbox_path_matches(self, frozen_artifacts: FrozenArtifactSet):
        """Manifest sandbox_path matches the actual sandbox directory."""
        assert frozen_artifacts.manifest.sandbox_path == str(frozen_artifacts.sandbox_dir)


# ===========================================================================
# Tests: Forensic Diagnosis
# ===========================================================================


class TestForensicDiagnosis:
    """Forensic analyzer produces structured diagnosis of sandbox artifacts.

    Codex criterion 5: Do forensic diagnosis against the artifact set.
    """

    def test_diagnosis_is_created(self, forensic_diagnosis: ForensicDiagnosis):
        """ForensicDiagnosis object is created."""
        assert forensic_diagnosis is not None
        assert forensic_diagnosis.sandbox_path

    def test_total_events_nonzero(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic diagnosis counts at least 1 event (genesis_installed)."""
        assert forensic_diagnosis.total_events >= 1, (
            f"Expected >=1 events, got {forensic_diagnosis.total_events}"
        )

    def test_event_types_mapped(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic diagnosis maps event type frequencies."""
        assert isinstance(forensic_diagnosis.event_type_counts, dict)
        assert len(forensic_diagnosis.event_type_counts) >= 1

    def test_genesis_installed_detected(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic diagnosis detects genesis_installed event."""
        assert forensic_diagnosis.genesis_installed_event_present, (
            "Forensic diagnosis did not detect genesis_installed — "
            f"event types: {forensic_diagnosis.event_type_counts}"
        )

    def test_installer_version_extracted(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic diagnosis extracts installer version from genesis_installed event."""
        assert forensic_diagnosis.installer_version, (
            "installer_version not extracted from genesis_installed event"
        )

    def test_no_critical_bugs_after_clean_install(
        self, forensic_diagnosis: ForensicDiagnosis
    ):
        """No critical bugs detected after a successful installation.

        If the installer ran cleanly, the forensic analyzer should find no
        critical structural issues with the sandbox.
        """
        critical = [
            b for b in forensic_diagnosis.bugs
            if isinstance(b, dict) and b.get("severity") == "critical"
        ]
        assert not critical, (
            f"Critical bugs found after successful install:\n"
            + "\n".join(
                f"  {b['bug_id']}: {b['title']}\n    {b['observation']}"
                for b in critical
            )
        )

    def test_forensic_md_written(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic report written to .e2e-meta/forensic_diagnosis.md."""
        sandbox = pathlib.Path(forensic_diagnosis.sandbox_path)
        report = sandbox / ".e2e-meta" / "forensic_diagnosis.md"
        assert report.exists(), ".e2e-meta/forensic_diagnosis.md not created"
        content = report.read_text()
        assert "# Forensic Diagnosis" in content
        assert "Event Stream" in content

    def test_forensic_json_has_required_keys(self, forensic_diagnosis: ForensicDiagnosis):
        """Forensic JSON report is readable and contains all key fields."""
        sandbox = pathlib.Path(forensic_diagnosis.sandbox_path)
        report = sandbox / ".e2e-meta" / "forensic_diagnosis.json"
        assert report.exists()
        data = json.loads(report.read_text())
        for key in (
            "sandbox_path", "diagnosed_at", "total_events",
            "event_type_counts", "genesis_installed_event_present", "bugs",
        ):
            assert key in data, f"forensic_diagnosis.json missing '{key}'"


# ===========================================================================
# Tests: Bug Report Chain Tracing (seeded broken sandbox)
# ===========================================================================


class TestBugReportChainTracing:
    """Bug report generator produces fully-traced findings.

    Codex criterion 6: Bug reports traced across
    intent → requirements → design → code → tests → events → monitor.

    These tests use a deliberately incomplete sandbox to force bug detection.
    """

    @pytest.fixture
    def broken_sandbox(self, tmp_path: pathlib.Path) -> pathlib.Path:
        """A sandbox where the installer was NOT run (events.jsonl absent)."""
        d = tmp_path / "broken_sandbox"
        d.mkdir()
        _factory.scaffold_template(d)
        # Create partial workspace without events.jsonl or engine
        ws = d / ".ai-workspace"
        (ws / "events").mkdir(parents=True)
        (ws / "features" / "active").mkdir(parents=True)
        (ws / "features" / "completed").mkdir()
        # No events.jsonl, no .genesis/, no .claude/commands/
        return d

    @pytest.fixture
    def empty_events_sandbox(self, tmp_path: pathlib.Path) -> pathlib.Path:
        """A sandbox with events.jsonl present but empty."""
        d = tmp_path / "empty_events"
        d.mkdir()
        _factory.scaffold_template(d)
        ws = d / ".ai-workspace"
        events_dir = ws / "events"
        events_dir.mkdir(parents=True)
        (events_dir / "events.jsonl").write_text("")
        (ws / "features" / "active").mkdir(parents=True)
        (ws / "features" / "completed").mkdir()
        return d

    def test_missing_events_generates_critical_bug(
        self, broken_sandbox: pathlib.Path
    ):
        """Missing events.jsonl produces a critical bug report."""
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        critical = [
            b for b in diagnosis.bugs
            if isinstance(b, dict) and b.get("severity") == "critical"
        ]
        assert critical, "Expected critical bug for missing events.jsonl"

    def test_empty_events_generates_critical_bug(
        self, empty_events_sandbox: pathlib.Path
    ):
        """Empty events.jsonl produces a critical bug report."""
        diagnosis = ForensicAnalyzer(empty_events_sandbox).analyze()
        critical = [
            b for b in diagnosis.bugs
            if isinstance(b, dict) and b.get("severity") == "critical"
        ]
        assert critical, "Expected critical bug for empty events.jsonl"

    def test_every_critical_bug_has_req_key(self, broken_sandbox: pathlib.Path):
        """Every critical/major bug has a REQ key for chain tracing.

        Codex: traces must cover intent → requirements.
        """
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        for b in diagnosis.bugs:
            if not isinstance(b, dict):
                continue
            if b.get("severity") in ("critical", "major"):
                assert b.get("req_key"), (
                    f"Bug {b['bug_id']} ({b['title']}) has no req_key — "
                    f"cannot trace chain req → design → code"
                )

    def test_every_critical_bug_has_design_ref(self, broken_sandbox: pathlib.Path):
        """Every critical bug has a design reference (ADR or design doc).

        Codex: traces must cover requirements → design.
        """
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        for b in diagnosis.bugs:
            if isinstance(b, dict) and b.get("severity") == "critical":
                assert b.get("design_ref"), (
                    f"Critical bug {b['bug_id']} ({b['title']}) has no design_ref — "
                    f"cannot trace chain design → code"
                )

    def test_every_critical_bug_has_code_location(
        self, broken_sandbox: pathlib.Path
    ):
        """Every critical bug has a code location.

        Codex: traces must cover design → code.
        """
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        for b in diagnosis.bugs:
            if isinstance(b, dict) and b.get("severity") == "critical":
                assert b.get("code_location"), (
                    f"Critical bug {b['bug_id']} has no code_location"
                )

    def test_every_critical_bug_has_test_gap(self, broken_sandbox: pathlib.Path):
        """Every critical bug references the test that would catch it.

        Codex: traces must cover code → tests.
        """
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        for b in diagnosis.bugs:
            if isinstance(b, dict) and b.get("severity") == "critical":
                assert b.get("test_gap"), (
                    f"Critical bug {b['bug_id']} has no test_gap — "
                    f"cannot trace chain tests → events"
                )

    def test_missing_engine_generates_bug(self, broken_sandbox: pathlib.Path):
        """Missing .genesis/genesis/ generates a critical engine bug."""
        diagnosis = ForensicAnalyzer(broken_sandbox).analyze()
        engine_bugs = [
            b for b in diagnosis.bugs
            if isinstance(b, dict) and "engine" in b.get("title", "").lower()
        ]
        assert engine_bugs, (
            f"Expected engine bug, got: {[b.get('title') for b in diagnosis.bugs]}"
        )

    def test_forensic_md_contains_chain_tracing(
        self, broken_sandbox: pathlib.Path
    ):
        """Forensic markdown report contains Traceability chain section."""
        ForensicAnalyzer(broken_sandbox).analyze()
        report = broken_sandbox / ".e2e-meta" / "forensic_diagnosis.md"
        assert report.exists()
        content = report.read_text()
        assert "Traceability chain" in content or "REQ:" in content, (
            "Forensic report does not include chain tracing"
        )


# ===========================================================================
# Tests: Full Sandbox E2E (Claude required)
# ===========================================================================


class TestSandboxFullE2E:
    """Full E2E convergence against installer-bootstrapped sandbox.

    Codex criterion 3: Run the real E2E/UAT suite against the installed sandbox,
    not the source tree.

    These tests require the Claude CLI and consume API budget.
    """

    @pytest.fixture(scope="class")
    def sandbox_with_feature(
        self, installed_sandbox: InstalledSandbox
    ) -> InstalledSandbox:
        """Write REQ-F-HELLO-001 feature vector into the installed sandbox."""
        active_dir = installed_sandbox.workspace_dir / "features" / "active"
        active_dir.mkdir(parents=True, exist_ok=True)
        fv_path = active_dir / "REQ-F-HELLO-001.yml"
        if not fv_path.exists():
            fv_path.write_text(SANDBOX_FEATURE_VECTOR)
        return installed_sandbox

    @pytest.mark.e2e
    @skip_no_claude
    def test_convergence_against_installed_sandbox(
        self, sandbox_with_feature: InstalledSandbox
    ):
        """gen-start --auto runs against the installed sandbox, not source tree.

        Codex: fresh sandbox + real installer + run against sandbox + preserve artifacts.
        """
        sb = sandbox_with_feature
        events_before = len(sb.load_events())

        result = _run_headless(
            sb.sandbox_dir,
            "/gen-start --auto --feature REQ-F-HELLO-001",
            max_budget_usd=3.00,
            wall_timeout=900.0,
            stall_timeout=180.0,
        )

        events_after = sb.load_events()

        assert not result.timed_out, (
            f"Run timed out after {result.elapsed:.0f}s"
        )
        assert result.returncode in (0, 3), (
            f"gen-start failed (exit {result.returncode}).\n"
            f"Events: {[e.get('event_type') for e in events_after]}\n"
            f"Stdout tail:\n{result.stdout[-3000:]}"
        )
        # Key: new events written to SANDBOX workspace
        assert len(events_after) > events_before, (
            "No new events written to sandbox workspace — "
            "Claude may have operated on source tree instead of sandbox"
        )

        # Freeze and diagnose
        frozen = sb.freeze()
        diagnosis = ForensicAnalyzer(sb.sandbox_dir).analyze()

        print(f"\n=== Sandbox E2E Summary ===")
        print(f"Events total: {diagnosis.total_events}")
        print(f"Event types: {diagnosis.event_type_counts}")
        print(f"Converged: {diagnosis.converged_features}")
        print(f"Pending: {diagnosis.pending_features}")
        print(f"Bugs: {len(diagnosis.bugs)}")
        for b in diagnosis.bugs:
            if isinstance(b, dict):
                print(f"  [{b.get('severity','?').upper()}] {b.get('bug_id')}: {b.get('title')}")

        # Codex criterion 4: artifacts preserved
        mf = sb.sandbox_dir / ".e2e-meta" / "artifact_manifest.json"
        assert mf.exists(), "Artifact manifest not created after run"

    @pytest.mark.e2e
    @skip_no_claude
    def test_engine_runs_in_sandbox_not_source_tree(
        self, sandbox_with_feature: InstalledSandbox
    ):
        """Engine emits events to sandbox events.jsonl, not source tree.

        Validates: the sandbox isolation guarantee — engine reads/writes
        to the sandbox workspace, not the main repo workspace.
        """
        sb = sandbox_with_feature
        # Check that no events appear in the main repo's events.jsonl
        main_events_file = (
            PROJECT_ROOT / ".ai-workspace" / "events" / "events.jsonl"
        )
        main_count_before = 0
        if main_events_file.exists():
            main_count_before = sum(
                1 for line in main_events_file.read_text().splitlines() if line.strip()
            )

        # Run engine directly in sandbox
        sb.run_engine(["check-tags", "--path", str(sb.sandbox_dir / "src")], timeout=15)

        main_count_after = 0
        if main_events_file.exists():
            main_count_after = sum(
                1 for line in main_events_file.read_text().splitlines() if line.strip()
            )

        assert main_count_after == main_count_before, (
            f"Engine ran in sandbox but wrote {main_count_after - main_count_before} "
            f"events to the main repo events.jsonl — sandbox isolation violated"
        )
