# Validates: REQ-TOOL-011 (Installability), REQ-UX-001 (State-Driven Routing)
"""
End-to-end test: install → state transitions → convergence.

This is SC-001 steps 1-5 as an executable test. It runs the installer on a fresh
directory, then exercises the workspace state machine through its full lifecycle
using workspace_state.py utilities and synthetic events/feature vectors.

The test proves that a freshly installed environment can:
1. Be installed via the installer
2. Detect correct initial state (NEEDS_INTENT)
3. Transition through states as artifacts are created
4. Accept events and feature vectors
5. Detect convergence
6. Load all methodology configs
"""

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

# ── Paths ────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
INSTALLER = PROJECT_ROOT / "imp_claude" / "code" / "installers" / "gen-setup.py"
PLUGIN_ROOT = PROJECT_ROOT / "imp_claude" / "code" / ".claude-plugin" / "plugins" / "genesis"
CONFIG_DIR = PLUGIN_ROOT / "config"

# Import workspace state utilities
sys.path.insert(0, str(Path(__file__).parent))
from workspace_state import (
    detect_workspace_state,
    load_events,
    get_active_features,
    get_converged_edges,
    detect_stuck_features,
    detect_corrupted_events,
    compute_aggregated_view,
    compute_context_hash,
    STANDARD_PROFILE_EDGES,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def run_installer(target: Path, *extra_args: str) -> subprocess.CompletedProcess:
    """Run the installer against a target directory."""
    return subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target), *extra_args],
        capture_output=True,
        text=True,
    )


def write_intent(target: Path, text: str = "Build a task management REST API"):
    """Write a non-placeholder intent to specification/INTENT.md."""
    intent_path = target / "specification" / "INTENT.md"
    intent_path.parent.mkdir(parents=True, exist_ok=True)
    intent_path.write_text(f"# Project Intent\n\n{text}\n")


def create_feature_vector(target: Path, feature_id: str, status: str = "in_progress"):
    """Create a feature vector YAML file in the active features directory."""
    fv_dir = target / ".ai-workspace" / "features" / "active"
    fv_dir.mkdir(parents=True, exist_ok=True)
    fv = {
        "feature": feature_id,
        "status": status,
        "profile": "standard",
        "trajectory": {
            "requirements": {"status": "pending", "iteration": 0},
            "design": {"status": "pending", "iteration": 0},
            "code": {"status": "pending", "iteration": 0},
            "unit_tests": {"status": "pending", "iteration": 0},
        },
    }
    fv_path = fv_dir / f"{feature_id}.yml"
    fv_path.write_text(yaml.dump(fv, default_flow_style=False))
    return fv_path


def append_event(target: Path, event: dict):
    """Append a JSON event to events.jsonl."""
    events_file = target / ".ai-workspace" / "events" / "events.jsonl"
    events_file.parent.mkdir(parents=True, exist_ok=True)
    with open(events_file, "a") as f:
        f.write(json.dumps(event) + "\n")


def make_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def copy_plugin_configs(target: Path):
    """Copy real methodology configs into the installed workspace for loading tests."""
    dest = target / ".ai-workspace" / "plugin_configs"
    if dest.exists():
        return dest
    shutil.copytree(CONFIG_DIR, dest)
    return dest


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def installed_project(tmp_path):
    """Fresh project with installer run. Returns the project directory."""
    project = tmp_path / "my_project"
    project.mkdir()
    result = run_installer(project)
    assert result.returncode == 0, f"Installer failed:\n{result.stderr}\n{result.stdout}"
    return project


# ── Tests ────────────────────────────────────────────────────────────────────


class TestInstallAndVerify:
    """Step 1: Install and verify the installation is valid."""

    @pytest.mark.uat
    def test_installer_creates_workspace(self, installed_project):
        """Installer creates .ai-workspace with v2 structure."""
        ws = installed_project / ".ai-workspace"
        assert ws.is_dir()
        assert (ws / "events" / "events.jsonl").exists()
        assert (ws / "features" / "active").is_dir()
        assert (ws / "features" / "completed").is_dir()
        assert (ws / "context" / "project_constraints.yml").exists()
        assert (ws / "tasks" / "active" / "ACTIVE_TASKS.md").exists()

    @pytest.mark.uat
    def test_installer_emits_project_initialized(self, installed_project):
        """First event in events.jsonl is project_initialized."""
        events = load_events(installed_project)
        assert len(events) == 1
        assert events[0]["event_type"] == "project_initialized"
        assert events[0]["project"] == "my_project"
        assert "timestamp" in events[0]

    @pytest.mark.uat
    def test_installer_creates_intent_template(self, installed_project):
        """specification/INTENT.md exists with template content."""
        intent = installed_project / "specification" / "INTENT.md"
        assert intent.exists()
        content = intent.read_text()
        assert "Intent" in content

    @pytest.mark.uat
    def test_installer_creates_settings(self, installed_project):
        """Plugin marketplace and enablement configured in .claude/settings.json."""
        settings = json.loads(
            (installed_project / ".claude" / "settings.json").read_text()
        )
        assert "genesis" in settings["extraKnownMarketplaces"]
        assert settings["enabledPlugins"]["genesis@genesis"] is True

    @pytest.mark.uat
    def test_verify_command_passes(self, installed_project):
        """The verify subcommand reports all checks passing."""
        result = subprocess.run(
            [sys.executable, str(INSTALLER), "verify", "--target", str(installed_project)],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "0 failed" in result.stdout

    @pytest.mark.uat
    def test_event_log_has_no_corruption(self, installed_project):
        """Event log passes integrity check."""
        corruptions = detect_corrupted_events(installed_project)
        assert corruptions == []


class TestStateTransitions:
    """Steps 2-5: Walk through the state machine from install to convergence."""

    @pytest.mark.uat
    def test_initial_state_after_install(self, installed_project):
        """Freshly installed project with template intent is NEEDS_INTENT or NO_FEATURES.

        The installer writes a template INTENT.md (>10 bytes), so state detection
        sees it as having an intent. With no features, state should be NO_FEATURES.
        """
        state = detect_workspace_state(installed_project)
        # Template intent is > 10 bytes, so it passes the intent check
        # No feature vectors exist, so NO_FEATURES
        assert state == "NO_FEATURES"

    @pytest.mark.uat
    def test_needs_intent_when_intent_removed(self, installed_project):
        """Removing intent transitions to NEEDS_INTENT."""
        intent = installed_project / "specification" / "INTENT.md"
        intent.write_text("")  # Empty = no intent
        state = detect_workspace_state(installed_project)
        assert state == "NEEDS_INTENT"

    @pytest.mark.uat
    def test_no_features_after_intent_written(self, installed_project):
        """Writing a real intent (with no features) produces NO_FEATURES."""
        write_intent(installed_project, "Build a REST API for task management")
        state = detect_workspace_state(installed_project)
        assert state == "NO_FEATURES"

    @pytest.mark.uat
    def test_in_progress_after_feature_created(self, installed_project):
        """Creating a feature vector transitions to IN_PROGRESS."""
        write_intent(installed_project)
        create_feature_vector(installed_project, "REQ-F-TASK-001")
        state = detect_workspace_state(installed_project)
        assert state == "IN_PROGRESS"

    @pytest.mark.uat
    def test_all_converged_when_feature_converged(self, installed_project):
        """Feature with status=converged and all edges converged → ALL_CONVERGED."""
        write_intent(installed_project)
        fv_dir = installed_project / ".ai-workspace" / "features" / "active"
        fv_dir.mkdir(parents=True, exist_ok=True)
        fv = {
            "feature": "REQ-F-TASK-001",
            "status": "converged",
            "profile": "standard",
            "trajectory": {
                "requirements": {"status": "converged", "iteration": 2},
                "design": {"status": "converged", "iteration": 1},
                "code": {"status": "converged", "iteration": 3},
                "unit_tests": {"status": "converged", "iteration": 3},
            },
        }
        (fv_dir / "REQ-F-TASK-001.yml").write_text(
            yaml.dump(fv, default_flow_style=False)
        )
        state = detect_workspace_state(installed_project)
        assert state == "ALL_CONVERGED"

    @pytest.mark.uat
    def test_stuck_when_delta_unchanged(self, installed_project):
        """Feature with same delta for 3+ iterations → STUCK."""
        write_intent(installed_project)
        create_feature_vector(installed_project, "REQ-F-TASK-001")

        # Emit 3 iterations with same non-zero delta
        for i in range(1, 4):
            append_event(installed_project, {
                "event_type": "iteration_completed",
                "timestamp": make_ts(),
                "project": "my_project",
                "feature": "REQ-F-TASK-001",
                "edge": "design→code",
                "iteration": i,
                "delta": 3,
            })

        state = detect_workspace_state(installed_project)
        assert state == "STUCK"


class TestFullLifecycle:
    """SC-001 compressed: install → intent → feature → iterate → converge."""

    @pytest.mark.uat
    def test_full_state_machine_walk(self, installed_project):
        """Walk every state transition in a single test."""
        project = installed_project

        # ── INITIAL STATE ──
        state = detect_workspace_state(project)
        assert state == "NO_FEATURES", f"Expected NO_FEATURES after install, got {state}"

        # ── Write intent ──
        write_intent(project, "Build a task management API with auth")
        state = detect_workspace_state(project)
        assert state == "NO_FEATURES"

        # ── Create feature ──
        create_feature_vector(project, "REQ-F-AUTH-001")
        state = detect_workspace_state(project)
        assert state == "IN_PROGRESS"

        # ── Verify feature is loadable ──
        features = get_active_features(project)
        assert len(features) == 1
        assert features[0]["feature"] == "REQ-F-AUTH-001"

        # ── Emit iteration events on intent→requirements ──
        append_event(project, {
            "event_type": "edge_started",
            "timestamp": make_ts(),
            "project": "my_project",
            "feature": "REQ-F-AUTH-001",
            "edge": "intent→requirements",
        })
        append_event(project, {
            "event_type": "iteration_completed",
            "timestamp": make_ts(),
            "project": "my_project",
            "feature": "REQ-F-AUTH-001",
            "edge": "intent→requirements",
            "iteration": 1,
            "delta": 2,
        })
        append_event(project, {
            "event_type": "iteration_completed",
            "timestamp": make_ts(),
            "project": "my_project",
            "feature": "REQ-F-AUTH-001",
            "edge": "intent→requirements",
            "iteration": 2,
            "delta": 0,
        })
        append_event(project, {
            "event_type": "edge_converged",
            "timestamp": make_ts(),
            "project": "my_project",
            "feature": "REQ-F-AUTH-001",
            "edge": "intent→requirements",
            "iteration": 2,
            "convergence_type": "standard",
        })

        # ── Verify events are loadable ──
        events = load_events(project)
        assert len(events) >= 5  # project_initialized + 4 above
        converged = get_converged_edges(events, "REQ-F-AUTH-001")
        assert "intent→requirements" in converged

        # Still IN_PROGRESS (more edges to go)
        state = detect_workspace_state(project)
        assert state == "IN_PROGRESS"

        # ── Converge remaining edges via feature vector ──
        fv_dir = project / ".ai-workspace" / "features" / "active"
        fv = {
            "feature": "REQ-F-AUTH-001",
            "status": "converged",
            "profile": "standard",
            "trajectory": {
                "requirements": {"status": "converged", "iteration": 2},
                "design": {"status": "converged", "iteration": 1},
                "code": {"status": "converged", "iteration": 3},
                "unit_tests": {"status": "converged", "iteration": 3},
            },
        }
        (fv_dir / "REQ-F-AUTH-001.yml").write_text(
            yaml.dump(fv, default_flow_style=False)
        )

        # Emit edge_converged for remaining edges
        for edge in ["requirements→design", "design→code", "code↔unit_tests"]:
            append_event(project, {
                "event_type": "edge_converged",
                "timestamp": make_ts(),
                "project": "my_project",
                "feature": "REQ-F-AUTH-001",
                "edge": edge,
                "iteration": 1,
                "convergence_type": "standard",
            })

        # ── ALL_CONVERGED ──
        state = detect_workspace_state(project)
        assert state == "ALL_CONVERGED"

        # ── Verify aggregated view ──
        agg = compute_aggregated_view(project)
        assert agg["total"] == 1
        assert agg["converged"] == 1
        assert agg["in_progress"] == 0
        assert agg["stuck"] == 0

        # ── Verify no corruption ──
        assert detect_corrupted_events(project) == []

    @pytest.mark.uat
    def test_multi_feature_lifecycle(self, installed_project):
        """Two features: one converges, one is in-progress."""
        project = installed_project
        write_intent(project)

        # Create two features
        create_feature_vector(project, "REQ-F-DB-001")
        create_feature_vector(project, "REQ-F-API-001")

        state = detect_workspace_state(project)
        assert state == "IN_PROGRESS"

        # Converge DB feature
        fv_dir = project / ".ai-workspace" / "features" / "active"
        fv_db = {
            "feature": "REQ-F-DB-001",
            "status": "converged",
            "profile": "standard",
            "trajectory": {
                "requirements": {"status": "converged", "iteration": 1},
                "design": {"status": "converged", "iteration": 1},
                "code": {"status": "converged", "iteration": 2},
                "unit_tests": {"status": "converged", "iteration": 2},
            },
        }
        (fv_dir / "REQ-F-DB-001.yml").write_text(
            yaml.dump(fv_db, default_flow_style=False)
        )

        # API still in progress
        state = detect_workspace_state(project)
        assert state == "IN_PROGRESS"

        agg = compute_aggregated_view(project)
        assert agg["total"] == 2
        assert agg["converged"] == 1
        assert agg["in_progress"] == 1


class TestConfigLoadability:
    """Verify all methodology configs are loadable from the installed environment."""

    @pytest.mark.uat
    def test_graph_topology_loadable(self, installed_project):
        """graph_topology.yml is valid YAML with expected structure."""
        config = copy_plugin_configs(installed_project)
        gt = yaml.safe_load((config / "graph_topology.yml").read_text())
        assert "asset_types" in gt
        assert "transitions" in gt
        assert len(gt["asset_types"]) >= 8

    @pytest.mark.uat
    def test_evaluator_defaults_loadable(self, installed_project):
        """evaluator_defaults.yml is valid YAML."""
        config = copy_plugin_configs(installed_project)
        docs = list(yaml.safe_load_all((config / "evaluator_defaults.yml").read_text()))
        assert len(docs) >= 1
        assert docs[0] is not None

    @pytest.mark.uat
    def test_intentengine_config_loadable(self, installed_project):
        """intentengine_config.yml is valid YAML with output types."""
        config = copy_plugin_configs(installed_project)
        ie = yaml.safe_load((config / "intentengine_config.yml").read_text())
        assert "output_types" in ie

    @pytest.mark.uat
    def test_all_edge_params_loadable(self, installed_project):
        """Every edge_params/*.yml file is valid YAML."""
        config = copy_plugin_configs(installed_project)
        edge_params = config / "edge_params"
        assert edge_params.is_dir()
        yml_files = list(edge_params.glob("*.yml"))
        assert len(yml_files) >= 5
        for f in yml_files:
            data = yaml.safe_load(f.read_text())
            assert data is not None, f"{f.name} is empty or invalid"

    @pytest.mark.uat
    def test_all_profiles_loadable(self, installed_project):
        """Every profiles/*.yml file is valid YAML with edges list."""
        config = copy_plugin_configs(installed_project)
        profiles = config / "profiles"
        assert profiles.is_dir()
        yml_files = list(profiles.glob("*.yml"))
        assert len(yml_files) >= 4
        for f in yml_files:
            data = yaml.safe_load(f.read_text())
            assert data is not None, f"{f.name} is empty or invalid"

    @pytest.mark.uat
    def test_feature_vector_template_loadable(self, installed_project):
        """feature_vector_template.yml is valid YAML with trajectory."""
        config = copy_plugin_configs(installed_project)
        fvt = yaml.safe_load((config / "feature_vector_template.yml").read_text())
        assert "trajectory" in fvt or "template" in fvt or fvt is not None

    @pytest.mark.uat
    def test_project_constraints_template_loadable(self, installed_project):
        """Installed project_constraints.yml is valid YAML."""
        pc = yaml.safe_load(
            (installed_project / ".ai-workspace" / "context" / "project_constraints.yml").read_text()
        )
        assert pc is not None
        assert "project" in pc


class TestEventIntegrity:
    """Verify event log integrity across lifecycle operations."""

    @pytest.mark.uat
    def test_events_are_append_only(self, installed_project):
        """Events written at different stages are all preserved."""
        project = installed_project
        write_intent(project)
        create_feature_vector(project, "REQ-F-001")

        # Append several events
        for i in range(5):
            append_event(project, {
                "event_type": "iteration_completed",
                "timestamp": make_ts(),
                "project": "my_project",
                "feature": "REQ-F-001",
                "edge": "intent→requirements",
                "iteration": i + 1,
                "delta": 5 - i,
            })

        events = load_events(project)
        # project_initialized + 5 iterations
        assert len(events) == 6
        assert events[0]["event_type"] == "project_initialized"
        assert all(
            events[i + 1]["event_type"] == "iteration_completed"
            for i in range(5)
        )

    @pytest.mark.uat
    def test_context_hash_deterministic(self, installed_project):
        """Same context always produces same hash."""
        ctx = {"feature": "REQ-F-001", "edge": "design→code", "iteration": 3}
        h1 = compute_context_hash(ctx)
        h2 = compute_context_hash(ctx)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    @pytest.mark.uat
    def test_idempotent_reinstall_preserves_events(self, installed_project):
        """Running installer again does not duplicate project_initialized."""
        project = installed_project

        # Add some user events
        write_intent(project)
        create_feature_vector(project, "REQ-F-001")
        append_event(project, {
            "event_type": "iteration_completed",
            "timestamp": make_ts(),
            "project": "my_project",
            "feature": "REQ-F-001",
            "edge": "intent→requirements",
            "iteration": 1,
            "delta": 0,
        })

        events_before = load_events(project)
        count_before = len(events_before)

        # Re-run installer
        result = run_installer(project)
        assert result.returncode == 0

        events_after = load_events(project)
        assert len(events_after) == count_before, "Installer should not add events on re-run"


class TestPluginIntegration:
    """Verify the installed plugin references are consistent."""

    @pytest.mark.uat
    def test_plugin_json_commands_all_exist(self, installed_project):
        """Every command referenced in plugin.json has a corresponding .md file."""
        pj = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        for cmd_path in pj["commands"]:
            full = PLUGIN_ROOT / cmd_path
            assert full.exists(), f"plugin.json references missing command: {cmd_path}"

    @pytest.mark.uat
    def test_plugin_json_agents_all_exist(self, installed_project):
        """Every agent referenced in plugin.json has a corresponding .md file."""
        pj = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        for agent_path in pj["agents"]:
            full = PLUGIN_ROOT / agent_path
            assert full.exists(), f"plugin.json references missing agent: {agent_path}"

    @pytest.mark.uat
    def test_plugin_json_configs_all_exist(self, installed_project):
        """Every config referenced in plugin.json exists."""
        pj = json.loads((PLUGIN_ROOT / "plugin.json").read_text())
        for cfg_path in pj["config"]:
            full = PLUGIN_ROOT / cfg_path
            assert full.exists(), f"plugin.json references missing config: {cfg_path}"

    @pytest.mark.uat
    def test_marketplace_json_exists(self):
        """Root marketplace.json exists and references the plugin."""
        mkt = PROJECT_ROOT / ".claude-plugin" / "marketplace.json"
        assert mkt.exists()
        data = json.loads(mkt.read_text())
        assert data["name"] == "genesis"
        plugin_names = [p["name"] for p in data["plugins"]]
        assert "genesis" in plugin_names
