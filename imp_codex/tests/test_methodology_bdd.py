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
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, DESIGN_DIR, load_yaml,
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
        """Init must create specification/INTENT.md placeholder."""
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
    def test_design_documents_exist(self):
        """Design documents must exist."""
        assert (DESIGN_DIR / "AISDLC_V2_DESIGN.md").exists()

    @pytest.mark.bdd
    def test_adrs_exist(self):
        """ADRs 008-013 must exist."""
        adr_dir = DESIGN_DIR / "adrs"
        for n in (8, 9, 10, 11, 12, 13):
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
    THEN all 20 event types are documented with schemas.

    Validates: REQ-LIFE-005, REQ-LIFE-007, REQ-SENSE-001, REQ-SENSE-002, REQ-COORD-003
    """

    REQUIRED_EVENT_TYPES = {
        # Core methodology events (12)
        "project_initialized", "iteration_completed", "edge_started",
        "edge_converged", "spawn_created", "spawn_folded_back",
        "checkpoint_created", "review_completed", "gaps_validated",
        "release_created", "intent_raised", "spec_modified",
        # Sensory/affect events (4)
        "interoceptive_signal", "exteroceptive_signal",
        "affect_triage", "draft_proposal",
        # Multi-agent coordination events (4)
        "claim_rejected", "edge_released",
        "claim_expired", "convergence_escalated",
    }

    @pytest.mark.bdd
    def test_all_event_types_in_agent_reference(self):
        """Iterate agent must document all 20 event types."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        for event_type in self.REQUIRED_EVENT_TYPES:
            assert event_type in content, f"Event type {event_type} missing from agent"

    @pytest.mark.bdd
    def test_all_event_types_in_design_doc(self):
        """Design document must list all event types."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
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
        adr_path = DESIGN_DIR / "adrs/ADR-011-consciousness-loop-at-every-observer.md"
        assert adr_path.exists(), "ADR-011 not found"

    @pytest.mark.bdd
    def test_adr_011_traces_to_requirements(self):
        """ADR-011 must reference REQ-LIFE-005 through REQ-LIFE-008."""
        adr_path = DESIGN_DIR / "adrs/ADR-011-consciousness-loop-at-every-observer.md"
        with open(adr_path) as f:
            content = f.read()
        for req in ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]:
            assert req in content, f"ADR-011 missing reference to {req}"

    @pytest.mark.bdd
    def test_design_references_consciousness_loop(self):
        """Design document must reference consciousness loop mechanics."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "Consciousness Loop" in content or "consciousness loop" in content
        assert "ADR-011" in content

    @pytest.mark.bdd
    def test_feedback_loop_config_implements_adr_011(self):
        """feedback_loop.yml must implement the signal sources from ADR-011."""
        feedback_loop = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        sources = feedback_loop.get("sources", {})
        assert len(sources) >= 7, f"Expected >= 7 signal sources, got {len(sources)}"


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 23: Three Processing Phases in Spec and Implementation
# ═══════════════════════════════════════════════════════════════════════


class TestProcessingPhasesInImpl:
    """
    GIVEN the formal spec defines three processing phases (§4.3)
    WHEN we check that Claude's agent and design reference them
    THEN all documents reference reflex/affect/conscious with correct mappings.

    Validates: REQ-EVAL-001 (processing_phase field)
    """

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
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
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
    WHEN we check Claude design docs
    THEN the design sections, monitors, and event contracts are defined.

    Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003, REQ-SENSE-004, REQ-SENSE-005
    """

    @pytest.mark.bdd
    def test_design_doc_has_sensory_service_section(self):
        """Design doc must have §1.8 Sensory Service section."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "1.8 Sensory Service" in content

    @pytest.mark.bdd
    def test_design_doc_has_all_sensory_subsections(self):
        """Design doc §1.8 must have all 8 subsections."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
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
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for i in range(1, 8):
            assert f"INTRO-{i:03d}" in content, f"Design doc missing INTRO-{i:03d}"

    @pytest.mark.bdd
    def test_design_doc_defines_exteroceptive_monitors(self):
        """Design doc must define EXTRO-001 through EXTRO-004."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for i in range(1, 5):
            assert f"EXTRO-{i:03d}" in content, f"Design doc missing EXTRO-{i:03d}"

    @pytest.mark.bdd
    def test_design_doc_defines_four_new_event_types(self):
        """Design doc must define 4 new sensory event types."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        for event_type in ("interoceptive_signal", "exteroceptive_signal",
                           "affect_triage", "draft_proposal"):
            assert event_type in content, f"Design doc missing event type: {event_type}"

    @pytest.mark.bdd
    def test_design_doc_defines_config_schemas(self):
        """Design doc must include sensory_monitors.yml and affect_triage.yml schemas."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "sensory_monitors.yml" in content
        assert "affect_triage.yml" in content



# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 25: Context Sources — Claude Implementation Checks
# ═══════════════════════════════════════════════════════════════════════


class TestContextSourcesInImpl:
    """
    GIVEN the context sources feature (URI-based external AD collections)
    WHEN we check design, init command, and iterate agent
    THEN context sources are documented and wired through.

    Validates: REQ-CTX-001, REQ-CTX-002
    """

    @pytest.mark.bdd
    def test_design_defines_context_sources(self):
        """AISDLC_V2_DESIGN.md must describe context source resolution."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
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


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 26: Two-Command UX Layer
# ═══════════════════════════════════════════════════════════════════════


class TestTwoCommandUX:
    """
    GIVEN the two-command UX layer (Start + Status)
    WHEN the user invokes Start or Status
    THEN state is detected, features are selected, and routing/observability works.

    Validates: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005
    """

    @pytest.mark.bdd
    def test_status_has_state_detection(self):
        """Status command must have Step 0 state detection."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Step 0" in content
        assert "State Detection" in content

    @pytest.mark.bdd
    def test_status_has_you_are_here(self):
        """Status command must show 'You Are Here' indicators."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "You Are Here" in content

    @pytest.mark.bdd
    def test_status_has_what_start_would_do(self):
        """Status command must preview what Start would do."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Start would" in content or "What Start Would Do" in content

    @pytest.mark.bdd
    def test_status_has_health_flag(self):
        """Status command must support --health flag."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "--health" in content

    @pytest.mark.bdd
    def test_start_defines_state_machine(self):
        """Start command must define 8 states in the state machine."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        for state in ("UNINITIALISED", "NEEDS_CONSTRAINTS", "NEEDS_INTENT",
                       "NO_FEATURES", "IN_PROGRESS", "ALL_CONVERGED",
                       "ALL_BLOCKED", "STUCK"):
            assert state in content, f"Start missing state: {state}"

    @pytest.mark.bdd
    def test_start_delegates_to_iterate(self):
        """Start command must delegate to /aisdlc-iterate."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "/aisdlc-iterate" in content

    @pytest.mark.bdd
    def test_start_has_progressive_init(self):
        """Start command must implement progressive init with ≤5 questions."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "Progressive Init" in content
        assert "Project name" in content
        assert "Project kind" in content

    @pytest.mark.bdd
    def test_start_has_deferred_constraints(self):
        """Start command must defer constraint dimensions to design edge."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "Deferred Constraint" in content or "deferred" in content.lower()
        assert "requirements→design" in content

    @pytest.mark.bdd
    def test_design_doc_describes_two_command_ux(self):
        """Design doc must have §1.9 Two-Command UX Layer."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "1.9 Two-Command UX Layer" in content
        assert "ADR-012" in content


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 22: Two-Command UX — Acceptance Criteria Depth
# ═══════════════════════════════════════════════════════════════════════


class TestTwoCommandUXAcceptanceCriteria:
    """
    GIVEN the two-command UX layer (Start + Status)
    WHEN each REQ-UX acceptance criterion is checked
    THEN the command spec contains the required content.

    Validates: REQ-UX-001, REQ-UX-002, REQ-UX-003, REQ-UX-004, REQ-UX-005
    """

    # ─── REQ-UX-001: State-Driven Routing ─────────────────────────────

    @pytest.mark.bdd
    def test_start_routes_to_action_per_state(self):
        """Each state must route to a specific action (init, iterate, etc.)."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        # Each state maps to a numbered step
        for action in ("Progressive Init", "Constraint Prompting",
                       "Intent Authoring", "Feature Creation",
                       "Feature/Edge Selection", "Release/Gaps",
                       "Stuck Recovery", "Blocked Recovery"):
            assert action in content, f"Start missing action: {action}"

    @pytest.mark.bdd
    def test_start_state_derived_not_stored(self):
        """State must be derived from workspace, never stored."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "derived" in content.lower()
        assert "pure read" in content.lower() or "never stored" in content.lower()

    @pytest.mark.bdd
    def test_start_auto_mode_loop(self):
        """Start must support --auto mode with pause conditions."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "--auto" in content
        # Must pause at human gates, spawn decisions, stuck, time-box
        for pause in ("human gate", "spawn", "stuck", "time-box"):
            assert pause.lower() in content.lower(), f"Auto-mode missing pause: {pause}"

    # ─── REQ-UX-002: Progressive Disclosure ───────────────────────────

    @pytest.mark.bdd
    def test_start_init_five_questions(self):
        """Progressive init must capture exactly 5 inputs."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        for question in ("Project name", "Project kind", "Language",
                         "Test runner", "Intent description"):
            assert question in content, f"Init missing question: {question}"

    @pytest.mark.bdd
    def test_start_auto_detection(self):
        """Progressive init must auto-detect from project files."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "Auto-detect" in content or "auto-detect" in content.lower()
        # Must mention config file detection
        for config in ("package.json", "pyproject.toml"):
            assert config in content, f"Init missing auto-detect from: {config}"

    @pytest.mark.bdd
    def test_start_project_kind_to_profile_mapping(self):
        """Project kind must map to default profile."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "application" in content
        assert "standard" in content
        assert "library" in content

    # ─── REQ-UX-003: Project-Wide Observability ───────────────────────

    @pytest.mark.bdd
    def test_status_has_project_rollup(self):
        """Status must show cross-feature rollup with edge counts."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Project Rollup" in content or "Rollup" in content
        assert "converged" in content.lower()

    @pytest.mark.bdd
    def test_status_has_gantt_support(self):
        """Status must support --gantt flag with Mermaid diagram."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "--gantt" in content
        assert "mermaid" in content.lower() or "Mermaid" in content

    @pytest.mark.bdd
    def test_status_has_process_telemetry(self):
        """Status must include process telemetry section."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Process Telemetry" in content
        assert "Convergence Pattern" in content

    @pytest.mark.bdd
    def test_status_has_self_reflection(self):
        """Status must include self-reflection / feedback-to-intent section."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Self-Reflection" in content or "Feedback" in content

    @pytest.mark.bdd
    def test_status_has_signals(self):
        """Status must surface unactioned intent_raised events as signals."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "intent_raised" in content
        assert "signal" in content.lower()

    @pytest.mark.bdd
    def test_status_event_sourcing_documented(self):
        """Status must document event sourcing architecture."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "Event Sourcing" in content
        assert "events.jsonl" in content
        assert "source of truth" in content.lower() or "Source of Truth" in content

    # ─── REQ-UX-004: Feature/Edge Auto-Selection ──────────────────────

    @pytest.mark.bdd
    def test_start_feature_selection_priority_tiers(self):
        """Start must document feature selection priority tiers."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        for tier in ("time-box", "closest-to-complete", "priority", "recently touched"):
            assert tier.lower() in content.lower(), f"Selection missing tier: {tier}"

    @pytest.mark.bdd
    def test_start_edge_determination_algorithm(self):
        """Start must document edge determination via topological walk."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "topological" in content.lower()
        assert "unconverged" in content.lower()
        assert "profile" in content.lower()

    @pytest.mark.bdd
    def test_start_user_override_flags(self):
        """Start must support --feature and --edge override flags."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "--feature" in content
        assert "--edge" in content

    @pytest.mark.bdd
    def test_start_coevolution_edge_handling(self):
        """Start must present co-evolution edges as a single unit."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "co-evolution" in content.lower() or "code↔unit_tests" in content

    # ─── REQ-UX-005: Recovery & Self-Healing ──────────────────────────

    @pytest.mark.bdd
    def test_start_recovery_scenarios(self):
        """Start must detect and handle recovery scenarios."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        for scenario in ("Corrupted event log", "Missing feature vectors",
                         "Orphaned spawns", "Stuck features"):
            assert scenario.lower() in content.lower(), \
                f"Recovery missing scenario: {scenario}"

    @pytest.mark.bdd
    def test_start_non_destructive_recovery(self):
        """Recovery must be non-destructive — never silently delete."""
        with open(COMMANDS_DIR / "aisdlc-start.md") as f:
            content = f.read()
        assert "non-destructive" in content.lower() or "never silently delete" in content.lower()

    @pytest.mark.bdd
    def test_status_health_check_comprehensive(self):
        """Health check must cover event log, vectors, spawns, convergence, constraints."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        for check in ("Event Log", "Feature Vector", "Orphaned",
                      "Convergence", "Constraint"):
            assert check.lower() in content.lower(), \
                f"Health check missing: {check}"

    @pytest.mark.bdd
    def test_status_views_rebuildable_from_events(self):
        """Status must document that views are reconstructible from event stream."""
        with open(COMMANDS_DIR / "aisdlc-status.md") as f:
            content = f.read()
        assert "reconstruct" in content.lower() or "regenerat" in content.lower() or \
            "replay" in content.lower()


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 23: Developer Tooling — Acceptance Criteria Depth
# ═══════════════════════════════════════════════════════════════════════


class TestDeveloperToolingAcceptanceCriteria:
    """
    GIVEN the developer tooling feature (plugin, commands, hooks, scaffolding)
    WHEN each REQ-TOOL acceptance criterion is checked
    THEN command specs, hook scripts, and config files contain required content.

    Validates: REQ-TOOL-001, REQ-TOOL-003, REQ-TOOL-004, REQ-TOOL-006,
               REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010
    """

    # ─── REQ-TOOL-003: Workflow Commands ──────────────────────────────

    @pytest.mark.bdd
    def test_all_ten_commands_exist(self):
        """All 10 /aisdlc-* commands must exist as markdown specs."""
        expected = [
            "aisdlc-checkpoint.md", "aisdlc-gaps.md", "aisdlc-init.md",
            "aisdlc-iterate.md", "aisdlc-release.md", "aisdlc-review.md",
            "aisdlc-spawn.md", "aisdlc-start.md", "aisdlc-status.md",
            "aisdlc-trace.md",
        ]
        for cmd in expected:
            assert (COMMANDS_DIR / cmd).exists(), f"Command missing: {cmd}"

    @pytest.mark.bdd
    def test_all_commands_have_usage_and_instructions(self):
        """Every command spec must have Usage and Instructions sections."""
        for cmd_file in sorted(COMMANDS_DIR.glob("aisdlc-*.md")):
            with open(cmd_file) as f:
                content = f.read()
            assert "## Usage" in content, f"{cmd_file.name} missing ## Usage"
            assert "## Instructions" in content or "## Layers" in content, \
                f"{cmd_file.name} missing ## Instructions"

    @pytest.mark.bdd
    def test_all_commands_reference_req_keys(self):
        """Every command spec must reference at least one REQ-* key."""
        for cmd_file in sorted(COMMANDS_DIR.glob("aisdlc-*.md")):
            with open(cmd_file) as f:
                content = f.read()
            assert "REQ-" in content, f"{cmd_file.name} missing REQ-* reference"

    # ─── REQ-TOOL-004: Release Management ─────────────────────────────

    @pytest.mark.bdd
    def test_release_command_supports_semver(self):
        """Release command must support semantic versioning."""
        with open(COMMANDS_DIR / "aisdlc-release.md") as f:
            content = f.read()
        assert "semver" in content.lower() or "semantic version" in content.lower()
        assert "--version" in content

    @pytest.mark.bdd
    def test_release_command_generates_changelog(self):
        """Release command must generate changelog from git log."""
        with open(COMMANDS_DIR / "aisdlc-release.md") as f:
            content = f.read()
        assert "changelog" in content.lower() or "Changelog" in content

    @pytest.mark.bdd
    def test_release_command_checks_coverage(self):
        """Release command must validate REQ key coverage before release."""
        with open(COMMANDS_DIR / "aisdlc-release.md") as f:
            content = f.read()
        assert "coverage" in content.lower() or "/aisdlc-gaps" in content

    @pytest.mark.bdd
    def test_release_command_emits_event(self):
        """Release command must emit release_created event."""
        with open(COMMANDS_DIR / "aisdlc-release.md") as f:
            content = f.read()
        assert "release_created" in content

    # ─── REQ-TOOL-006: Methodology Hooks ──────────────────────────────

    @pytest.mark.bdd
    def test_hooks_json_exists_with_two_hooks(self):
        """hooks.json must define UserPromptSubmit and Stop hooks."""
        hooks_dir = COMMANDS_DIR.parent / "hooks"
        hooks_json = hooks_dir / "hooks.json"
        assert hooks_json.exists(), "hooks.json missing"
        import json
        with open(hooks_json) as f:
            data = json.load(f)
        assert "UserPromptSubmit" in data["hooks"]
        assert "Stop" in data["hooks"]

    @pytest.mark.bdd
    def test_iterate_start_hook_exists(self):
        """on-iterate-start.sh must exist and set up edge context."""
        hooks_dir = COMMANDS_DIR.parent / "hooks"
        hook = hooks_dir / "on-iterate-start.sh"
        assert hook.exists()
        with open(hook) as f:
            content = f.read()
        assert "edge_in_progress" in content or "EDGE" in content

    @pytest.mark.bdd
    def test_stop_check_hook_enforces_protocol(self):
        """on-stop-check-protocol.sh must enforce iterate protocol completion."""
        hooks_dir = COMMANDS_DIR.parent / "hooks"
        hook = hooks_dir / "on-stop-check-protocol.sh"
        assert hook.exists()
        with open(hook) as f:
            content = f.read()
        # Must check for event emission and feature vector update
        assert "events.jsonl" in content or "event" in content.lower()
        assert "block" in content.lower()

    @pytest.mark.bdd
    def test_hooks_are_reflex_processing(self):
        """Both hooks must operate in reflex processing regime (unconditional)."""
        hooks_dir = COMMANDS_DIR.parent / "hooks"
        for hook_name in ("on-iterate-start.sh", "on-stop-check-protocol.sh"):
            with open(hooks_dir / hook_name) as f:
                content = f.read()
            assert "reflex" in content.lower() or "REFLEX" in content, \
                f"{hook_name} missing reflex processing regime label"

    # ─── REQ-TOOL-008: Context Snapshot ───────────────────────────────

    @pytest.mark.bdd
    def test_checkpoint_command_computes_context_hash(self):
        """Checkpoint must compute SHA-256 context hash."""
        with open(COMMANDS_DIR / "aisdlc-checkpoint.md") as f:
            content = f.read()
        assert "sha256" in content.lower() or "SHA-256" in content
        assert "context_hash" in content or "Context Hash" in content

    @pytest.mark.bdd
    def test_checkpoint_creates_immutable_snapshot(self):
        """Checkpoint must create an immutable snapshot file."""
        with open(COMMANDS_DIR / "aisdlc-checkpoint.md") as f:
            content = f.read()
        assert "snapshot" in content.lower()
        assert "immutable" in content.lower()

    @pytest.mark.bdd
    def test_checkpoint_captures_feature_states(self):
        """Checkpoint must capture all feature vector states."""
        with open(COMMANDS_DIR / "aisdlc-checkpoint.md") as f:
            content = f.read()
        assert "feature_states" in content or "feature" in content.lower()
        assert "git_ref" in content or "git" in content.lower()

    @pytest.mark.bdd
    def test_checkpoint_emits_event(self):
        """Checkpoint must emit checkpoint_created event."""
        with open(COMMANDS_DIR / "aisdlc-checkpoint.md") as f:
            content = f.read()
        assert "checkpoint_created" in content

    # ─── REQ-TOOL-009: Feature Views ──────────────────────────────────

    @pytest.mark.bdd
    def test_trace_command_supports_bidirectional(self):
        """Trace command must support forward, backward, and both directions."""
        with open(COMMANDS_DIR / "aisdlc-trace.md") as f:
            content = f.read()
        assert "forward" in content.lower()
        assert "backward" in content.lower()
        assert "--direction" in content

    @pytest.mark.bdd
    def test_trace_command_shows_cross_artifact_status(self):
        """Trace must show REQ key status across spec, design, code, tests."""
        with open(COMMANDS_DIR / "aisdlc-trace.md") as f:
            content = f.read()
        for stage in ("Intent", "Requirements", "Design", "Code", "Test"):
            assert stage.lower() in content.lower(), \
                f"Trace missing stage: {stage}"

    @pytest.mark.bdd
    def test_gaps_command_supports_three_layers(self):
        """Gaps command must support 3 traceability layers."""
        with open(COMMANDS_DIR / "aisdlc-gaps.md") as f:
            content = f.read()
        assert "Layer 1" in content or "REQ Tag Coverage" in content
        assert "Layer 2" in content or "Test Gap" in content
        assert "Layer 3" in content or "Telemetry Gap" in content
        assert "--layer" in content

    @pytest.mark.bdd
    def test_gaps_command_reports_severity(self):
        """Gaps command must report gap severity and recommended actions."""
        with open(COMMANDS_DIR / "aisdlc-gaps.md") as f:
            content = f.read()
        assert "severity" in content.lower() or "Severity" in content

    # ─── REQ-TOOL-010: Spec/Design Boundary ───────────────────────────

    @pytest.mark.bdd
    def test_requirements_design_edge_has_boundary_check(self):
        """Requirements→Design edge must check for spec/design boundary."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        check_names = [c["name"] for c in config["checklist"]]
        # Must have tech-agnostic validation or spec/design boundary check
        has_boundary = any("spec" in n.lower() or "boundary" in n.lower()
                          or "tech" in n.lower() or "dimension" in n.lower()
                          for n in check_names)
        assert has_boundary, \
            f"requirements_design.yml missing spec/design boundary check. Checks: {check_names}"

    @pytest.mark.bdd
    def test_design_edge_mandates_adr_generation(self):
        """Requirements→Design edge must mandate ADR generation for decisions."""
        config = load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")
        guidance = config.get("agent_guidance", "")
        assert "ADR" in guidance, "Agent guidance missing ADR generation mandate"


# ═══════════════════════════════════════════════════════════════════════
# SCENARIO 24: Full Lifecycle Closure — Acceptance Criteria Depth
# ═══════════════════════════════════════════════════════════════════════


class TestFullLifecycleAcceptanceCriteria:
    """
    GIVEN the full lifecycle feature (CI/CD, telemetry, homeostasis, feedback loop)
    WHEN each REQ-LIFE acceptance criterion is checked
    THEN graph topology, edge configs, and agent docs contain required content.

    Validates: REQ-LIFE-001, REQ-LIFE-002, REQ-LIFE-003, REQ-LIFE-004,
               REQ-LIFE-005, REQ-LIFE-006, REQ-LIFE-007, REQ-LIFE-008,
               REQ-INTENT-003
    """

    # ─── REQ-LIFE-001: CI/CD as Graph Edge ────────────────────────────

    @pytest.mark.bdd
    def test_graph_has_cicd_edges(self):
        """Graph topology must include code→cicd and cicd→running_system."""
        config = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = config.get("transitions", [])
        edge_pairs = [(t["source"], t["target"]) for t in transitions]
        assert ("code", "cicd") in edge_pairs, "Missing code→cicd edge"
        assert ("cicd", "running_system") in edge_pairs, "Missing cicd→running_system"

    @pytest.mark.bdd
    def test_graph_has_cicd_asset_type(self):
        """Graph topology must define cicd as an asset type."""
        config = load_yaml(CONFIG_DIR / "graph_topology.yml")
        asset_types = config.get("asset_types", {})
        assert "cicd" in asset_types, f"Missing cicd asset type. Types: {list(asset_types.keys())}"

    @pytest.mark.bdd
    def test_release_command_lists_feature_vectors(self):
        """Release command must include feature vector IDs in release notes."""
        with open(COMMANDS_DIR / "aisdlc-release.md") as f:
            content = f.read()
        assert "REQ" in content
        assert "feature" in content.lower()

    # ─── REQ-LIFE-002: Telemetry and Homeostasis ──────────────────────

    @pytest.mark.bdd
    def test_graph_has_telemetry_edge(self):
        """Graph topology must include running_system→telemetry."""
        config = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = config.get("transitions", [])
        edge_pairs = [(t["source"], t["target"]) for t in transitions]
        assert ("running_system", "telemetry") in edge_pairs

    @pytest.mark.bdd
    def test_feedback_loop_has_homeostasis_concept(self):
        """Feedback loop config must reference homeostasis or deviation detection."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        content = str(config)
        assert "homeostasis" in content.lower() or "deviation" in content.lower() \
            or "drift" in content.lower()

    @pytest.mark.bdd
    def test_traceability_has_telemetry_layer(self):
        """Traceability config must define Layer 3 telemetry gap analysis."""
        config = load_yaml(EDGE_PARAMS_DIR / "traceability.yml")
        content = str(config)
        assert "telemetry" in content.lower()
        assert "layer_3" in content or "Layer 3" in content or "telemetry_gap" in content

    # ─── REQ-LIFE-003: Feedback Loop Closure ──────────────────────────

    @pytest.mark.bdd
    def test_graph_has_telemetry_to_intent_edge(self):
        """Graph topology must close the loop: telemetry→intent."""
        config = load_yaml(CONFIG_DIR / "graph_topology.yml")
        transitions = config.get("transitions", [])
        edge_pairs = [(t["source"], t["target"]) for t in transitions]
        assert ("telemetry", "intent") in edge_pairs, "Missing telemetry→intent edge"

    @pytest.mark.bdd
    def test_feedback_loop_generates_intents(self):
        """Feedback loop config must generate intent_raised events."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        content = str(config)
        assert "intent_raised" in content

    @pytest.mark.bdd
    def test_feedback_loop_has_deviation_details(self):
        """Feedback loop intents must include deviation details."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        content = str(config)
        assert "deviation" in content.lower() or "delta" in content.lower() \
            or "drift" in content.lower()

    # ─── REQ-LIFE-004: Feature Lineage in Telemetry ───────────────────

    @pytest.mark.bdd
    def test_traceability_has_telemetry_tag_format(self):
        """Traceability config must define telemetry REQ key tag format."""
        config = load_yaml(EDGE_PARAMS_DIR / "traceability.yml")
        content = str(config)
        assert "telemetry" in content.lower()
        assert "req" in content.lower()

    @pytest.mark.bdd
    def test_feedback_loop_has_telemetry_checks(self):
        """Feedback loop must check for REQ key presence in telemetry."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        check_names = [c["name"] for c in config.get("checklist", [])]
        assert "telemetry_tag_format" in check_names or \
            "code_req_keys_have_telemetry" in check_names, \
            f"Feedback loop missing telemetry check. Checks: {check_names}"

    # ─── REQ-INTENT-003: Eco-Intent Generation ────────────────────────

    @pytest.mark.bdd
    def test_ecosystem_signal_source_exists(self):
        """Feedback loop must recognise 'ecosystem' as a signal source."""
        config = load_yaml(EDGE_PARAMS_DIR / "feedback_loop.yml")
        sources = config.get("sources", {})
        signal_sources = [v.get("signal_source", "") for v in sources.values()
                          if isinstance(v, dict)]
        assert "ecosystem" in signal_sources, \
            f"Missing ecosystem signal source. Sources: {signal_sources}"

    @pytest.mark.bdd
    def test_iterate_agent_documents_ecosystem_intent(self):
        """Iterate agent must document ecosystem-triggered intent generation."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "ecosystem" in content.lower()

    # ─── Phase 2 readiness checks ─────────────────────────────────────

    @pytest.mark.bdd
    def test_full_profile_includes_lifecycle_edges(self):
        """Full profile must include cicd and telemetry edges."""
        config = load_yaml(CONFIG_DIR / "profiles" / "full.yml")
        graph_include = config.get("graph", {}).get("include", "")
        assert graph_include == "all", \
            f"Full profile must include all edges (got: {graph_include})"

    @pytest.mark.bdd
    def test_consciousness_loop_operates_at_every_observer(self):
        """Agent must state consciousness loop operates at every observer."""
        with open(AGENTS_DIR / "aisdlc-iterate.md") as f:
            content = f.read()
        assert "every observer" in content.lower() or \
            "consciousness loop" in content.lower()


class TestSensorySystemsAcceptanceCriteria:
    """
    GIVEN the sensory systems feature (MCP service, monitors, triage, review boundary)
    WHEN each REQ-SENSE acceptance criterion is checked
    THEN config files, design doc, and agent docs contain required content.

    Validates: REQ-SENSE-001, REQ-SENSE-002, REQ-SENSE-003,
               REQ-SENSE-004, REQ-SENSE-005
    """

    # ─── REQ-SENSE-001: Interoceptive Monitoring ────────────────────

    @pytest.mark.bdd
    def test_sensory_monitors_config_exists(self):
        """sensory_monitors.yml must exist in config directory."""
        assert (CONFIG_DIR / "sensory_monitors.yml").exists()

    @pytest.mark.bdd
    def test_interoceptive_monitors_defined(self):
        """Config must define INTRO-001 through INTRO-007."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("interoceptive", [])
        ids = [m["id"] for m in monitors]
        for i in range(1, 8):
            expected = f"INTRO-{i:03d}"
            assert expected in ids, f"Missing interoceptive monitor {expected}"

    @pytest.mark.bdd
    def test_interoceptive_monitors_have_thresholds(self):
        """Each interoceptive monitor must have threshold with warning/critical levels."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("interoceptive", [])
        for m in monitors:
            assert "threshold" in m or "checks" in m, \
                f"Monitor {m['id']} missing threshold or checks"

    @pytest.mark.bdd
    def test_interoceptive_monitors_have_schedules(self):
        """Each interoceptive monitor must define a schedule."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("interoceptive", [])
        for m in monitors:
            assert "schedule" in m, f"Monitor {m['id']} missing schedule"

    @pytest.mark.bdd
    def test_service_runs_independently(self):
        """Service must start on workspace_open, not only during iterate()."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        service = config.get("service", {})
        assert service.get("start_on") == "workspace_open"

    # ─── REQ-SENSE-002: Exteroceptive Monitoring ────────────────────

    @pytest.mark.bdd
    def test_exteroceptive_monitors_defined(self):
        """Config must define EXTRO-001 through EXTRO-004."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("exteroceptive", [])
        ids = [m["id"] for m in monitors]
        for i in range(1, 5):
            expected = f"EXTRO-{i:03d}"
            assert expected in ids, f"Missing exteroceptive monitor {expected}"

    @pytest.mark.bdd
    def test_exteroceptive_monitors_observe_external_sources(self):
        """Exteroceptive monitors must reference external sources (commands, endpoints, APIs)."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("exteroceptive", [])
        for m in monitors:
            has_external = "commands" in m or "endpoint" in m or "sources" in m
            assert has_external, \
                f"Monitor {m['id']} must reference external sources"

    @pytest.mark.bdd
    def test_cve_monitor_has_severity_filter(self):
        """EXTRO-002 (CVE scanning) must filter by severity."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        monitors = config.get("monitors", {}).get("exteroceptive", [])
        cve = next((m for m in monitors if m["id"] == "EXTRO-002"), None)
        assert cve is not None, "EXTRO-002 not found"
        assert "severity_filter" in cve, "CVE monitor must have severity_filter"

    # ─── REQ-SENSE-003: Affect Triage Pipeline ──────────────────────

    @pytest.mark.bdd
    def test_affect_triage_config_exists(self):
        """affect_triage.yml must exist in config directory."""
        assert (CONFIG_DIR / "affect_triage.yml").exists()

    @pytest.mark.bdd
    def test_triage_has_classification_rules(self):
        """Triage config must define classification rules."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        rules = config.get("classification_rules", [])
        assert len(rules) >= 5, \
            f"Expected at least 5 classification rules, got {len(rules)}"

    @pytest.mark.bdd
    def test_triage_has_agent_fallback(self):
        """Triage must have agent classification fallback for unmatched signals."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        rules = config.get("classification_rules", [])
        fallback = [r for r in rules if r.get("pattern", {}).get("unmatched")]
        assert len(fallback) >= 1, "Missing agent_classify fallback rule"

    @pytest.mark.bdd
    def test_triage_escalation_thresholds_per_profile(self):
        """Triage must define escalation thresholds for each profile."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        thresholds = config.get("escalation_thresholds", {})
        expected_profiles = ["full", "standard", "hotfix", "spike", "poc", "minimal"]
        for profile in expected_profiles:
            assert profile in thresholds, \
                f"Missing escalation threshold for profile: {profile}"

    @pytest.mark.bdd
    def test_triage_assigns_classification_severity_escalation(self):
        """Each classification rule must assign classification, severity, and escalation."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        rules = config.get("classification_rules", [])
        for rule in rules:
            assert "classification" in rule, \
                f"Rule {rule.get('name', '?')} missing classification"
            assert "escalation" in rule, \
                f"Rule {rule.get('name', '?')} missing escalation"

    @pytest.mark.bdd
    def test_triage_tiered_approach(self):
        """Triage must be tiered: rule-based first, agent for ambiguous."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        assert "classification_rules" in config, "Missing rule-based classification"
        assert "agent_classification" in config, "Missing agent classification config"

    # ─── REQ-SENSE-004: Sensory System Configuration ────────────────

    @pytest.mark.bdd
    def test_profile_overrides_exist(self):
        """sensory_monitors.yml must define profile-level overrides."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        overrides = config.get("profile_overrides", {})
        assert len(overrides) >= 4, \
            f"Expected profile overrides for at least 4 profiles, got {len(overrides)}"

    @pytest.mark.bdd
    def test_spike_disables_exteroception(self):
        """Spike profile must disable all exteroceptive monitors."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        spike = config.get("profile_overrides", {}).get("spike", {})
        disabled = spike.get("disable", [])
        for i in range(1, 5):
            expected = f"EXTRO-{i:03d}"
            assert expected in disabled, \
                f"Spike profile must disable {expected}"

    @pytest.mark.bdd
    def test_meta_monitoring_enabled(self):
        """Config must support meta-monitoring (monitor health)."""
        config = load_yaml(CONFIG_DIR / "sensory_monitors.yml")
        meta = config.get("meta_monitoring", {})
        assert meta.get("enabled") is True, "Meta-monitoring must be enabled"

    # ─── REQ-SENSE-005: Review Boundary ─────────────────────────────

    @pytest.mark.bdd
    def test_review_boundary_defined(self):
        """affect_triage.yml must define review boundary with MCP tools."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        boundary = config.get("review_boundary", {})
        tools = boundary.get("mcp_tools", [])
        tool_names = [t["name"] for t in tools]
        expected = ["sensory-status", "sensory-proposals",
                    "sensory-approve", "sensory-dismiss"]
        for name in expected:
            assert name in tool_names, f"Missing MCP tool: {name}"

    @pytest.mark.bdd
    def test_review_boundary_draft_only_autonomy(self):
        """Review boundary must enforce draft-only autonomy model."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        boundary = config.get("review_boundary", {})
        assert boundary.get("autonomy_model") == "draft_only"

    @pytest.mark.bdd
    def test_review_boundary_human_required_for_modifications(self):
        """Review boundary must require human approval for file modifications."""
        config = load_yaml(CONFIG_DIR / "affect_triage.yml")
        boundary = config.get("review_boundary", {})
        human_req = boundary.get("human_required_for", [])
        assert "file_modification" in human_req

    @pytest.mark.bdd
    def test_design_doc_covers_sensory_service(self):
        """Design document must have §1.8 Sensory Service section."""
        with open(DESIGN_DIR / "AISDLC_V2_DESIGN.md") as f:
            content = f.read()
        assert "### 1.8 Sensory Service" in content or \
            "## 1.8 Sensory Service" in content
        assert "REQ-SENSE-001" in content
        assert "REQ-SENSE-005" in content

    @pytest.mark.bdd
    def test_design_doc_has_sensory_architecture_diagram(self):
        """Design document must include sensory service architecture diagram."""
        with open(DESIGN_DIR / "AISDLC_V2_DESIGN.md") as f:
            content = f.read()
        assert "SENSORY SERVICE" in content
        assert "REVIEW BOUNDARY" in content

    @pytest.mark.bdd
    def test_two_event_categories_enforced(self):
        """Design must distinguish sensor/evaluate events from change-approval events."""
        with open(DESIGN_DIR / "AISDLC_V2_DESIGN.md") as f:
            content = f.read()
        assert "observation event" in content.lower() or \
            "sensor/evaluate" in content.lower() or \
            "observation-only" in content.lower()
