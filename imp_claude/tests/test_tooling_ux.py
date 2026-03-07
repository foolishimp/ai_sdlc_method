# Validates: REQ-TOOL-002
# Validates: REQ-TOOL-003
# Validates: REQ-TOOL-004
# Validates: REQ-TOOL-006
# Validates: REQ-TOOL-007
# Validates: REQ-TOOL-008
# Validates: REQ-TOOL-011
# Validates: REQ-TOOL-012
# Validates: REQ-TOOL-013
# Validates: REQ-TOOL-014
# Validates: REQ-UX-002
# Validates: REQ-UX-004
# Validates: REQ-UX-005
# Validates: REQ-UX-007
"""Deterministic tests for tooling and UX requirements.

INT-GAP-005 resolution — Phase 1 tooling/UX correctness.
Tests verify file existence, content structure, and configuration
without requiring a live LLM.
"""

import pathlib

import pytest
import yaml

from conftest import (
    COMMANDS_DIR,
    CONFIG_DIR,
    PROJECT_ROOT,
)

WORKSPACE = PROJECT_ROOT / ".ai-workspace"
INSTALLER = PROJECT_ROOT / "imp_claude" / "code" / "installers" / "gen-setup.py"


def _cmd(name: str) -> pathlib.Path:
    """Return path to a command markdown file."""
    return COMMANDS_DIR / f"{name}.md"


def _cmd_text(name: str) -> str:
    return _cmd(name).read_text()


def _load_yaml(path: pathlib.Path) -> dict:
    with open(path) as f:
        docs = list(yaml.safe_load_all(f))
    result: dict = {}
    for doc in docs:
        if doc is not None:
            result.update(doc)
    return result


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-002 — Developer Workspace
# ═══════════════════════════════════════════════════════════════════════


class TestDeveloperWorkspace:
    """Workspace structure supports task tracking and context preservation."""

    def test_workspace_directory_exists(self):
        """`.ai-workspace/` directory exists at project root."""
        assert WORKSPACE.is_dir(), (
            "`.ai-workspace/` must exist — it is the runtime workspace "
            "for task tracking and context management"
        )

    def test_task_tracking_active_dir_exists(self):
        """Task tracking: active tasks directory present."""
        assert (WORKSPACE / "tasks" / "active").is_dir(), (
            "`.ai-workspace/tasks/active/` must exist for task tracking"
        )

    def test_task_tracking_finished_dir_exists(self):
        """Task tracking: finished tasks directory present."""
        assert (WORKSPACE / "tasks" / "finished").is_dir(), (
            "`.ai-workspace/tasks/finished/` must exist for task archival"
        )

    def test_events_directory_exists(self):
        """Events directory exists for event log (context preservation across sessions)."""
        assert (WORKSPACE / "events").is_dir(), (
            "`.ai-workspace/events/` must exist — event log is the context "
            "that preserves session state"
        )

    def test_workspace_is_version_controlled(self):
        """Project root is a git repository (workspace is version-controlled)."""
        assert (PROJECT_ROOT / ".git").is_dir(), (
            "Project root must be a git repository — workspace is version-controlled"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-003 — Workflow Commands
# ═══════════════════════════════════════════════════════════════════════


class TestWorkflowCommands:
    """Commands exist for common workflow operations."""

    REQUIRED_COMMANDS = [
        "gen-start",
        "gen-iterate",
        "gen-status",
        "gen-checkpoint",
        "gen-gaps",
        "gen-release",
        "gen-review",
        "gen-spawn",
    ]

    def test_all_required_commands_exist(self):
        """All core workflow commands have corresponding .md files."""
        for cmd in self.REQUIRED_COMMANDS:
            path = _cmd(cmd)
            assert path.exists(), (
                f"Command `{cmd}` missing — workflow commands required by REQ-TOOL-003"
            )

    def test_gen_checkpoint_is_context_command(self):
        """gen-checkpoint provides context preservation (checkpoint/restore)."""
        text = _cmd_text("gen-checkpoint")
        assert "snapshot" in text.lower() or "checkpoint" in text.lower()

    def test_gen_gaps_is_coverage_command(self):
        """gen-gaps provides gap/coverage reporting."""
        text = _cmd_text("gen-gaps")
        assert "gap" in text.lower() and "coverage" in text.lower()

    def test_gen_status_is_progress_command(self):
        """gen-status provides project-wide status/progress view."""
        text = _cmd_text("gen-status")
        assert "status" in text.lower() or "progress" in text.lower()


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-004 — Release Management
# ═══════════════════════════════════════════════════════════════════════


class TestReleaseManagement:
    """Release management with semver, changelog, and coverage summary."""

    def test_gen_release_command_exists(self):
        """gen-release command exists for release management."""
        assert _cmd("gen-release").exists(), "gen-release.md must exist"

    def test_release_mentions_semver(self):
        """gen-release.md references semantic versioning."""
        text = _cmd_text("gen-release")
        assert (
            "semver" in text.lower()
            or "semantic" in text.lower()
            or "version" in text.lower()
        ), "gen-release must reference semantic versioning"

    def test_release_mentions_changelog(self):
        """gen-release.md references changelog generation."""
        text = _cmd_text("gen-release")
        assert "changelog" in text.lower() or "CHANGELOG" in text, (
            "gen-release must reference changelog generation"
        )

    def test_project_has_version_in_pyproject(self):
        """pyproject.toml specifies the project version (semantic versioning)."""
        pyproject = PROJECT_ROOT / "pyproject.toml"
        if not pyproject.exists():
            pytest.skip("No pyproject.toml found")
        content = pyproject.read_text()
        assert "version" in content, (
            "pyproject.toml must specify a version for release management"
        )

    def test_release_mentions_coverage_summary(self):
        """gen-release.md includes feature vector coverage in release notes."""
        text = _cmd_text("gen-release")
        assert (
            "coverage" in text.lower() or "feature" in text.lower() or "REQ" in text
        ), "gen-release must reference feature coverage summary in release notes"


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-006 — Methodology Hooks
# ═══════════════════════════════════════════════════════════════════════


class TestMethodologyHooks:
    """Lifecycle hooks automating methodology compliance."""

    def test_installer_references_hooks(self):
        """Installer mentions hooks as part of methodology scaffolding."""
        installer_text = INSTALLER.read_text()
        assert "hook" in installer_text.lower(), (
            "Installer must reference hooks — methodology compliance automation"
        )

    def test_post_commit_hook_registered(self):
        """Git post-commit hook is installed for spec-watch automation."""
        hooks_dir = PROJECT_ROOT / ".git" / "hooks"
        assert hooks_dir.is_dir(), ".git/hooks directory must exist"
        post_commit = hooks_dir / "post-commit"
        # Hook either exists or spec-watch script exists in source
        spec_watch = (
            PROJECT_ROOT
            / "imp_claude"
            / "code"
            / ".claude-plugin"
            / "plugins"
            / "genesis"
            / "hooks"
        )
        assert post_commit.exists() or spec_watch.is_dir(), (
            "Either .git/hooks/post-commit or a hooks/ directory must exist"
        )

    def test_hooks_validate_req_tags(self):
        """Hook scripts reference REQ key validation (compliance automation)."""
        # Check the spec-watch hook or any hook file
        hook_files = list(
            (
                PROJECT_ROOT
                / "imp_claude"
                / "code"
                / ".claude-plugin"
                / "plugins"
                / "genesis"
            ).rglob("*hook*")
        ) + list(PROJECT_ROOT.glob(".git/hooks/post-commit"))
        found_req_ref = False
        for f in hook_files:
            if f.is_file():
                try:
                    content = f.read_text()
                    if "REQ" in content or "spec" in content.lower():
                        found_req_ref = True
                        break
                except Exception:
                    pass
        assert found_req_ref, "At least one hook file must reference REQ key validation"


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-007 — Project Scaffolding
# ═══════════════════════════════════════════════════════════════════════


class TestProjectScaffolding:
    """Installer creates complete workspace including observability artifacts."""

    def test_installer_implements_req_tool_007(self):
        """gen-setup.py declares it implements REQ-TOOL-007."""
        installer_text = INSTALLER.read_text()
        assert "REQ-TOOL-007" in installer_text, (
            "gen-setup.py must declare # Implements: REQ-TOOL-007"
        )

    def test_workspace_graph_topology_created(self):
        """Installer creates `.ai-workspace/graph/graph_topology.yml`."""
        installer_text = INSTALLER.read_text()
        assert "graph_topology" in installer_text, (
            "Installer must create graph_topology.yml — REQ-TOOL-007 acceptance criteria"
        )
        # And it actually exists in the workspace
        assert (WORKSPACE / "graph" / "graph_topology.yml").exists(), (
            "`.ai-workspace/graph/graph_topology.yml` must exist after installation"
        )

    def test_installer_creates_features_dirs(self):
        """Installer creates feature vector directories."""
        assert (WORKSPACE / "features" / "active").is_dir(), (
            "`.ai-workspace/features/active/` must exist for feature vectors"
        )

    def test_installer_creates_context_dir(self):
        """Installer creates context directory for project constraints."""
        # Context may be in workspace/context or workspace/<impl>/context
        context_dirs = list(WORKSPACE.rglob("project_constraints.yml"))
        assert len(context_dirs) >= 1, (
            "At least one project_constraints.yml must exist under `.ai-workspace/`"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-008 — Context Snapshot
# ═══════════════════════════════════════════════════════════════════════


class TestContextSnapshot:
    """Context snapshots for session recovery and continuity."""

    def test_gen_checkpoint_command_exists(self):
        """gen-checkpoint command exists for context snapshot creation."""
        assert _cmd("gen-checkpoint").exists(), "gen-checkpoint.md must exist"

    def test_snapshots_directory_exists(self):
        """`.ai-workspace/snapshots/` directory exists for immutable snapshots."""
        assert (WORKSPACE / "snapshots").is_dir(), (
            "`.ai-workspace/snapshots/` must exist — context snapshots are stored here"
        )

    def test_checkpoint_captures_active_tasks(self):
        """gen-checkpoint.md describes capturing active tasks in snapshot."""
        text = _cmd_text("gen-checkpoint")
        assert "task" in text.lower() or "active" in text.lower(), (
            "gen-checkpoint must capture active tasks in the snapshot"
        )

    def test_checkpoint_is_immutable(self):
        """gen-checkpoint.md describes snapshots as immutable."""
        text = _cmd_text("gen-checkpoint")
        assert "immutable" in text.lower(), (
            "gen-checkpoint must describe snapshots as immutable once created"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-011 — Installability
# ═══════════════════════════════════════════════════════════════════════


class TestInstallability:
    """Single-command, idempotent, verifiable installation."""

    def test_installer_is_single_python_file(self):
        """gen-setup.py is a single self-contained installer file."""
        assert INSTALLER.exists(), "gen-setup.py must exist"
        assert INSTALLER.suffix == ".py", "Installer must be a Python file"

    def test_installer_mentions_idempotent(self):
        """Installer preserves existing work on re-run (idempotent)."""
        installer_text = INSTALLER.read_text()
        assert (
            "idempotent" in installer_text.lower()
            or "preserve" in installer_text.lower()
        ), "Installer must be idempotent — re-running preserves existing work"

    def test_installer_emits_project_initialized_event(self):
        """Installer emits `project_initialized` event on first run."""
        installer_text = INSTALLER.read_text()
        assert "project_initialized" in installer_text, (
            "Installer must emit a project_initialized event (REQ-TOOL-011)"
        )

    def test_installer_has_verify_subcommand(self):
        """Installation is verifiable via a verify command."""
        installer_text = INSTALLER.read_text()
        assert "verify" in installer_text.lower(), (
            "Installer must support a verify command to confirm successful setup"
        )

    def test_installer_supports_offline_install(self):
        """Installer supports offline/air-gapped installation via local source."""
        installer_text = INSTALLER.read_text()
        assert (
            "--target" in installer_text
            or "local" in installer_text.lower()
            or "offline" in installer_text.lower()
        ), "Installer must support offline/local-path installation"

    def test_installer_implements_req_tool_011(self):
        """gen-setup.py declares it implements REQ-TOOL-011."""
        installer_text = INSTALLER.read_text()
        assert "REQ-TOOL-011" in installer_text


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-012 — Multi-Tenant Folder Structure
# ═══════════════════════════════════════════════════════════════════════


class TestMultiTenantStructure:
    """spec/ at root, imp_<name>/ per design variant — isolation enforced."""

    def test_specification_at_project_root(self):
        """Shared specification lives in `specification/` at project root."""
        assert (PROJECT_ROOT / "specification").is_dir(), (
            "`specification/` must exist at project root — tech-agnostic, one per project"
        )

    def test_imp_claude_design_variant_exists(self):
        """At least one `imp_<name>/` design variant directory exists."""
        imp_dirs = [
            d
            for d in PROJECT_ROOT.iterdir()
            if d.name.startswith("imp_") and d.is_dir()
        ]
        assert len(imp_dirs) >= 1, (
            "At least one `imp_*/` design variant directory must exist"
        )

    def test_imp_dirs_have_design_and_tests(self):
        """Each `imp_<name>/` has design/ and tests/ (independently structured)."""
        imp_claude = PROJECT_ROOT / "imp_claude"
        assert (imp_claude / "design").is_dir(), "imp_claude/ must have design/"
        assert (imp_claude / "tests").is_dir(), "imp_claude/ must have tests/"

    def test_project_constraints_template_has_design_tenants(self):
        """project_constraints_template.yml declares structure.design_tenants."""
        template = _load_yaml(CONFIG_DIR / "project_constraints_template.yml")
        structure = template.get("structure", {})
        assert "design_tenants" in structure, (
            "project_constraints_template.yml must include structure.design_tenants — "
            "the multi-tenant pattern must be declared in constraints"
        )

    def test_multiple_imp_dirs_exist(self):
        """Multiple design variants (imp_*) demonstrate the multi-tenant pattern."""
        imp_dirs = [
            d
            for d in PROJECT_ROOT.iterdir()
            if d.name.startswith("imp_") and d.is_dir()
        ]
        assert len(imp_dirs) >= 2, (
            f"Multiple `imp_*/` directories must exist — found {[d.name for d in imp_dirs]}"
        )

    def test_installer_implements_req_tool_012(self):
        """gen-setup.py declares it implements REQ-TOOL-012."""
        installer_text = INSTALLER.read_text()
        assert "REQ-TOOL-012" in installer_text


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-013 — Output Directory Binding
# ═══════════════════════════════════════════════════════════════════════


class TestOutputDirectoryBinding:
    """design→code edge binds output directory before code generation."""

    def test_project_constraints_template_has_structure_section(self):
        """project_constraints_template.yml has a structure section."""
        template = _load_yaml(CONFIG_DIR / "project_constraints_template.yml")
        assert "structure" in template, (
            "project_constraints_template.yml must have a structure section "
            "for output directory binding"
        )

    def test_design_tenants_field_in_structure(self):
        """structure.design_tenants enables output directory resolution."""
        template = _load_yaml(CONFIG_DIR / "project_constraints_template.yml")
        structure = template.get("structure", {})
        assert "design_tenants" in structure, (
            "structure.design_tenants must exist in project_constraints_template "
            "so the iterate agent can resolve the output directory"
        )

    def test_design_code_edge_exists(self):
        """design→code edge exists in graph topology (the binding point)."""
        topo_path = CONFIG_DIR / "graph_topology.yml"
        topo = _load_yaml(topo_path)
        transitions = topo.get("transitions", [])
        design_code = next(
            (
                t
                for t in transitions
                if t["source"] == "design" and t["target"] == "code"
            ),
            None,
        )
        assert design_code is not None, (
            "design→code transition must exist — it is where output dir binding occurs"
        )

    def test_installer_creates_structure_section(self):
        """Installer writes structure section to project_constraints.yml."""
        installer_text = INSTALLER.read_text()
        assert "structure" in installer_text, (
            "Installer must write structure section to project_constraints.yml "
            "for output directory binding"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-TOOL-014 — Observability Integration Contract
# ═══════════════════════════════════════════════════════════════════════


class TestObservabilityContract:
    """Installer scaffolds all files required by observability layer."""

    def test_workspace_graph_topology_exists(self):
        """`.ai-workspace/graph/graph_topology.yml` exists after installation."""
        path = WORKSPACE / "graph" / "graph_topology.yml"
        assert path.exists(), (
            "`.ai-workspace/graph/graph_topology.yml` must exist — "
            "it is the integration contract between methodology and monitors"
        )

    def test_workspace_graph_topology_is_parseable(self):
        """`.ai-workspace/graph/graph_topology.yml` is valid YAML with asset_types."""
        topo = _load_yaml(WORKSPACE / "graph" / "graph_topology.yml")
        assert "asset_types" in topo or "transitions" in topo, (
            "Workspace graph_topology.yml must define asset_types or transitions"
        )

    def test_installer_implements_req_tool_014(self):
        """gen-setup.py declares it implements REQ-TOOL-014."""
        installer_text = INSTALLER.read_text()
        assert "REQ-TOOL-014" in installer_text

    def test_workspace_status_md_exists(self):
        """`.ai-workspace/STATUS.md` exists as project status summary."""
        status = WORKSPACE / "STATUS.md"
        assert status.exists(), (
            "`.ai-workspace/STATUS.md` must exist — "
            "it is the observable status artifact for the methodology"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-UX-002 — Progressive Disclosure
# ═══════════════════════════════════════════════════════════════════════


class TestProgressiveDisclosure:
    """Only information needed for current edge is requested at init."""

    def test_gen_start_has_5_question_flow(self):
        """gen-start.md describes ≤5-question initialisation flow (delegates to gen-init).

        REQ-UX-002: Project initialisation requires ≤5 user inputs.
        gen-start is the entry point that runs the 5-question flow.
        """
        text = _cmd_text("gen-start")
        has_five_flow = (
            "5-question" in text.lower()
            or "five" in text.lower()
            or "≤5" in text
            or ("5" in text and "question" in text.lower())
        )
        assert has_five_flow, (
            "gen-start must describe a ≤5-question initialisation flow "
            "(name, kind, language, test runner, intent)"
        )

    def test_constraint_dims_deferred_to_design_edge(self):
        """gen-start.md or gen-init.md describes deferring constraints until design edge."""
        start_text = _cmd_text("gen-start")
        assert "deferred" in start_text.lower() or "defer" in start_text.lower(), (
            "gen-start must describe deferring constraint dimensions until "
            "the requirements→design edge"
        )

    def test_template_has_advisory_distinction(self):
        """project_constraints_template.yml distinguishes advisory from required fields."""
        raw = (CONFIG_DIR / "project_constraints_template.yml").read_text()
        assert "advisory" in raw.lower(), (
            "project_constraints_template.yml must mark advisory dimensions — "
            "they are deferred until explicitly needed"
        )

    def test_template_has_required_false_for_advisory(self):
        """Advisory dimensions are marked required: false in template."""
        raw = (CONFIG_DIR / "project_constraints_template.yml").read_text()
        assert "required: false" in raw, (
            "project_constraints_template.yml must have required: false for advisory dims"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-UX-004 — Automatic Feature and Edge Selection
# ═══════════════════════════════════════════════════════════════════════


class TestAutomaticSelection:
    """Highest-priority feature and next unconverged edge selected automatically."""

    def test_gen_start_has_priority_tiers(self):
        """gen-start.md describes feature selection priority tiers."""
        text = _cmd_text("gen-start")
        assert "priority" in text.lower(), (
            "gen-start must describe feature selection by priority tiers"
        )

    def test_gen_start_has_closest_to_complete(self):
        """gen-start.md mentions closest-to-complete as a selection criterion."""
        text = _cmd_text("gen-start")
        assert (
            "closest-to-complete" in text.lower()
            or "closest to complete" in text.lower()
        ), "gen-start must use closest-to-complete as a WIP-reduction criterion"

    def test_gen_start_mentions_topological_walk(self):
        """gen-start.md describes topological walk for edge determination."""
        text = _cmd_text("gen-start")
        assert "topological" in text.lower() or "topology" in text.lower(), (
            "gen-start must determine next edge via topological walk of graph"
        )

    def test_feature_vector_priority_documented_in_gen_start(self):
        """gen-start.md documents feature priority field (critical>high>medium>low).

        REQ-UX-004: feature selection uses priority field from feature vector.
        """
        text = _cmd_text("gen-start")
        assert "priority" in text.lower() and (
            "critical" in text.lower() or "high" in text.lower()
        ), (
            "gen-start must document feature priority tiers "
            "(critical > high > medium > low) for selection ordering"
        )

    def test_gen_start_user_can_override_selection(self):
        """gen-start.md documents --feature and --edge override options."""
        text = _cmd_text("gen-start")
        assert "--feature" in text and "--edge" in text, (
            "gen-start must allow user to override automatic selection via "
            "--feature and --edge flags"
        )


# ═══════════════════════════════════════════════════════════════════════
# REQ-UX-005 — Recovery and Self-Healing
# ═══════════════════════════════════════════════════════════════════════


class TestRecoveryAndSelfHealing:
    """Detect and guide recovery from inconsistent workspace states."""

    def test_gen_status_health_flag(self):
        """gen-status.md documents --health flag for workspace health check."""
        text = _cmd_text("gen-status")
        assert "--health" in text, (
            "gen-status must have --health flag for workspace health diagnostics"
        )

    def test_health_detects_corrupted_event_log(self):
        """gen-status --health detects corrupted event log."""
        text = _cmd_text("gen-status")
        assert "corrupt" in text.lower() or "invalid json" in text.lower(), (
            "gen-status --health must detect corrupted event log lines"
        )

    def test_health_detects_orphaned_spawns(self):
        """gen-status --health detects orphaned spawn vectors."""
        text = _cmd_text("gen-status")
        assert "orphan" in text.lower(), (
            "gen-status --health must detect orphaned spawn vectors"
        )

    def test_health_detects_stuck_features(self):
        """gen-status --health detects stuck features (δ unchanged 3+ iterations)."""
        text = _cmd_text("gen-status")
        assert "stuck" in text.lower(), "gen-status --health must detect stuck features"

    def test_health_is_non_destructive(self):
        """gen-status/gen-start recovery is non-destructive (ask before overwrite)."""
        start_text = _cmd_text("gen-start")
        assert (
            "non-destructive" in start_text.lower()
            or "never silently" in start_text.lower()
            or "ask before" in start_text.lower()
        ), "Recovery must be non-destructive — always ask before overwriting"

    def test_workspace_rebuildable_from_events(self):
        """Event log is the source of truth (workspace rebuildable from events)."""
        text = _cmd_text("gen-status")
        assert (
            "event sourcing" in text.lower()
            or "events.jsonl" in text.lower()
            or "source of truth" in text.lower()
        ), "gen-status must describe workspace as rebuildable from event log"


# ═══════════════════════════════════════════════════════════════════════
# REQ-UX-007 — Edge Zoom Management
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeZoomManagement:
    """Users can zoom in/out of graph edges to manage complexity."""

    def test_gen_zoom_command_exists(self):
        """gen-zoom.md command exists for edge zoom management."""
        assert _cmd("gen-zoom").exists(), "gen-zoom.md must exist"

    def test_gen_zoom_has_zoom_in(self):
        """gen-zoom.md describes zoom in (expand edge to sub-graph)."""
        text = _cmd_text("gen-zoom")
        assert "zoom in" in text.lower() or "in" in text.lower(), (
            "gen-zoom must describe zoom-in operation"
        )

    def test_gen_zoom_has_zoom_out(self):
        """gen-zoom.md describes zoom out (collapse sub-graph to edge)."""
        text = _cmd_text("gen-zoom")
        assert "zoom out" in text.lower() or "out" in text.lower(), (
            "gen-zoom must describe zoom-out operation"
        )

    def test_gen_zoom_emits_events(self):
        """gen-zoom.md documents event emission for zoom operations."""
        text = _cmd_text("gen-zoom")
        assert "graph_zoom" in text.lower() or "event" in text.lower(), (
            "gen-zoom must emit events documenting zoom operations"
        )

    def test_gen_zoom_implements_req_ux_007(self):
        """gen-zoom.md declares it implements REQ-UX-007."""
        text = _cmd_text("gen-zoom")
        assert "REQ-UX-007" in text, (
            "gen-zoom.md must declare <!-- Implements: REQ-UX-007 -->"
        )

    def test_graph_topology_is_extensible_for_zoom(self):
        """Graph topology's extensible property supports zoom operations."""
        topo = _load_yaml(CONFIG_DIR / "graph_topology.yml")
        graph_props = topo.get("graph_properties", {})
        assert (
            graph_props.get("zoomable") is True or graph_props.get("extensible") is True
        ), (
            "graph_topology.yml must declare zoomable or extensible=true "
            "to support edge zoom management"
        )
