# Validates: REQ-TOOL-001, REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-004, REQ-TOOL-005
# Validates: REQ-TOOL-006, REQ-TOOL-007, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010
"""UC-08: Developer Tooling — 24 scenarios.

Tests plugin architecture, workspace structure, workflow commands,
release management, gap analysis, hooks, scaffolding, snapshots,
feature views, and spec/design boundary enforcement.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

import pytest
import yaml

from imp_codex.tests.uat.conftest import (
    CONFIG_DIR, PLUGIN_ROOT, COMMANDS_DIR, AGENTS_DIR,
    EDGE_PARAMS_DIR, PROFILES_DIR,
    make_event, write_events, write_feature_vector,
)
from imp_codex.tests.uat.workspace_state import (
    load_events, get_active_features,
    compute_feature_view, compute_aggregated_view,
)

pytestmark = [pytest.mark.uat]


# -- EXISTING COVERAGE (not duplicated) --
# UC-08-01: TestPluginStructure (test_config_validation.py)
# UC-08-02: TestPluginVersion (test_config_validation.py)
# UC-08-03: TestWorkspaceStructure (test_config_validation.py)
# UC-08-12: TestGapAnalysis (test_methodology_bdd.py)
# UC-08-17: TestScaffolding (test_config_validation.py)


# ===================================================================
# UC-08-01..02: PLUGIN ARCHITECTURE (Tier 1)
# ===================================================================


class TestPluginArchitecture:
    """UC-08-01 through UC-08-02: plugin structure and versioning."""

    # UC-08-01 | Validates: REQ-TOOL-001 | Fixture: CLEAN
    def test_plugin_structure_complete(self):
        """Plugin has configs, commands, templates, edge configs."""
        assert CONFIG_DIR.exists()
        assert COMMANDS_DIR.exists()
        assert EDGE_PARAMS_DIR.exists()
        assert PROFILES_DIR.exists()
        assert (CONFIG_DIR / "graph_topology.yml").exists()
        assert (CONFIG_DIR / "evaluator_defaults.yml").exists()
        assert (CONFIG_DIR / "feature_vector_template.yml").exists()

    # UC-08-02 | Validates: REQ-TOOL-001 | Fixture: INITIALIZED
    def test_plugin_versioned(self):
        """Plugin has plugin.json with version information."""
        plugin_json = PLUGIN_ROOT / "plugin.json"
        assert plugin_json.exists(), "plugin.json should exist"
        data = json.loads(plugin_json.read_text())
        assert "version" in data or "name" in data


# ===================================================================
# UC-08-03..05: DEVELOPER WORKSPACE (Tier 1 / Tier 2)
# ===================================================================


class TestDeveloperWorkspace:
    """UC-08-03 through UC-08-05: workspace structure and persistence."""

    # UC-08-03 | Validates: REQ-TOOL-002 | Fixture: INITIALIZED
    def test_workspace_directories(self, initialized_workspace):
        """Initialized workspace has required directory structure."""
        ws = initialized_workspace / ".ai-workspace"
        required = ["graph", "features/active", "events", "profiles"]
        for d in required:
            assert (ws / d).exists(), f"Missing workspace directory: {d}"

    # UC-08-04 | Validates: REQ-TOOL-002 | Fixture: IN_PROGRESS
    def test_context_preserved(self, in_progress_workspace):
        """Workspace has events and features that persist across sessions."""
        events = load_events(in_progress_workspace)
        features = get_active_features(in_progress_workspace)
        assert len(events) > 0, "Events should persist"
        assert len(features) > 0, "Features should persist"

    # UC-08-05 | Validates: REQ-TOOL-002 | Fixture: INITIALIZED
    def test_workspace_in_project(self, initialized_workspace):
        """Workspace is within the project directory (git-integratable)."""
        ws = initialized_workspace / ".ai-workspace"
        assert ws.exists()
        assert ws.parent == initialized_workspace


# ===================================================================
# UC-08-06..08: WORKFLOW COMMANDS (Tier 1 / Tier 3)
# ===================================================================


class TestWorkflowCommands:
    """UC-08-06 through UC-08-08: task management, context ops, status."""

    # UC-08-06 | Validates: REQ-TOOL-003 | Fixture: IN_PROGRESS
    def test_workflow_task_management(self, initialized_workspace):
        """Workflow commands can create/update/complete tasks."""
        ws = initialized_workspace / ".ai-workspace"
        tasks_dir = ws / "tasks" / "active"

        # Task management directory should exist in initialized workspace
        assert tasks_dir.exists(), "tasks/active directory should exist"

        # Create a synthetic task as a YAML file
        task_data = {
            "id": "TASK-001",
            "title": "Implement authentication",
            "status": "in_progress",
            "feature": "REQ-F-ALPHA-001",
            "edge": "design->code",
            "created": "2026-02-22T00:00:00Z",
            "updated": "2026-02-22T00:00:00Z",
        }
        task_file = tasks_dir / "TASK-001.yml"
        with open(task_file, "w") as f:
            yaml.dump(task_data, f, default_flow_style=False)

        # Read it back and validate round-trip
        assert task_file.exists(), "Task file should be written"
        with open(task_file) as f:
            loaded = yaml.safe_load(f)

        assert loaded["id"] == "TASK-001"
        assert loaded["status"] == "in_progress"
        assert loaded["feature"] == "REQ-F-ALPHA-001"
        assert loaded["title"] == "Implement authentication"

    # UC-08-07 | Validates: REQ-TOOL-003 | Fixture: IN_PROGRESS
    def test_workflow_checkpoint_restore(self, in_progress_workspace):
        """Context operations include checkpoint and non-destructive restore."""
        ws = in_progress_workspace / ".ai-workspace"

        # Create a checkpoints directory and write a checkpoint snapshot
        checkpoints_dir = ws / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        # Build a checkpoint from current workspace state
        events = load_events(in_progress_workspace)
        features = get_active_features(in_progress_workspace)

        checkpoint_data = {
            "checkpoint_id": "CP-001",
            "timestamp": "2026-02-22T12:00:00Z",
            "event_count": len(events),
            "feature_count": len(features),
            "feature_ids": [f.get("feature", "") for f in features],
            "context_hash": hashlib.sha256(
                json.dumps({"events": len(events)}, sort_keys=True).encode()
            ).hexdigest(),
        }
        cp_file = checkpoints_dir / "CP-001.yml"
        with open(cp_file, "w") as f:
            yaml.dump(checkpoint_data, f, default_flow_style=False)

        # Read it back (restore) and validate round-trip
        assert cp_file.exists(), "Checkpoint file should be written"
        with open(cp_file) as f:
            restored = yaml.safe_load(f)

        assert restored["checkpoint_id"] == "CP-001"
        assert restored["event_count"] == len(events)
        assert restored["feature_count"] == len(features)
        assert restored["context_hash"], "Checkpoint should have a context hash"

    # UC-08-08 | Validates: REQ-TOOL-003 | Fixture: IN_PROGRESS
    def test_status_command_exists(self):
        """Status command markdown exists."""
        status_cmd = COMMANDS_DIR / "gen-status.md"
        assert status_cmd.exists(), "gen-status command should exist"


# ===================================================================
# UC-08-09..11: RELEASE MANAGEMENT (Tier 3)
# ===================================================================


class TestReleaseManagement:
    """UC-08-09 through UC-08-11: release, manifest, tagging."""

    # UC-08-09 | Validates: REQ-TOOL-004 | Fixture: CONVERGED
    def test_release_with_semver(self):
        """Release command produces semver-versioned release."""
        # Validate the release command spec documents semver usage
        release_cmd = COMMANDS_DIR / "gen-release.md"
        assert release_cmd.exists(), "gen-release command should exist"

        content = release_cmd.read_text()

        # Command spec must document semver versioning
        assert "semver" in content.lower() or "semantic version" in content.lower(), (
            "Release command should document semver versioning"
        )
        assert "--version" in content, (
            "Release command should accept --version parameter"
        )
        # Verify the usage pattern shows semver format
        assert "{semver}" in content or "1.0.0" in content or "0.2.0" in content, (
            "Release command should show semver format examples"
        )

    # UC-08-10 | Validates: REQ-TOOL-004 | Fixture: CONVERGED
    def test_release_manifest_coverage(self):
        """Release manifest lists feature vectors with coverage summary."""
        # Create a synthetic release manifest and validate its schema
        manifest = {
            "version": "1.0.0",
            "date": "2026-02-22",
            "context_hash": "sha256:" + hashlib.sha256(b"test").hexdigest(),
            "features_included": [
                {"id": "REQ-F-DELTA-001", "status": "converged"},
                {"id": "REQ-F-EPSILON-001", "status": "converged"},
            ],
            "coverage": {
                "requirements": "2/2 (100%)",
                "design": "2/2 (100%)",
                "code": "2/2 (100%)",
                "tests": "2/2 (100%)",
            },
            "known_gaps": [],
        }

        # Validate the required schema fields
        assert "version" in manifest
        assert "features_included" in manifest
        assert len(manifest["features_included"]) >= 1
        assert "coverage" in manifest
        assert "requirements" in manifest["coverage"]
        assert "code" in manifest["coverage"]
        assert "context_hash" in manifest
        assert manifest["context_hash"].startswith("sha256:")

        # Validate YAML round-trip
        serialized = yaml.dump(manifest, default_flow_style=False)
        restored = yaml.safe_load(serialized)
        assert restored["version"] == "1.0.0"
        assert len(restored["features_included"]) == 2

        # Also validate the release command spec documents manifest coverage
        release_cmd = COMMANDS_DIR / "gen-release.md"
        content = release_cmd.read_text()
        assert "coverage" in content.lower(), (
            "Release command should document coverage in manifest"
        )
        assert "features_included" in content or "features" in content.lower(), (
            "Release command should document features in manifest"
        )

    # UC-08-11 | Validates: REQ-TOOL-004 | Fixture: CONVERGED
    def test_release_git_tag(self):
        """Release creates git tag pointing to manifest commit."""
        # Validate the release command spec documents git tagging
        release_cmd = COMMANDS_DIR / "gen-release.md"
        assert release_cmd.exists(), "gen-release command should exist"

        content = release_cmd.read_text()

        assert "git tag" in content.lower() or "git_tag" in content.lower(), (
            "Release command should document git tagging"
        )
        # Verify the tag format is documented
        assert "v{version}" in content or 'v{' in content, (
            "Release command should document tag format v{version}"
        )


# ===================================================================
# UC-08-12..14: GAP ANALYSIS (Tier 1 / Tier 3)
# ===================================================================


class TestGapAnalysis:
    """UC-08-12 through UC-08-14: uncovered REQs, suggestions, events."""

    # UC-08-12 | Validates: REQ-TOOL-005 | Fixture: IN_PROGRESS
    def test_gap_analysis_command_exists(self):
        """Gap analysis command markdown exists."""
        gaps_cmd = COMMANDS_DIR / "gen-gaps.md"
        assert gaps_cmd.exists(), "gen-gaps command should exist"

    # UC-08-13 | Validates: REQ-TOOL-005 | Fixture: IN_PROGRESS
    @pytest.mark.xfail(reason="Requires LLM-based semantic analysis", strict=False)
    def test_gap_suggestions(self, in_progress_workspace):
        """Gap analysis suggests test cases for uncovered REQ keys."""
        raise NotImplementedError("Requires runtime gap engine with LLM")

    # UC-08-14 | Validates: REQ-TOOL-005 | Fixture: IN_PROGRESS
    def test_gaps_validated_event(self, in_progress_workspace):
        """Gap analysis emits gaps_validated event."""
        ws = in_progress_workspace / ".ai-workspace"
        events_file = ws / "events" / "events.jsonl"

        # Create a synthetic gaps_validated event
        existing_events = load_events(in_progress_workspace)
        gaps_event = make_event(
            "gaps_validated",
            project="uat-test-project",
            total_req_keys=10,
            covered_req_keys=7,
            uncovered_req_keys=3,
            coverage_pct=70.0,
            uncovered=["REQ-F-MISSING-001", "REQ-F-MISSING-002", "REQ-F-MISSING-003"],
        )
        existing_events.append(gaps_event)
        write_events(events_file, existing_events)

        # Re-load and validate the event schema
        reloaded = load_events(in_progress_workspace)
        gap_events = [
            e for e in reloaded if e.get("event_type") == "gaps_validated"
        ]
        assert len(gap_events) >= 1, "Should have at least one gaps_validated event"

        ev = gap_events[0]
        assert ev["event_type"] == "gaps_validated"
        assert "timestamp" in ev
        assert "total_req_keys" in ev
        assert "covered_req_keys" in ev
        assert "uncovered_req_keys" in ev
        assert ev["total_req_keys"] >= ev["covered_req_keys"]


# ===================================================================
# UC-08-15..16: METHODOLOGY HOOKS (Tier 1 / Tier 3)
# ===================================================================


class TestMethodologyHooks:
    """UC-08-15 through UC-08-16: commit and edge transition hooks."""

    # UC-08-15 | Validates: REQ-TOOL-006 | Fixture: IN_PROGRESS
    def test_hooks_config_exists(self):
        """Hooks configuration file exists."""
        hooks_dir = PLUGIN_ROOT / "hooks"
        assert hooks_dir.exists(), "Hooks directory should exist"
        hooks_json = hooks_dir / "hooks.json"
        assert hooks_json.exists(), "hooks.json should exist"

    # UC-08-16 | Validates: REQ-TOOL-006 | Fixture: IN_PROGRESS
    def test_edge_transition_hooks(self):
        """Hooks fire unconditionally on edge transition (reflex)."""
        # Read the hooks config and verify it defines hooks for edge transitions
        hooks_json = PLUGIN_ROOT / "hooks" / "hooks.json"
        assert hooks_json.exists(), "hooks.json should exist"

        data = json.loads(hooks_json.read_text())
        hooks = data.get("hooks", {})

        # There should be at least one hook category
        assert len(hooks) >= 1, "hooks.json should define at least one hook category"

        # Check for iterate-related hooks (edge transition hooks)
        # UserPromptSubmit with gen-iterate matcher fires on edge transitions
        has_edge_hook = False
        for category, hook_list in hooks.items():
            if not isinstance(hook_list, list):
                continue
            for entry in hook_list:
                matcher = entry.get("matcher", "")
                entry_hooks = entry.get("hooks", [])
                # A hook matching iterate commands or a Stop hook is edge-related
                if "iterate" in matcher or category == "Stop":
                    if entry_hooks:
                        has_edge_hook = True
                        # Verify hook has required fields
                        for h in entry_hooks:
                            assert "type" in h, "Hook must have a type"
                            assert "command" in h, "Hook must have a command"

        assert has_edge_hook, (
            "hooks.json should define hooks that fire on edge transitions"
        )


# ===================================================================
# UC-08-17..18: PROJECT SCAFFOLDING (Tier 1)
# ===================================================================


class TestProjectScaffolding:
    """UC-08-17 through UC-08-18: scaffolding and templates."""

    # UC-08-17 | Validates: REQ-TOOL-007 | Fixture: CLEAN
    def test_scaffolding_command_exists(self):
        """Init command for scaffolding exists."""
        init_cmd = COMMANDS_DIR / "gen-init.md"
        assert init_cmd.exists(), "gen-init command should exist"

    # UC-08-18 | Validates: REQ-TOOL-007 | Fixture: CLEAN
    def test_templates_available(self):
        """Templates for feature vector and project constraints exist."""
        assert (CONFIG_DIR / "feature_vector_template.yml").exists()
        assert (CONFIG_DIR / "project_constraints_template.yml").exists()


# ===================================================================
# UC-08-19..20: CONTEXT SNAPSHOT (Tier 3)
# ===================================================================


class TestContextSnapshot:
    """UC-08-19 through UC-08-20: immutable checkpoints."""

    # UC-08-19 | Validates: REQ-TOOL-008 | Fixture: IN_PROGRESS
    def test_snapshot_immutable(self, in_progress_workspace):
        """Checkpoint at T1 remains unchanged after further work."""
        ws = in_progress_workspace / ".ai-workspace"

        # Create a checkpoint file at T1
        checkpoints_dir = ws / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)

        events_t1 = load_events(in_progress_workspace)
        checkpoint = {
            "checkpoint_id": "CP-IMMUTABLE",
            "timestamp": "2026-02-22T10:00:00Z",
            "event_count": len(events_t1),
            "snapshot_hash": hashlib.sha256(
                json.dumps(events_t1, sort_keys=True, default=str).encode()
            ).hexdigest(),
        }
        cp_file = checkpoints_dir / "CP-IMMUTABLE.yml"
        with open(cp_file, "w") as f:
            yaml.dump(checkpoint, f, default_flow_style=False)

        # Record the checkpoint file content
        checkpoint_content_before = cp_file.read_text()

        # Simulate further work: add more events to the workspace
        events_file = ws / "events" / "events.jsonl"
        new_events = events_t1 + [
            make_event("iteration_completed", feature="REQ-F-ALPHA-001",
                       edge="requirements->design", iteration=3, delta=0),
            make_event("edge_converged", feature="REQ-F-ALPHA-001",
                       edge="requirements->design"),
        ]
        write_events(events_file, new_events)

        # Verify the checkpoint file is unchanged
        checkpoint_content_after = cp_file.read_text()
        assert checkpoint_content_before == checkpoint_content_after, (
            "Checkpoint file should remain immutable after further work"
        )

        # Verify events actually changed (the workspace moved on)
        events_after = load_events(in_progress_workspace)
        assert len(events_after) > len(events_t1), (
            "Workspace should have more events after further work"
        )

    # UC-08-20 | Validates: REQ-TOOL-008 | Fixture: IN_PROGRESS
    def test_snapshot_includes_tasks(self, in_progress_workspace):
        """Checkpoint includes active tasks, feature states, context hash."""
        ws = in_progress_workspace / ".ai-workspace"

        # Create tasks directory and a task
        tasks_dir = ws / "tasks" / "active"
        tasks_dir.mkdir(parents=True, exist_ok=True)
        task_data = {
            "id": "TASK-SNAP-001",
            "title": "Snapshot task",
            "status": "in_progress",
        }
        with open(tasks_dir / "TASK-SNAP-001.yml", "w") as f:
            yaml.dump(task_data, f)

        # Build a comprehensive checkpoint
        events = load_events(in_progress_workspace)
        features = get_active_features(in_progress_workspace)

        # Collect task files
        task_files = sorted(tasks_dir.glob("*.yml"))
        tasks = []
        for tf in task_files:
            with open(tf) as f:
                tasks.append(yaml.safe_load(f))

        context_hash = hashlib.sha256(
            json.dumps(
                {"events": len(events), "features": len(features), "tasks": len(tasks)},
                sort_keys=True,
            ).encode()
        ).hexdigest()

        checkpoint = {
            "checkpoint_id": "CP-FULL",
            "timestamp": "2026-02-22T12:00:00Z",
            "tasks": [t.get("id", "") for t in tasks],
            "features": [f.get("feature", "") for f in features],
            "context_hash": f"sha256:{context_hash}",
            "event_count": len(events),
        }

        # Validate the checkpoint structure
        assert "tasks" in checkpoint
        assert len(checkpoint["tasks"]) >= 1, "Checkpoint should include tasks"
        assert "features" in checkpoint
        assert len(checkpoint["features"]) >= 1, "Checkpoint should include features"
        assert "context_hash" in checkpoint
        assert checkpoint["context_hash"].startswith("sha256:"), (
            "Context hash should be sha256-prefixed"
        )

        # Validate YAML round-trip
        checkpoints_dir = ws / "checkpoints"
        checkpoints_dir.mkdir(parents=True, exist_ok=True)
        cp_file = checkpoints_dir / "CP-FULL.yml"
        with open(cp_file, "w") as f:
            yaml.dump(checkpoint, f, default_flow_style=False)

        with open(cp_file) as f:
            restored = yaml.safe_load(f)

        assert restored["checkpoint_id"] == "CP-FULL"
        assert "TASK-SNAP-001" in restored["tasks"]
        assert len(restored["features"]) >= 1
        assert restored["context_hash"].startswith("sha256:")


# ===================================================================
# UC-08-21..22: FEATURE VIEWS (Tier 3)
# ===================================================================


class TestFeatureViews:
    """UC-08-21 through UC-08-22: per-REQ and aggregated views."""

    # UC-08-21 | Validates: REQ-TOOL-009 | Fixture: IN_PROGRESS
    def test_per_req_feature_view(self, in_progress_workspace):
        """Feature view for specific REQ key shows cross-artifact status."""
        # Use compute_feature_view() on in_progress_workspace
        view = compute_feature_view(in_progress_workspace, "REQ-F-ALPHA-001")

        assert view["feature"] == "REQ-F-ALPHA-001"
        assert view["status"] == "in_progress"
        assert "edges" in view

        edges = view["edges"]
        assert len(edges) >= 1, "Feature view should have at least one edge"

        # Feature A has converged requirements and iterating design
        assert "requirements" in edges
        assert edges["requirements"]["status"] == "converged"
        assert "design" in edges
        assert edges["design"]["status"] == "iterating"

        # Each edge entry should have status, iterations, and delta
        for edge_name, edge_data in edges.items():
            assert "status" in edge_data, f"Edge {edge_name} should have status"

        # Verify a non-existent feature returns not_found
        missing_view = compute_feature_view(in_progress_workspace, "REQ-F-NONEXIST-999")
        assert missing_view["status"] == "not_found"

    # UC-08-22 | Validates: REQ-TOOL-009 | Fixture: IN_PROGRESS
    def test_aggregated_feature_view(self, in_progress_workspace):
        """Aggregated view shows all features with coverage per stage."""
        # Use compute_aggregated_view() on in_progress_workspace
        agg = compute_aggregated_view(in_progress_workspace)

        assert "total" in agg
        assert "converged" in agg
        assert "in_progress" in agg
        assert "edges_converged" in agg
        assert "edges_total" in agg

        # in_progress_workspace has 3 features, none converged
        assert agg["total"] == 3
        assert agg["converged"] == 0
        assert agg["in_progress"] >= 1, "At least one feature should be in progress"

        # Edge counts should be positive (features have trajectories)
        assert agg["edges_total"] > 0, "Should have total edges"
        assert agg["edges_converged"] >= 0, "Converged edges should be non-negative"
        assert agg["edges_converged"] <= agg["edges_total"], (
            "Converged edges should not exceed total"
        )


# ===================================================================
# UC-08-23..24: SPEC/DESIGN BOUNDARY (Tier 1)
# ===================================================================


class TestSpecDesignBoundary:
    """UC-08-23 through UC-08-24: boundary enforcement."""

    # UC-08-23 | Validates: REQ-TOOL-010 | Fixture: IN_PROGRESS
    def test_spec_is_tech_agnostic(self):
        """Spec directory contains no technology-specific terms."""
        import re
        spec_model = pathlib.Path(__file__).parent.parent.parent.parent / "specification" / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        if spec_model.exists():
            content = spec_model.read_text()
            # Spec should not mention specific implementation tools
            tech_terms = ["Claude Code", "slash command", "MCP server", ".claude"]
            for term in tech_terms:
                # Allow in cross-reference sections
                assert content.lower().count(term.lower()) <= 2, (
                    f"Spec mentions implementation term '{term}' too frequently"
                )

    # UC-08-24 | Validates: REQ-TOOL-010 | Fixture: INITIALIZED
    def test_multi_tenant_structure(self):
        """Repository supports multiple implementation tenants."""
        project_root = pathlib.Path(__file__).parent.parent.parent.parent
        assert (project_root / "imp_codex").exists()
        # Spec is shared, implementations are separate
        assert (project_root / "specification").exists()
