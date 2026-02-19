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
            "tasks/", "intents/", "snapshots/",
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
