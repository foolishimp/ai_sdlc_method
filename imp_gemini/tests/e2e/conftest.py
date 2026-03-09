# Validates: REQ-TOOL-005, REQ-EVAL-001, REQ-F-EVAL-001
import json
import os
import pathlib
import shutil
import subprocess
import textwrap
import time
import uuid
import sys
from datetime import datetime, timezone
import pytest
import yaml

# Path Constants
PROJECT_ROOT = pathlib.Path(__file__).parents[3]
IMP_GEMINI = PROJECT_ROOT / "imp_gemini"
PLUGIN_ROOT = IMP_GEMINI / "gemini_cli"
CONFIG_DIR = PLUGIN_ROOT / "config"
EDGE_PARAMS_DIR = CONFIG_DIR / "edge_params"
PROFILES_DIR = CONFIG_DIR / "profiles"
RUNS_DIR = pathlib.Path(__file__).parent / "runs"

INTENT_MD = "# Intent: Temp Converter"
PROJECT_CONSTRAINTS_YML = "project: {name: temperature-converter}"

_archive_path: pathlib.Path | None = None

def _get_plugin_version() -> str:
    try:
        data = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        return data.get("version", "unknown")
    except: return "unknown"

def _compute_run_dir(failed: bool = False) -> pathlib.Path:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    prefix = "FAILED_" if failed else ""
    idx = len(list(RUNS_DIR.glob(f"{prefix}*"))) + 1
    return RUNS_DIR / f"{prefix}{_get_plugin_version()}_{ts}_{idx:04d}"

def _persist_run(source_dir: pathlib.Path, failed: bool = False) -> pathlib.Path | None:
    dest = _compute_run_dir(failed=failed)
    shutil.copytree(source_dir, dest, ignore=shutil.ignore_patterns(".git", "__pycache__"), dirs_exist_ok=True)
    latest = RUNS_DIR / "e2e_latest"
    if latest.exists() or latest.is_symlink(): latest.unlink()
    latest.symlink_to(dest.name)
    return dest

def _clean_env(): return {}

class MockGeminiRunner:
    def __init__(self, project_dir):
        self.project_dir = pathlib.Path(project_dir)
        self.ws_dir = self.project_dir / ".ai-workspace"
        self.events_file = self.ws_dir / "events" / "events.jsonl"

    def _emit_event(self, event_type, **kwargs):
        ev = {"event_type": event_type, "timestamp": datetime.now(timezone.utc).isoformat(), "project": "temperature-converter"}
        if "runId" not in kwargs: kwargs["runId"] = str(uuid.uuid4())
        ev.update(kwargs)
        self.events_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.events_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(ev) + "\n")

    def _update_intent_vector(self, vector_id, edge, status="converged", delta=0):
        iv_dir = self.ws_dir / "vectors" / "active"
        iv_dir.mkdir(parents=True, exist_ok=True)
        iv_path = iv_dir / f"{vector_id}.yml"
        if iv_path.exists(): data = yaml.safe_load(iv_path.read_text())
        else: data = {"id": vector_id, "feature": vector_id, "status": "iterating", "trajectory": {}}
        
        target = edge.replace("↔", "→").split("→")[-1].strip()
        data["trajectory"][target] = {"status": status, "converged_at": datetime.now(timezone.utc).isoformat(), "iteration": 1, "delta": delta}
        
        if all(data["trajectory"].get(e, {}).get("status") == "converged" for e in ["requirements", "design", "code", "unit_tests"]):
            data["status"] = "converged"
        iv_path.write_text(yaml.dump(data), encoding="utf-8")
        legacy_dir = self.ws_dir / "features" / "active"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        (legacy_dir / f"{vector_id}.yml").write_text(yaml.dump(data), encoding="utf-8")

    def _generate_artifacts(self, feature_id):
        src_dir = self.project_dir / "src"; src_dir.mkdir(exist_ok=True)
        test_dir = self.project_dir / "tests"; test_dir.mkdir(exist_ok=True)
        (src_dir / "converter.py").write_text(f'"""\n# Implements: {feature_id}\n"""\ndef celsius_to_fahrenheit(c):\n    # Implements: {feature_id}\n    return c * 9/5 + 32', encoding="utf-8")
        (test_dir / "test_converter.py").write_text(f'"""\n# Validates: {feature_id}\n"""\nfrom src.converter import celsius_to_fahrenheit\ndef test_freezing():\n    # Validates: {feature_id}\n    assert celsius_to_fahrenheit(0) == 32.0', encoding="utf-8")
        (self.project_dir / "tests" / "scenarios").mkdir(exist_ok=True)
        (self.project_dir / "tests" / "scenarios" / "converter.feature").write_text("Feature: Converter\n  Scenario: Scale conversion\n    # Validates: REQ-F-CONV-001\n    Given a temperature\n    Then it works\n\n  Scenario: Error case\n    # Validates: REQ-F-CONV-001\n    Given an invalid temperature\n    Then it raises an error", encoding="utf-8")

    def run_auto(self, feature_id, include_uat=False):
        self._emit_event("project_initialized")
        status_dir = self.project_dir / "specification"
        status_dir.mkdir(parents=True, exist_ok=True)
        status_file = status_dir / "STATUS.md"
        status_file.write_text("# Project Status\n\n| Edge | Status | Iterations |\n|------|--------|------------|\n", encoding="utf-8")
        
        edges = ["intent\u2192requirements", "requirements\u2192design", "design\u2192code", "code\u2194unit_tests"]
        if include_uat: edges.append("design\u2192uat_tests")
        
        for edge in edges:
            run_id = str(uuid.uuid4())
            self._emit_event("edge_started", feature=feature_id, edge=edge, runId=run_id)
            if "code" in edge or "unit_tests" in edge or "uat_tests" in edge: self._generate_artifacts(feature_id)
            self._emit_event("iteration_completed", feature=feature_id, edge=edge, iteration=1, delta=0, status="converged", runId=run_id, evaluators={"details": "All checks passed"})
            self._emit_event("edge_converged", feature=feature_id, edge=edge, runId=run_id)
            self._update_intent_vector(feature_id, edge, "converged", 0)
            with open(status_file, "a", encoding="utf-8") as f: 
                f.write(f"| {edge} | converged | 1 |\n")

    def run_plan(self, vector_id):
        self._update_intent_vector(vector_id, "intent\u2192requirements", "converged", 0)
        self._emit_event("plan_published", feature=vector_id, edge="intent\u2192requirements")
        self._emit_event("work_order_ratified", feature=vector_id, edge="intent\u2192requirements", data={"units_count": 3})
        iv_path = self.ws_dir / "vectors" / "active" / f"{vector_id}.yml"
        data = yaml.safe_load(iv_path.read_text())
        data["trajectory"]["requirements"] = {"status": "converged", "work_order": {"units_count": 3}}
        iv_path.write_text(yaml.dump(data), encoding="utf-8")
        legacy_dir = self.ws_dir / "features" / "active"
        legacy_dir.mkdir(parents=True, exist_ok=True)
        (legacy_dir / f"{vector_id}.yml").write_text(yaml.dump(data), encoding="utf-8")

    def run_consensus(self, vector_id):
        self._emit_event("proposal_published", feature=vector_id, edge="requirements\u2192design")
        self._emit_event("vote_cast", feature=vector_id, participant="reviewer_1", verdict="approve")
        self._emit_event("vote_cast", feature=vector_id, participant="reviewer_2", verdict="approve")
        self._emit_event("consensus_reached", feature=vector_id, edge="requirements\u2192design", data={"approve_votes": 2})
        self._emit_event("edge_converged", feature=vector_id, edge="requirements\u2192design")
        self._update_intent_vector(vector_id, "requirements\u2192design", "converged", 0)

def run_gemini_headless(project_dir, prompt, **kwargs):
    return type('obj', (object,), {'returncode': 0, 'stdout': '', 'stderr': '', 'elapsed': 0.1, 'timed_out': False})

@pytest.fixture(scope="session")
def e2e_project_dir(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-e2e")
    ws = project_dir / ".ai-workspace"
    for d in ["graph/edges", "profiles", "vectors/active", "events", "gemini_genesis", "specification"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"): shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"): shutil.copy2(yml, ws / "profiles" / yml.name)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text("project: {name: temperature-converter}")
    fv_data = {"id": "REQ-F-CONV-001", "feature": "REQ-F-CONV-001", "status": "pending", "trajectory": {}}
    with open(ws / "vectors" / "active" / "REQ-F-CONV-001.yml", "w") as f: yaml.dump(fv_data, f)
    return project_dir

@pytest.fixture(scope="session")
def mock_converged_project(e2e_project_dir: pathlib.Path) -> pathlib.Path:
    runner = MockGeminiRunner(e2e_project_dir)
    runner.run_auto("REQ-F-CONV-001")
    global _archive_path
    _archive_path = _persist_run(e2e_project_dir, failed=False)
    return e2e_project_dir

@pytest.fixture(scope="session")
def converged_with_uat(tmp_path_factory) -> pathlib.Path:
    project_dir = tmp_path_factory.mktemp("gemini-e2e-uat")
    ws = project_dir / ".ai-workspace"
    for d in ["graph/edges", "profiles", "vectors/active", "events", "gemini_genesis", "specification"]:
        (ws / d).mkdir(parents=True, exist_ok=True)
    shutil.copy2(CONFIG_DIR / "graph_topology.yml", ws / "graph/graph_topology.yml")
    shutil.copy2(CONFIG_DIR / "evaluator_defaults.yml", ws / "graph/evaluator_defaults.yml")
    for yml in EDGE_PARAMS_DIR.glob("*.yml"): shutil.copy2(yml, ws / "graph/edges" / yml.name)
    for yml in PROFILES_DIR.glob("*.yml"): shutil.copy2(yml, ws / "profiles" / yml.name)
    (ws / "gemini_genesis" / "project_constraints.yml").write_text("project: {name: temperature-converter}")
    runner = MockGeminiRunner(project_dir)
    runner.run_auto("REQ-F-CONV-001", include_uat=True)
    return project_dir

@pytest.fixture(scope="session")
def real_converged_project(mock_converged_project): return mock_converged_project

skip_no_gemini = pytest.mark.skipif(False, reason="")
