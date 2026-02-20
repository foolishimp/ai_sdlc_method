# Validates: REQ-ITER-001, REQ-ITER-002, REQ-EVAL-003, REQ-TOOL-002, REQ-TOOL-007
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
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, load_yaml,
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
