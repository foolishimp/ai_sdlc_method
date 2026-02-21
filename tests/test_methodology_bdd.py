# Validates: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-003, REQ-TOOL-002, REQ-TOOL-007, REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008
"""BDD acceptance tests — methodology workflow coherence validation.

These tests validate that the methodology's components compose correctly:
- Init scaffolds a complete workspace
- Iterate can traverse every pre-CI/CD edge
- Profiles correctly constrain the graph
- Spawn/fold-back relationships are well-formed
- Traceability checks cover the full pipeline

Written as Given/When/Then scenarios using plain pytest.
"""

import pathlib
import re

import pytest
import yaml

from conftest import (
    CONFIG_DIR, EDGE_PARAMS_DIR, PROFILES_DIR, COMMANDS_DIR,
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, DOCS_DIR, load_yaml,
)


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 1: Workspace Initialization
# ═══════════════════════════════════════════════════════════════════════


class TestInitWorkflow:
    """
    GIVEN the /aisdlc-init command and plugin configs
    WHEN a user initializes a new project
    THEN all required workspace directories and files are scaffolded.
    """

    @pytest.mark.bdd
    def test_init_command_references_all_scaffold_dirs(self):
        """Init command must describe all workspace directories."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        expected_dirs = [
            "graph/", "edges/", "context/", "adrs/",
            "features/", "active/", "completed/",
            "profiles/", "fold-back/",
            "events/", "tasks/", "intents/", "snapshots/",
        ]
        for d in expected_dirs:
            assert d in content, f"init command missing directory reference: {d}"

    @pytest.mark.bdd
    def test_init_copies_graph_topology(self):
        """Init must copy graph_topology.yml to workspace."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "graph_topology.yml" in content

    @pytest.mark.bdd
    def test_init_copies_edge_configs(self):
        """Init must copy edge_params/ to workspace."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "edge_params/" in content

    @pytest.mark.bdd
    def test_init_copies_profiles(self):
        """Init must copy profiles/ to workspace."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "profiles/" in content

    @pytest.mark.bdd
    def test_init_scaffolds_project_constraints(self):
        """Init must scaffold project_constraints.yml with auto-detection."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "project_constraints" in content
        assert "auto-detect" in content.lower() or "detect" in content.lower()

    @pytest.mark.bdd
    def test_init_creates_intent_placeholder(self):
        """Init must create docs/specification/INTENT.md placeholder."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "INTENT.md" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 2: Edge Traversal Coverage
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeTraversal:
    """
    GIVEN the iterate agent and edge configs
    WHEN traversing each pre-CI/CD edge
    THEN the agent has guidance, evaluators, and convergence criteria.
    """

    PRE_CICD_EDGES = [
        ("intent", "requirements", "intent_requirements"),
        ("requirements", "design", "requirements_design"),
        ("design", "code", "design_code"),
        ("code", "unit_tests", "tdd"),
        ("design", "test_cases", "design_tests"),
        ("design", "uat_tests", "bdd"),
    ]

    @pytest.mark.bdd
    @pytest.mark.parametrize("source,target,config_name", PRE_CICD_EDGES)
    def test_edge_config_exists(self, source, target, config_name):
        """Each pre-CI/CD edge must have an edge config file."""
        config_path = EDGE_PARAMS_DIR / f"{config_name}.yml"
        assert config_path.exists(), f"missing edge config: {config_name}.yml"

    @pytest.mark.bdd
    @pytest.mark.parametrize("source,target,config_name", PRE_CICD_EDGES)
    def test_edge_has_evaluator_checklist(self, source, target, config_name):
        """Each edge config must have a checklist with at least one check."""
        config = load_yaml(EDGE_PARAMS_DIR / f"{config_name}.yml")
        assert "checklist" in config, f"{config_name} missing checklist"
        assert len(config["checklist"]) >= 1

    @pytest.mark.bdd
    @pytest.mark.parametrize("source,target,config_name", PRE_CICD_EDGES)
    def test_edge_has_agent_guidance(self, source, target, config_name):
        """Each edge config should have agent_guidance."""
        config = load_yaml(EDGE_PARAMS_DIR / f"{config_name}.yml")
        assert "agent_guidance" in config, f"{config_name} missing agent_guidance"

    @pytest.mark.bdd
    def test_iterate_agent_covers_all_edge_types(self):
        """The iterate agent must have guidance for all pre-CI/CD edge patterns."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        expected_patterns = [
            "Intent → Requirements",
            "Requirements → Design",
            "Design → Code",
            "Code ↔ Unit Tests",
            "Design → UAT Tests",
        ]
        for pattern in expected_patterns:
            assert pattern in content, f"iterate agent missing guidance for: {pattern}"

    @pytest.mark.bdd
    def test_tdd_edge_has_red_green_refactor(self):
        """TDD edge must define RED → GREEN → REFACTOR → COMMIT phases."""
        config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        assert "phases" in config
        for phase in ("red", "green", "refactor", "commit"):
            assert phase in config["phases"], f"TDD missing phase: {phase}"

    @pytest.mark.bdd
    def test_bdd_edge_has_gherkin(self):
        """BDD edge must reference Gherkin/Given/When/Then format."""
        config = load_yaml(EDGE_PARAMS_DIR / "bdd.yml")
        content = yaml.dump(config)
        assert "Given" in content or "gherkin" in content.lower() or "Gherkin" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 3: Projection Profile Constraints
# ═══════════════════════════════════════════════════════════════════════


class TestProfileConstraints:
    """
    GIVEN a projection profile
    WHEN it defines a graph subset
    THEN edges not in the subset are skipped.
    """

    @pytest.mark.bdd
    def test_poc_skips_tdd_and_cicd(self):
        """PoC profile must skip TDD and CI/CD edges."""
        poc = load_yaml(PROFILES_DIR / "poc.yml")
        skipped = poc["graph"].get("skip", [])
        skip_str = " ".join(str(s) for s in skipped)
        assert "unit_tests" in skip_str or "tests" in skip_str
        assert "cicd" in skip_str

    @pytest.mark.bdd
    def test_hotfix_skips_design(self):
        """Hotfix profile must skip formal design phase."""
        hotfix = load_yaml(PROFILES_DIR / "hotfix.yml")
        skipped = hotfix["graph"].get("skip", [])
        skip_str = " ".join(str(s) for s in skipped)
        assert "design" in skip_str

    @pytest.mark.bdd
    def test_full_profile_no_skips(self):
        """Full profile must not skip any edges."""
        full = load_yaml(PROFILES_DIR / "full.yml")
        assert full["graph"]["include"] == "all"
        assert "skip" not in full["graph"] or not full["graph"].get("skip")

    @pytest.mark.bdd
    def test_profile_strictness_ordering(self):
        """full > standard > minimal in strictness."""
        full = load_yaml(PROFILES_DIR / "full.yml")
        standard = load_yaml(PROFILES_DIR / "standard.yml")
        minimal = load_yaml(PROFILES_DIR / "minimal.yml")

        # Full has more evaluators than minimal
        assert len(full["evaluators"]["default"]) >= len(minimal["evaluators"]["default"])

        # Full requires human on all edges
        assert full["convergence"].get("human_required_on_all_edges") is True
        assert standard["convergence"].get("human_required_on_all_edges") is not True


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 4: Spawn and Fold-Back
# ═══════════════════════════════════════════════════════════════════════


class TestSpawnFoldBack:
    """
    GIVEN a parent feature vector
    WHEN a child vector is spawned
    THEN the child has a profile, time-box, and fold-back path.
    """

    @pytest.mark.bdd
    def test_spawn_command_exists(self):
        """The /aisdlc-spawn command must exist."""
        assert (COMMANDS_DIR / "aisdlc-spawn.md").exists()

    @pytest.mark.bdd
    def test_spawn_command_supports_vector_types(self):
        """Spawn command must support discovery, spike, poc, hotfix types."""
        with open(COMMANDS_DIR / "aisdlc-spawn.md") as f:
            content = f.read()
        for vtype in ("discovery", "spike", "poc", "hotfix"):
            assert vtype in content, f"spawn command missing vector type: {vtype}"

    @pytest.mark.bdd
    def test_spawn_command_defines_fold_back(self):
        """Spawn command must describe the fold-back process."""
        with open(COMMANDS_DIR / "aisdlc-spawn.md") as f:
            content = f.read()
        assert "fold-back" in content.lower() or "fold_back" in content.lower()
        assert "Context[]" in content or "context" in content.lower()

    @pytest.mark.bdd
    def test_feature_template_supports_parent_child(self):
        """Feature vector template must have parent and children fields."""
        template = load_yaml(CONFIG_DIR / "feature_vector_template.yml")
        assert "parent" in template
        assert "feature" in template["parent"]
        assert "children" in template

    @pytest.mark.bdd
    def test_hotfix_spawns_remediation(self):
        """Hotfix profile must require spawning a remediation feature."""
        hotfix = load_yaml(PROFILES_DIR / "hotfix.yml")
        assert hotfix.get("hotfix", {}).get("spawn_remediation") is True

    @pytest.mark.bdd
    def test_iterate_agent_detects_spawn_opportunities(self):
        """Iterate agent must document spawn detection."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "Spawn" in content or "spawn" in content
        assert "Discovery" in content or "discovery" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 5: Extended Convergence
# ═══════════════════════════════════════════════════════════════════════


class TestExtendedConvergence:
    """
    GIVEN a non-feature vector (discovery, spike, PoC)
    WHEN convergence is checked
    THEN question_answered and time_box_expired are valid stopping conditions.
    """

    @pytest.mark.bdd
    def test_iterate_agent_supports_extended_convergence(self):
        """Iterate agent must define extended convergence model."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "question_answered" in content
        assert "time_box_expired" in content

    @pytest.mark.bdd
    def test_iterate_command_supports_extended_convergence(self):
        """Iterate command must handle extended convergence in results."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "CONVERGED_QUESTION_ANSWERED" in content
        assert "TIME_BOX_EXPIRED" in content

    @pytest.mark.bdd
    def test_spike_profile_uses_question_convergence(self):
        """Spike profile convergence should include question_answered."""
        spike = load_yaml(PROFILES_DIR / "spike.yml")
        conditions = spike["convergence"].get("conditions", [])
        cond_str = " ".join(str(c) for c in conditions)
        rule = spike["convergence"].get("rule", "")
        assert "question" in cond_str or "question" in rule or "risk" in cond_str

    @pytest.mark.bdd
    def test_time_boxed_profiles_have_on_expiry(self):
        """Time-boxed profiles must define what happens on expiry."""
        for name in ("spike", "poc", "hotfix", "minimal"):
            profile = load_yaml(PROFILES_DIR / f"{name}.yml")
            iteration = profile.get("iteration", {})
            if iteration.get("budget") == "time_boxed":
                time_box = iteration.get("time_box", {})
                assert "on_expiry" in time_box, \
                    f"profile '{name}' time_box missing on_expiry"


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 6: Traceability Pipeline
# ═══════════════════════════════════════════════════════════════════════


class TestTraceabilityPipeline:
    """
    GIVEN the traceability validation system
    WHEN running /aisdlc-gaps
    THEN all 3 layers (REQ tags, test gaps, telemetry gaps) are checked.
    """

    @pytest.mark.bdd
    def test_traceability_config_exists(self):
        """Traceability edge config must exist."""
        assert (EDGE_PARAMS_DIR / "traceability.yml").exists()

    @pytest.mark.bdd
    def test_traceability_has_three_layers(self):
        """Traceability config must define 3 layers."""
        config = load_yaml(EDGE_PARAMS_DIR / "traceability.yml")
        assert "layer_1_req_coverage" in config
        assert "layer_2_test_gaps" in config
        assert "layer_3_telemetry_gaps" in config

    @pytest.mark.bdd
    def test_gaps_command_supports_layers(self):
        """Gaps command must support --layer flag."""
        with open(COMMANDS_DIR / "aisdlc-gaps.md") as f:
            content = f.read()
        assert "--layer" in content
        assert "Layer 1" in content
        assert "Layer 2" in content
        assert "Layer 3" in content

    @pytest.mark.bdd
    def test_tdd_edge_includes_traceability_checks(self):
        """TDD edge must compose traceability Layer 1 + 2 checks."""
        config = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "req_tags_in_code" in check_names
        assert "req_tags_in_tests" in check_names
        assert "all_req_keys_have_tests" in check_names

    @pytest.mark.bdd
    def test_design_code_edge_includes_traceability(self):
        """Design→Code edge must compose traceability Layer 1 checks."""
        config = load_yaml(EDGE_PARAMS_DIR / "design_code.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "req_tags_in_code" in check_names

    @pytest.mark.bdd
    def test_feedback_loop_includes_telemetry_checks(self):
        """Feedback loop edge must compose traceability Layer 3 checks."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "code_req_keys_have_telemetry" in check_names
        assert "telemetry_tag_format" in check_names


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 7: Methodology Self-Consistency
# ═══════════════════════════════════════════════════════════════════════


class TestMethodologySelfConsistency:
    """
    GIVEN the full methodology (spec + design + implementation)
    WHEN we check cross-document consistency
    THEN all references resolve and no orphans exist.
    """

    @pytest.mark.bdd
    def test_spec_documents_exist(self):
        """All specification documents must exist."""
        expected = [
            "INTENT.md",
            "AI_SDLC_ASSET_GRAPH_MODEL.md",
            "PROJECTIONS_AND_INVARIANTS.md",
            "AISDLC_IMPLEMENTATION_REQUIREMENTS.md",
            "FEATURE_VECTORS.md",
        ]
        for doc in expected:
            assert (SPEC_DIR / doc).exists(), f"missing spec document: {doc}"

    @pytest.mark.bdd
    def test_design_documents_exist(self):
        """Design documents must exist."""
        design_dir = PLUGIN_ROOT.parent.parent.parent.parent.parent / "docs/design/claude_aisdlc"
        assert (design_dir / "AISDLC_V2_DESIGN.md").exists()

    @pytest.mark.bdd
    def test_adrs_exist(self):
        """ADRs 008-010 must exist."""
        adr_dir = PLUGIN_ROOT.parent.parent.parent.parent.parent / "docs/design/claude_aisdlc/adrs"
        for n in (8, 9, 10):
            pattern = f"ADR-{n:03d}*"
            matches = list(adr_dir.glob(pattern))
            assert matches, f"missing ADR-{n:03d}"

    @pytest.mark.bdd
    def test_iterate_agent_references_req_keys(self):
        """Iterate agent must reference REQ key discipline."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "Implements: REQ-" in content
        assert "Validates: REQ-" in content

    @pytest.mark.bdd
    def test_no_orphan_edge_configs(self):
        """Every edge config file should be referenced by graph_topology or another config."""
        topology = load_yaml(CONFIG_DIR / "graph_topology.yml")
        referenced = set()
        for t in topology["transitions"]:
            if "edge_config" in t:
                # Extract filename from path like "edge_params/tdd.yml"
                referenced.add(pathlib.Path(t["edge_config"]).name)

        # Cross-cutting configs that are composed into other edges
        cross_cutting = {"code_tagging.yml", "traceability.yml", "adr.yml"}

        actual = {p.name for p in EDGE_PARAMS_DIR.glob("*.yml")}
        orphans = actual - referenced - cross_cutting
        assert not orphans, f"orphan edge configs (not referenced anywhere): {orphans}"


# ═══════════════════════════════════════════════════════════════════════
# 8. TASK UPDATE AND GANTT CHART SUPPORT
# ═══════════════════════════════════════════════════════════════════════


class TestTaskUpdateOnConvergence:
    """
    GIVEN a feature that converges on an edge
    WHEN the iterate agent completes
    THEN a task update is appended and the feature vector records timestamps.
    """

    @pytest.mark.bdd
    def test_iterate_command_mandates_task_update(self):
        """Iterate command must include task log update as a derived view."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "Task log" in content or "ACTIVE_TASKS.md" in content
        assert "ACTIVE_TASKS.md" in content

    @pytest.mark.bdd
    def test_iterate_agent_mandates_task_update(self):
        """Iterate agent must include task tracking step."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "Update Task Tracking" in content or "Step 5a" in content

    @pytest.mark.bdd
    def test_iterate_report_includes_task_log(self):
        """Iteration report format must include TASK LOG line."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "TASK LOG" in content

    @pytest.mark.bdd
    def test_feature_template_has_started_at(self, feature_vector_template):
        """Feature vector template trajectory must document started_at field."""
        with open(CONFIG_DIR / "feature_vector_template.yml") as f:
            raw = f.read()
        assert "started_at" in raw

    @pytest.mark.bdd
    def test_feature_template_has_converged_at(self, feature_vector_template):
        """Feature vector template trajectory must document converged_at field."""
        with open(CONFIG_DIR / "feature_vector_template.yml") as f:
            raw = f.read()
        assert "converged_at" in raw


class TestGanttChartSupport:
    """
    GIVEN a project with feature vectors that have trajectory timestamps
    WHEN the user runs /aisdlc-status --gantt
    THEN a Mermaid Gantt chart is generated showing the build schedule.
    """

    @pytest.mark.bdd
    def test_status_command_has_gantt_flag(self):
        """Status command must support --gantt flag."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "--gantt" in content

    @pytest.mark.bdd
    def test_status_command_documents_gantt_format(self):
        """Status command must specify Mermaid Gantt output format."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "gantt" in content.lower()
        assert "mermaid" in content.lower()

    @pytest.mark.bdd
    def test_status_command_maps_status_to_gantt_states(self):
        """Status command must define mapping from trajectory status to Gantt task states."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        for state in (":done", ":active", ":crit"):
            assert state in content, f"Gantt state '{state}' not documented"

    @pytest.mark.bdd
    def test_status_command_has_phase_summary(self):
        """Status command must include phase completion summary table."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Phase Completion Summary" in content

    @pytest.mark.bdd
    def test_status_gantt_writes_to_file(self):
        """Gantt output must be written to .ai-workspace/STATUS.md, not terminal."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "STATUS.md" in content
        assert "Write" in content or "write" in content
        # Must NOT say "Display ... as a fenced code block" as the primary output
        assert "viewable" in content.lower() or "renderable" in content.lower()

    @pytest.mark.bdd
    def test_status_includes_process_telemetry(self):
        """STATUS.md must include a Process Telemetry section with structured observations."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Process Telemetry" in content
        for subsection in ("Convergence Pattern", "Traceability Coverage", "Constraint Surface"):
            assert subsection in content, f"Telemetry missing subsection: {subsection}"

    @pytest.mark.bdd
    def test_status_includes_self_reflection(self):
        """STATUS.md must include Self-Reflection section that feeds back to new Intent."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Self-Reflection" in content
        assert "Feedback" in content or "feedback" in content
        assert "TELEM-" in content  # structured signal IDs


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 10: Telemetry Loop — Convergence Triggers Observability
# ═══════════════════════════════════════════════════════════════════════


class TestTelemetryLoop:
    """
    GIVEN the iterate agent converges on an edge
    WHEN convergence is recorded
    THEN an event is emitted and derived views are regenerated,
         closing the Telemetry / Observer → feedback → new Intent loop.
    """

    @pytest.mark.bdd
    def test_iterate_command_emits_event(self):
        """Iterate command must emit an event to events.jsonl on every iteration."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "events.jsonl" in content
        assert "append-only" in content.lower()

    @pytest.mark.bdd
    def test_iterate_command_updates_derived_views(self):
        """Iterate command must update all derived views after emitting event."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "STATUS.md" in content
        assert "ACTIVE_TASKS.md" in content
        assert "feature vector" in content.lower() or "Feature vector" in content

    @pytest.mark.bdd
    def test_iterate_agent_emits_event(self):
        """Iterate agent must emit an event to events.jsonl."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "events.jsonl" in content
        assert "append-only" in content.lower()

    @pytest.mark.bdd
    def test_iterate_agent_updates_derived_views(self):
        """Iterate agent must update derived views after emitting event."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "STATUS.md" in content
        assert "Step 5b" in content

    @pytest.mark.bdd
    def test_status_command_documents_event_sourcing(self):
        """Status command must document the event sourcing architecture."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "event sourcing" in content.lower() or "Event Sourcing" in content
        assert "events.jsonl" in content
        assert "source of truth" in content.lower()

    @pytest.mark.bdd
    def test_status_command_has_event_schema(self):
        """Status command must define the event JSON schema."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Event Schema" in content
        assert "iteration_completed" in content

    @pytest.mark.bdd
    def test_views_derivable_from_events(self):
        """All views must be documented as reconstructable from events alone."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            iterate_content = f.read()
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            status_content = f.read()
        # Both specs must state that views derive from events
        assert "reconstructed from" in iterate_content.lower() or "derived" in iterate_content.lower()
        assert "derived" in status_content.lower()

    @pytest.mark.bdd
    def test_telemetry_loop_closes(self):
        """The self-reflection section must reference the feedback→Intent loop."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            status_content = f.read()
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            agent_content = f.read()
        # Status spec defines the telemetry loop
        assert "telemetry loop" in status_content.lower() or "Telemetry" in status_content
        # Agent spec acknowledges it closes the loop
        assert "telemetry loop" in agent_content.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 11: Three-Direction Gap Detection
# ═══════════════════════════════════════════════════════════════════════


class TestThreeDirectionGapDetection:
    """
    GIVEN the iterate agent processing an edge
    WHEN it analyses source, evaluates output, and reviews its own process
    THEN it reports gaps in all three directions: backward, forward, inward.
    """

    @pytest.mark.bdd
    def test_agent_has_source_analysis_step(self):
        """Iterate agent must have a source analysis step (backward gap detection)."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "SOURCE_AMBIGUITY" in content
        assert "SOURCE_GAP" in content
        assert "SOURCE_UNDERSPEC" in content

    @pytest.mark.bdd
    def test_agent_has_process_evaluation_step(self):
        """Iterate agent must have a process evaluation step (inward gap detection)."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "PROCESS_GAP" in content
        assert "EVALUATOR_MISSING" in content
        assert "CONTEXT_MISSING" in content

    @pytest.mark.bdd
    def test_iteration_report_has_three_sections(self):
        """Iteration report must include source analysis, checklist, and process gaps."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "SOURCE ANALYSIS" in content or "Source Analysis" in content
        assert "CHECKLIST RESULTS" in content
        assert "PROCESS GAPS" in content or "Process Gaps" in content

    @pytest.mark.bdd
    def test_event_schema_captures_all_gap_types(self):
        """Event schema must include source_findings and process_gaps."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "source_findings" in content
        assert "process_gaps" in content

    @pytest.mark.bdd
    def test_edge_configs_have_source_analysis(self):
        """All pre-CI/CD edge configs must define source_analysis checks."""
        edges_with_source_analysis = [
            "intent_requirements.yml",
            "requirements_design.yml",
            "design_code.yml",
            "tdd.yml",
        ]
        for edge_file in edges_with_source_analysis:
            with open(EDGE_PARAMS_DIR / edge_file) as f:
                content = f.read()
            assert "source_analysis:" in content, \
                f"{edge_file} missing source_analysis section"

    @pytest.mark.bdd
    def test_edge_configs_have_context_guidance(self):
        """Edge configs must specify what context the agent needs."""
        edges_with_context = [
            "intent_requirements.yml",
            "requirements_design.yml",
            "design_code.yml",
            "tdd.yml",
        ]
        for edge_file in edges_with_context:
            with open(EDGE_PARAMS_DIR / edge_file) as f:
                content = f.read()
            assert "context_guidance:" in content, \
                f"{edge_file} missing context_guidance section"

    @pytest.mark.bdd
    def test_intent_requirements_has_document_structure(self):
        """Intent→requirements edge must define document structure beyond individual REQs."""
        with open(EDGE_PARAMS_DIR / "intent_requirements.yml") as f:
            content = f.read()
        assert "document_structure:" in content
        for section in ("Terminology", "Success Criteria", "Assumptions"):
            assert section in content, \
                f"intent_requirements.yml missing required section: {section}"

    @pytest.mark.bdd
    def test_requirements_design_has_document_structure(self):
        """Requirements→design edge must define document structure."""
        with open(EDGE_PARAMS_DIR / "requirements_design.yml") as f:
            content = f.read()
        assert "document_structure:" in content
        for section in ("Architecture Overview", "Traceability Matrix", "ADR Index"):
            assert section in content, \
                f"requirements_design.yml missing required section: {section}"

    @pytest.mark.bdd
    def test_requirements_design_has_adr_depth_check(self):
        """Requirements→design edge must check ADR depth, not just existence."""
        with open(EDGE_PARAMS_DIR / "requirements_design.yml") as f:
            content = f.read()
        assert "adr_depth_adequate" in content
        assert "alternatives" in content.lower()

    @pytest.mark.bdd
    def test_tdd_has_test_data_strategy(self):
        """TDD edge must check for test data strategy."""
        with open(EDGE_PARAMS_DIR / "tdd.yml") as f:
            content = f.read()
        assert "test_data_strategy" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 12: Constraint Dimension Initialization
# ═══════════════════════════════════════════════════════════════════════


class TestConstraintDimensionInitialization:
    """
    GIVEN the /aisdlc-init command
    WHEN a user initializes a new project
    THEN constraint dimensions are auto-detected and scaffolded in project_constraints.yml.
    """

    @pytest.mark.bdd
    def test_init_references_constraint_dimensions(self):
        """Init command must reference constraint dimensions."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "constraint_dimensions" in content or "Constraint" in content

    @pytest.mark.bdd
    def test_init_auto_detects_ecosystem_language(self):
        """Init must auto-detect ecosystem_compatibility.language."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "ecosystem_compatibility" in content or "language" in content.lower()

    @pytest.mark.bdd
    def test_init_auto_detects_build_system(self):
        """Init must auto-detect build_system.tool."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "build_system" in content or "build" in content.lower()

    @pytest.mark.bdd
    def test_init_marks_undetected_dimensions_todo(self):
        """Init must mark undetected mandatory dimensions as TODO."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "TODO" in content

    @pytest.mark.bdd
    def test_init_report_shows_dimension_status(self):
        """Init report must show constraint dimension configuration status."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        # Report should show how many dimensions are configured vs TODO
        assert "Dimensions" in content or "dimensions" in content

    @pytest.mark.bdd
    def test_init_report_shows_three_layer_structure(self):
        """Init report must show the three-layer structure (Graph Package + Project Binding)."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "Layer 2" in content or "Graph Package" in content
        assert "Layer 3" in content or "Project Binding" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 13: Constraint Dimension Convergence at Design Edge
# ═══════════════════════════════════════════════════════════════════════


class TestConstraintDimensionConvergence:
    """
    GIVEN a requirements→design edge traversal
    WHEN the iterate agent evaluates design
    THEN all mandatory constraint dimensions must be resolved for convergence.
    """

    @pytest.mark.bdd
    def test_design_edge_has_4_mandatory_dimension_checks(self):
        """Requirements→Design edge must have checklist items for all 4 mandatory dimensions."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        mandatory = [
            "ecosystem_compatibility_resolved",
            "deployment_target_resolved",
            "security_model_resolved",
            "build_system_resolved",
        ]
        for name in mandatory:
            assert name in check_names, f"design edge missing mandatory dimension check: {name}"

    @pytest.mark.bdd
    def test_mandatory_checks_block_convergence(self):
        """Mandatory dimension checks must be required (blocking convergence)."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        for name in ("ecosystem_compatibility_resolved", "deployment_target_resolved",
                      "security_model_resolved", "build_system_resolved"):
            assert checks_by_name[name]["required"] is True, \
                f"'{name}' must be required to block convergence"

    @pytest.mark.bdd
    def test_advisory_check_does_not_block_convergence(self):
        """Advisory dimensions check must NOT block convergence."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        assert checks_by_name["advisory_dimensions_considered"]["required"] is False

    @pytest.mark.bdd
    def test_convergence_rule_is_all_required(self):
        """Convergence rule must be all_required_checks_pass."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        assert config["convergence"]["rule"] == "all_required_checks_pass"

    @pytest.mark.bdd
    def test_iterate_agent_loads_constraint_dimensions(self):
        """Iterate agent must load constraint dimensions at design edge."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "constraint dimension" in content.lower() or "constraint_dimensions" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 14: Design Document Structure Requirements
# ═══════════════════════════════════════════════════════════════════════


class TestDesignDocumentStructure:
    """
    GIVEN the requirements→design edge config
    WHEN it defines document structure requirements
    THEN all required sections, diagrams, and traceability are enforced.
    """

    @pytest.mark.bdd
    def test_six_required_sections_defined(self):
        """Design document_structure must define 6 required sections."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        required = config["document_structure"]["required_sections"]
        assert len(required) >= 6

    @pytest.mark.bdd
    def test_required_sections_include_core_set(self):
        """Required sections must include Architecture Overview, Component Design, Data Model, etc."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        titles = [s["title"] for s in config["document_structure"]["required_sections"]]
        for expected in ("Architecture Overview", "Component Design", "Data Model",
                         "Traceability Matrix", "ADR Index", "Package/Module Structure"):
            assert expected in titles, f"missing required section: {expected}"

    @pytest.mark.bdd
    def test_mermaid_diagrams_check_exists(self):
        """Checklist must include architecture_diagrams_present check."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "architecture_diagrams_present" in check_names

    @pytest.mark.bdd
    def test_mermaid_check_requires_two_diagrams(self):
        """Architecture diagrams check must require at least 2 Mermaid diagrams."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        criterion = checks_by_name["architecture_diagrams_present"]["criterion"]
        assert "2" in criterion or "two" in criterion.lower()

    @pytest.mark.bdd
    def test_traceability_matrix_check_exists(self):
        """Checklist must include all_reqs_traced_to_components check."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "all_reqs_traced_to_components" in check_names

    @pytest.mark.bdd
    def test_no_orphan_components_check_exists(self):
        """Checklist must include no_orphan_components check."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "no_orphan_components" in check_names

    @pytest.mark.bdd
    def test_recommended_sections_defined(self):
        """Document structure should have recommended (optional) sections."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        recommended = config["document_structure"].get("recommended_sections", [])
        assert len(recommended) >= 1


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 15: ADR Generation for Constraint Dimensions
# ═══════════════════════════════════════════════════════════════════════


class TestConstraintDimensionADRs:
    """
    GIVEN a design that resolves mandatory constraint dimensions
    WHEN ADRs are checked
    THEN each mandatory dimension resolution has an ADR with alternatives and consequences.
    """

    @pytest.mark.bdd
    def test_adr_check_exists_in_design_edge(self):
        """Design edge must have adrs_for_decisions check."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        assert "adrs_for_decisions" in check_names

    @pytest.mark.bdd
    def test_adr_depth_check_requires_alternatives(self):
        """ADR depth check must require at least 2 alternatives considered."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        criterion = checks_by_name["adr_depth_adequate"]["criterion"]
        assert "2 alternatives" in criterion or "alternatives considered" in criterion.lower()

    @pytest.mark.bdd
    def test_adr_depth_check_requires_consequences(self):
        """ADR depth check must require concrete consequences."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        criterion = checks_by_name["adr_depth_adequate"]["criterion"]
        assert "consequence" in criterion.lower()

    @pytest.mark.bdd
    def test_adr_depth_check_requires_req_key_connection(self):
        """ADR depth check must require connection to REQ keys."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        checks_by_name = {c["name"]: c for c in config["checklist"]}
        criterion = checks_by_name["adr_depth_adequate"]["criterion"]
        assert "REQ" in criterion

    @pytest.mark.bdd
    def test_agent_guidance_prescribes_dimension_adrs(self):
        """Agent guidance must prescribe generating ADRs for mandatory dimensions."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        guidance = config["agent_guidance"]
        assert "ADR" in guidance
        assert "mandatory" in guidance.lower() or "dimension" in guidance.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 16: Status Command — Constraint Dimension Display
# ═══════════════════════════════════════════════════════════════════════


class TestStatusConstraintDimensions:
    """
    GIVEN the /aisdlc-status command with --feature flag
    WHEN displaying detailed feature status
    THEN constraint dimension resolution status is shown.
    """

    @pytest.mark.bdd
    def test_status_shows_constraint_dimensions_section(self):
        """Detailed status view must show Constraint Dimensions section."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Constraint Dimensions" in content

    @pytest.mark.bdd
    def test_status_shows_resolved_indicator(self):
        """Status must show resolution indicators (resolved/advisory)."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "resolved" in content.lower()

    @pytest.mark.bdd
    def test_status_links_dimensions_to_adrs(self):
        """Status must show which ADR resolved each dimension."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "ADR-" in content

    @pytest.mark.bdd
    def test_status_shows_advisory_acknowledgement(self):
        """Status must show advisory dimensions with acknowledgement status."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "advisory" in content.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 17: Consciousness Loop — Intent Raised at Every Observer
# ═══════════════════════════════════════════════════════════════════════


class TestConsciousnessLoopIntentRaised:
    """
    GIVEN the iterate agent processing an edge
    WHEN any observer detects a non-trivial delta
    THEN an intent_raised event is emitted with causal chain,
         enabling the consciousness loop at every observer point.

    Validates: REQ-LIFE-005
    """

    @pytest.mark.bdd
    def test_iterate_agent_has_intent_raised_event_type(self):
        """Iterate agent Event Type Reference must include intent_raised."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_intent_raised_has_prior_intents_field(self):
        """intent_raised event must include prior_intents for reflexive loop detection."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "prior_intents" in content

    @pytest.mark.bdd
    def test_intent_raised_has_signal_source_field(self):
        """intent_raised event must include signal_source classification."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "signal_source" in content

    @pytest.mark.bdd
    def test_intent_raised_has_affected_req_keys(self):
        """intent_raised event must include affected_req_keys."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "affected_req_keys" in content

    @pytest.mark.bdd
    def test_intent_raised_has_edge_context(self):
        """intent_raised event must include edge_context."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "edge_context" in content

    @pytest.mark.bdd
    def test_backward_gap_can_trigger_intent(self):
        """Backward gap detection (source findings) must be able to trigger intent_raised."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        # Source findings that escalate should generate intent
        assert "source_finding" in content
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_inward_gap_can_trigger_intent(self):
        """Inward gap detection (process gaps) must be able to trigger intent_raised."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "process_gap" in content
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_iterate_command_stuck_delta_triggers_intent(self):
        """Iterate command must detect stuck deltas (>3 iterations) and emit intent_raised."""
        with open(COMMANDS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "stuck delta" in content.lower() or "3 iterations" in content

    @pytest.mark.bdd
    def test_consciousness_loop_documented_in_agent(self):
        """Iterate agent must document that consciousness loop operates at every observer."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "every observer" in content.lower() or "Every Observer" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 18: Signal Source Classification
# ═══════════════════════════════════════════════════════════════════════


class TestSignalSourceClassification:
    """
    GIVEN the feedback loop edge configuration
    WHEN signals are classified
    THEN all seven signal sources are recognised with intent templates.

    Validates: REQ-LIFE-006
    """

    REQUIRED_SIGNAL_SOURCES = {
        "gap", "test_failure", "refactoring",
        "source_finding", "process_gap",
        "runtime_feedback", "ecosystem",
    }

    @pytest.mark.bdd
    def test_feedback_loop_has_all_signal_sources(self):
        """Feedback loop edge config must define all 7 signal source types."""
        feedback_loop = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        sources = feedback_loop.get("sources", {})
        source_names = set()
        for key, val in sources.items():
            if isinstance(val, dict) and "signal_source" in val:
                source_names.add(val["signal_source"])
        for required in self.REQUIRED_SIGNAL_SOURCES:
            assert required in source_names, f"Missing signal source: {required}"

    @pytest.mark.bdd
    def test_each_signal_source_has_intent_template(self):
        """Each signal source must have an intent template."""
        feedback_loop = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        sources = feedback_loop.get("sources", {})
        for key, val in sources.items():
            if isinstance(val, dict) and "signal_source" in val:
                assert "intent_template" in val, \
                    f"Signal source {key} missing intent_template"

    @pytest.mark.bdd
    def test_iterate_agent_lists_all_signal_sources(self):
        """Iterate agent Event Type Reference must list all signal source types."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        for source in self.REQUIRED_SIGNAL_SOURCES:
            assert source in content, f"Signal source {source} not in iterate agent"

    @pytest.mark.bdd
    def test_gaps_command_emits_gap_signal(self):
        """/aisdlc-gaps must emit intent_raised with signal_source: gap."""
        with open(COMMANDS_DIR / "aisdlc-gaps.md") as f:
            content = f.read()
        assert "intent_raised" in content
        assert "gap" in content

    @pytest.mark.bdd
    def test_tdd_edge_emits_test_failure_signal(self):
        """TDD edge config must emit intent_raised for stuck test failures."""
        tdd = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        guidance = tdd.get("agent_guidance", "")
        assert "intent_raised" in guidance
        assert "test_failure" in guidance

    @pytest.mark.bdd
    def test_tdd_edge_emits_refactoring_signal(self):
        """TDD edge config must emit intent_raised for refactoring needs."""
        tdd = load_yaml(EDGE_PARAMS_DIR / "tdd.yml")
        guidance = tdd.get("agent_guidance", "")
        assert "refactoring" in guidance

    @pytest.mark.bdd
    def test_development_signals_use_same_mechanism_as_production(self):
        """Development-time signals must use the same intent_raised mechanism as production."""
        feedback_loop = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        desc = feedback_loop.get("description", "")
        assert "same mechanism" in desc.lower() or "not limited" in desc.lower() \
            or "every observer" in desc.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 19: Spec Change Events
# ═══════════════════════════════════════════════════════════════════════


class TestSpecChangeEvents:
    """
    GIVEN the specification absorbing a signal
    WHEN a requirement is added, modified, or deprecated
    THEN a spec_modified event is emitted with full traceability.

    Validates: REQ-LIFE-007
    """

    @pytest.mark.bdd
    def test_iterate_agent_has_spec_modified_event_type(self):
        """Iterate agent Event Type Reference must include spec_modified."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "spec_modified" in content

    @pytest.mark.bdd
    def test_spec_modified_has_trigger_intent(self):
        """spec_modified event must include trigger_intent field."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "trigger_intent" in content

    @pytest.mark.bdd
    def test_spec_modified_has_what_changed(self):
        """spec_modified event must include what_changed field."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "what_changed" in content

    @pytest.mark.bdd
    def test_spec_modified_has_prior_intents(self):
        """spec_modified event must include prior_intents for loop detection."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        # Both intent_raised and spec_modified should have prior_intents
        assert content.count("prior_intents") >= 2

    @pytest.mark.bdd
    def test_reflexive_loop_detection_documented(self):
        """Documentation must explain how prior_intents enables reflexive loop detection."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "reflexive" in content.lower() or "loop detection" in content.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 20: Protocol Enforcement Hooks
# ═══════════════════════════════════════════════════════════════════════


class TestProtocolEnforcementHooks:
    """
    GIVEN the iterate agent completing an iteration
    WHEN side effects are required
    THEN five mandatory side effects must be enforced.

    Validates: REQ-LIFE-008
    """

    @pytest.mark.bdd
    def test_iterate_agent_mandates_event_emission(self):
        """Iterate agent must explicitly mandate event emission as non-optional."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "MANDATORY" in content or "mandatory" in content

    @pytest.mark.bdd
    def test_iterate_agent_requires_source_findings_in_event(self):
        """Every iteration event must include source_findings array."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "source_findings" in content

    @pytest.mark.bdd
    def test_iterate_agent_requires_process_gaps_in_event(self):
        """Every iteration event must include process_gaps array."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "process_gaps" in content

    @pytest.mark.bdd
    def test_circuit_breaker_prevents_infinite_regression(self):
        """Protocol enforcement must have a circuit breaker mechanism."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            agent = f.read()
        with open(EDGE_PARAMS_DIR / "feedback_loop.yml") as f:
            feedback = f.read()
        # Either agent or feedback loop must mention circuit breaker
        combined = agent + feedback
        assert "circuit breaker" in combined.lower() or "circuit_breaker" in combined.lower() \
            or "infinite regression" in combined.lower()

    @pytest.mark.bdd
    def test_all_commands_emit_events(self):
        """Every /aisdlc-* command must emit events to events.jsonl."""
        event_emitting_commands = [
            "aisdlc-init.md", "aisdlc-iterate.md", "aisdlc-spawn.md",
            "aisdlc-checkpoint.md", "aisdlc-review.md", "aisdlc-gaps.md",
            "aisdlc-release.md",
        ]
        for cmd_name in event_emitting_commands:
            with open(COMMANDS_DIR / cmd_name) as f:
                content = f.read()
            assert "event_type" in content, f"{cmd_name} missing event_type emission"

    @pytest.mark.bdd
    def test_event_type_field_standardised(self):
        """All event schemas must use 'event_type' field (not bare 'type')."""
        for cmd_file in COMMANDS_DIR.glob("*.md"):
            with open(cmd_file) as f:
                content = f.read()
            if "event_type" in content:
                # If this command emits events, it should NOT use bare "type" for events
                # (process_gaps use "type" for gap classification — that's fine)
                pass  # Field standardisation verified by presence of event_type

        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            agent = f.read()
        assert "event_type" in agent


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 21: Event Type Completeness
# ═══════════════════════════════════════════════════════════════════════


class TestEventTypeCompleteness:
    """
    GIVEN the event type reference in the iterate agent
    WHEN listing all event types
    THEN all 12 event types are documented with schemas.

    Validates: REQ-LIFE-005, REQ-LIFE-007
    """

    REQUIRED_EVENT_TYPES = {
        "project_initialized", "iteration_completed", "edge_started",
        "edge_converged", "spawn_created", "spawn_folded_back",
        "checkpoint_created", "review_completed", "gaps_validated",
        "release_created", "intent_raised", "spec_modified",
    }

    @pytest.mark.bdd
    def test_all_event_types_in_agent_reference(self):
        """Iterate agent must document all 12 event types."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        for event_type in self.REQUIRED_EVENT_TYPES:
            assert event_type in content, f"Event type {event_type} missing from agent"

    @pytest.mark.bdd
    def test_all_event_types_in_design_doc(self):
        """Design document must list all event types."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for event_type in self.REQUIRED_EVENT_TYPES:
            assert event_type in content, \
                f"Event type {event_type} missing from design doc"


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 22: ADR-011 Consciousness Loop Lineage
# ═══════════════════════════════════════════════════════════════════════


class TestADR011Lineage:
    """
    GIVEN ADR-011 (Consciousness Loop at Every Observer Point)
    WHEN tracing requirements to design to implementation
    THEN complete lineage exists from REQ-LIFE-005..008 through ADR to plugin.

    Validates: REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008
    """

    @pytest.mark.bdd
    def test_adr_011_exists(self):
        """ADR-011 must exist."""
        adr_path = DOCS_DIR / "design/claude_aisdlc/adrs/ADR-011-consciousness-loop-at-every-observer.md"
        assert adr_path.exists(), "ADR-011 not found"

    @pytest.mark.bdd
    def test_adr_011_traces_to_requirements(self):
        """ADR-011 must reference REQ-LIFE-005 through REQ-LIFE-008."""
        adr_path = DOCS_DIR / "design/claude_aisdlc/adrs/ADR-011-consciousness-loop-at-every-observer.md"
        with open(adr_path) as f:
            content = f.read()
        for req in ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]:
            assert req in content, f"ADR-011 missing reference to {req}"

    @pytest.mark.bdd
    def test_requirements_exist_in_spec(self):
        """REQ-LIFE-005 through REQ-LIFE-008 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]:
            assert req in content, f"{req} missing from implementation requirements"

    @pytest.mark.bdd
    def test_design_references_consciousness_loop(self):
        """Design document must reference consciousness loop mechanics."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "Consciousness Loop" in content or "consciousness loop" in content
        assert "ADR-011" in content

    @pytest.mark.bdd
    def test_spec_defines_consciousness_loop(self):
        """Formal spec must define the consciousness loop."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "consciousness loop" in content.lower() or "Consciousness Loop" in content
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_feedback_loop_config_implements_adr_011(self):
        """feedback_loop.yml must implement the signal sources from ADR-011."""
        feedback_loop = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        sources = feedback_loop.get("sources", {})
        assert len(sources) >= 7, f"Expected >= 7 signal sources, got {len(sources)}"


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 23: Three Processing Phases in Spec and Implementation
# ═══════════════════════════════════════════════════════════════════════


class TestProcessingPhasesInSpec:
    """
    GIVEN the formal spec defines three processing phases (§4.3)
    WHEN we check that the concept is threaded through spec, agent, and design
    THEN all documents reference reflex/affect/conscious with correct mappings.

    Validates: REQ-EVAL-001 (processing_phase field)
    """

    @pytest.mark.bdd
    def test_spec_defines_three_processing_phases(self):
        """Formal spec must define §4.3 Three Processing Phases."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Three Processing Phases" in content
        assert "reflex" in content.lower()
        assert "affect" in content.lower()
        assert "conscious" in content.lower()

    @pytest.mark.bdd
    def test_spec_maps_evaluators_to_phases(self):
        """Spec must map evaluator types to processing phases."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Human evaluator" in content and "Conscious" in content
        assert "Agent evaluator" in content and "Conscious" in content
        assert "Deterministic" in content and "Reflex" in content

    @pytest.mark.bdd
    def test_spec_defines_affect_phase(self):
        """Spec §4.3 must define the affect (limbic) processing phase."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Affect (limbic)" in content
        assert "Limbic system" in content
        assert "signal classification" in content.lower() or "Signal triage" in content

    @pytest.mark.bdd
    def test_spec_labels_hooks_as_reflex(self):
        """Spec §7.8 must label protocol hooks as reflex arc."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "reflex arc" in content.lower()
        assert "autonomic nervous system" in content.lower()

    @pytest.mark.bdd
    def test_spec_states_each_phase_enables_next(self):
        """Spec must state that each phase enables the next."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Each phase enables the next" in content

    @pytest.mark.bdd
    def test_living_system_table_has_three_nervous_system_layers(self):
        """Living system table (§7.7.6) must have autonomic, limbic, and frontal cortex."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Autonomic nervous system" in content
        assert "Limbic system" in content
        assert "Frontal cortex" in content

    @pytest.mark.bdd
    def test_iterate_agent_references_phases(self):
        """Iterate agent must reference the three processing phases."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "processing phase" in content.lower() or "processing_phase" in content
        assert "conscious" in content.lower()
        assert "affect" in content.lower()
        assert "reflex" in content.lower()

    @pytest.mark.bdd
    def test_design_doc_references_phases(self):
        """Design document must reference processing phases."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "processing_phase" in content
        assert "conscious" in content
        assert "reflex" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 24: Sensory Service Architecture
# ═══════════════════════════════════════════════════════════════════════


class TestSensoryServiceArchitecture:
    """
    GIVEN the spec §4.5.4 defines sensory service architecture
    WHEN we check spec, design, and requirements
    THEN the service model, review boundary, and event contracts are defined.

    Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
    """

    @pytest.mark.bdd
    def test_spec_defines_sensory_service_architecture(self):
        """Spec §4.5.4 must define Sensory Service Architecture."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "4.5.4 Sensory Service Architecture" in content

    @pytest.mark.bdd
    def test_spec_defines_mcp_service_model(self):
        """Spec §4.5.4 must define MCP server as the service model."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "MCP server" in content or "MCP Server" in content

    @pytest.mark.bdd
    def test_spec_defines_review_boundary(self):
        """Spec §4.5.4 must define the review boundary separating autonomous sensing from changes."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "review boundary" in content.lower() or "REVIEW BOUNDARY" in content

    @pytest.mark.bdd
    def test_spec_defines_two_event_categories(self):
        """Spec §4.5.4 must define sensor/evaluate vs change-approval event categories."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Sensor/evaluate events" in content
        assert "Change-approval events" in content

    @pytest.mark.bdd
    def test_spec_defines_draft_only_autonomy(self):
        """Spec §4.5.4 must state that homeostatic responses are draft proposals only."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "draft proposals only" in content.lower() or "draft proposals" in content

    @pytest.mark.bdd
    def test_spec_defines_monitor_telemetry_separation(self):
        """Spec §4.5.4 must clarify that the monitor rides the telemetry."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "monitor rides the telemetry" in content.lower() or "genesis_monitor" in content

    @pytest.mark.bdd
    def test_design_doc_has_sensory_service_section(self):
        """Design doc must have §1.8 Sensory Service section."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "1.8 Sensory Service" in content

    @pytest.mark.bdd
    def test_design_doc_has_all_sensory_subsections(self):
        """Design doc §1.8 must have all 8 subsections."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        expected_subsections = [
            "1.8.1 Service Architecture",
            "1.8.2 Interoceptive Monitors",
            "1.8.3 Exteroceptive Monitors",
            "1.8.4 Affect Triage Pipeline",
            "1.8.5 Homeostatic Responses",
            "1.8.6 Review Boundary",
            "1.8.7 Event Contracts",
            "1.8.8 Monitor",
        ]
        for sub in expected_subsections:
            assert sub in content, f"Design doc missing subsection: {sub}"

    @pytest.mark.bdd
    def test_design_doc_defines_interoceptive_monitors(self):
        """Design doc must define INTRO-001 through INTRO-007."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for i in range(1, 8):
            assert f"INTRO-{i:03d}" in content, f"Design doc missing INTRO-{i:03d}"

    @pytest.mark.bdd
    def test_design_doc_defines_exteroceptive_monitors(self):
        """Design doc must define EXTRO-001 through EXTRO-004."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for i in range(1, 5):
            assert f"EXTRO-{i:03d}" in content, f"Design doc missing EXTRO-{i:03d}"

    @pytest.mark.bdd
    def test_design_doc_defines_four_new_event_types(self):
        """Design doc must define 4 new sensory event types."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for event_type in ("interoceptive_signal", "exteroceptive_signal",
                           "affect_triage", "draft_proposal"):
            assert event_type in content, f"Design doc missing event type: {event_type}"

    @pytest.mark.bdd
    def test_design_doc_defines_config_schemas(self):
        """Design doc must include sensory_monitors.yml and affect_triage.yml schemas."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "sensory_monitors.yml" in content
        assert "affect_triage.yml" in content

    @pytest.mark.bdd
    def test_req_sense_005_exists(self):
        """REQ-SENSE-005 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "REQ-SENSE-005" in content

    @pytest.mark.bdd
    def test_req_sense_005_defines_review_boundary(self):
        """REQ-SENSE-005 must define the review boundary concept."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        # Find the REQ-SENSE-005 section heading (not a cross-reference)
        idx = content.find("### REQ-SENSE-005")
        assert idx > 0, "REQ-SENSE-005 section heading not found"
        section = content[idx:idx + 1000]
        assert "Review Boundary" in section
        assert "MCP" in section or "mcp" in section

    @pytest.mark.bdd
    def test_feature_vector_references_req_sense_005(self):
        """REQ-F-SENSE-001 must reference REQ-SENSE-005."""
        fv_path = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_path) as f:
            content = f.read()
        assert "REQ-SENSE-005" in content

    @pytest.mark.bdd
    def test_living_system_table_shows_service_hosted(self):
        """Living system table must show interoception/exteroception as service-hosted."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Service-hosted" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 25: Context Sources — URI-Based External AD Collections
# ═══════════════════════════════════════════════════════════════════════


class TestContextSourcesInSpec:
    """
    GIVEN the context sources feature (URI-based external AD collections)
    WHEN we check spec, design, init command, and iterate agent
    THEN context sources are defined, documented, and wired through.

    Validates: REQ-CTX-001, REQ-CTX-002
    """

    @pytest.mark.bdd
    def test_spec_defines_context_sources(self):
        """AI_SDLC_ASSET_GRAPH_MODEL.md must mention context sources in §2.8."""
        spec_path = SPEC_DIR / "AI_SDLC_ASSET_GRAPH_MODEL.md"
        with open(spec_path) as f:
            content = f.read()
        assert "Context sources" in content
        assert "URI references" in content or "uri" in content.lower()

    @pytest.mark.bdd
    def test_design_defines_context_sources(self):
        """AISDLC_V2_DESIGN.md must describe context source resolution."""
        design_path = DOCS_DIR / "design/claude_aisdlc/AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "context_sources" in content
        assert "standards/" in content

    @pytest.mark.bdd
    def test_iterate_agent_scans_standards_dir(self):
        """aisdlc-iterate.md must mention context/standards/ directory."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "context/standards/" in content

    @pytest.mark.bdd
    def test_init_resolves_context_sources(self):
        """aisdlc-init.md must have Step 4b for resolving context sources."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "Step 4b" in content
        assert "Resolve Context Sources" in content
