# Validates: REQ-GRAPH-001, REQ-GRAPH-002, REQ-GRAPH-003
# Validates: REQ-EVAL-001, REQ-EVAL-002
# Validates: REQ-TOOL-001
"""TDD unit tests — deterministic validation of YAML configs and cross-references."""

import json
import pathlib
import re

import pytest
import yaml

from conftest import (
    CONFIG_DIR, EDGE_PARAMS_DIR, PROFILES_DIR, COMMANDS_DIR,
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, load_yaml,
)

# ═══════════════════════════════════════════════════════════════════════
# 1. YAML SYNTAX VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestYamlSyntax:
    """Every YAML file in config/ must parse without errors."""

    @pytest.mark.tdd
    @pytest.mark.parametrize("yml_path", sorted(CONFIG_DIR.rglob("*.yml")))
    def test_yaml_parses(self, yml_path):
        """YAML file must be syntactically valid."""
        with open(yml_path) as f:
            docs = list(yaml.safe_load_all(f))
        non_none = [d for d in docs if d is not None]
        assert len(non_none) > 0, f"{yml_path.name} parsed to empty"

    @pytest.mark.tdd
    def test_plugin_json_parses(self):
        """plugin.json must be valid JSON."""
        with open(PLUGIN_ROOT / "plugin.json") as f:
            data = json.load(f)
        assert "name" in data
        assert "commands" in data


# ═══════════════════════════════════════════════════════════════════════
# 2. GRAPH TOPOLOGY VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestGraphTopology:
    """Graph topology must define asset types and valid transitions."""

    @pytest.mark.tdd
    def test_has_asset_types(self, graph_topology):
        assert "asset_types" in graph_topology
        assert len(graph_topology["asset_types"]) >= 10

    @pytest.mark.tdd
    def test_has_transitions(self, graph_topology):
        assert "transitions" in graph_topology
        assert len(graph_topology["transitions"]) >= 10

    @pytest.mark.tdd
    def test_asset_types_have_required_fields(self, graph_topology):
        """Each asset type needs description, schema, markov_criteria."""
        for name, asset in graph_topology["asset_types"].items():
            assert "description" in asset, f"asset_type '{name}' missing description"
            assert "schema" in asset, f"asset_type '{name}' missing schema"
            assert "markov_criteria" in asset, f"asset_type '{name}' missing markov_criteria"
            assert len(asset["markov_criteria"]) > 0, f"asset_type '{name}' has empty markov_criteria"

    @pytest.mark.tdd
    def test_transitions_reference_valid_asset_types(self, graph_topology):
        """Every transition source/target must be a defined asset type."""
        valid_types = set(graph_topology["asset_types"].keys())
        for t in graph_topology["transitions"]:
            assert t["source"] in valid_types, f"transition '{t['name']}' source '{t['source']}' not in asset_types"
            assert t["target"] in valid_types, f"transition '{t['name']}' target '{t['target']}' not in asset_types"

    @pytest.mark.tdd
    def test_transitions_have_required_fields(self, graph_topology):
        """Each transition needs name, source, target, edge_type, evaluators, constructor."""
        for t in graph_topology["transitions"]:
            assert "name" in t, f"transition missing name: {t}"
            assert "source" in t
            assert "target" in t
            assert "edge_type" in t
            assert t["edge_type"] in ("standard", "co_evolution"), \
                f"transition '{t['name']}' edge_type must be standard or co_evolution"
            assert "evaluators" in t
            assert "constructor" in t

    @pytest.mark.tdd
    def test_transitions_evaluators_valid(self, graph_topology):
        """Evaluators must be from {human, agent, deterministic}."""
        valid_evaluators = {"human", "agent", "deterministic"}
        for t in graph_topology["transitions"]:
            for e in t["evaluators"]:
                assert e in valid_evaluators, \
                    f"transition '{t['name']}' has invalid evaluator '{e}'"

    @pytest.mark.tdd
    def test_graph_is_cyclic(self, graph_topology):
        """The graph must contain at least one cycle (feedback loop)."""
        assert graph_topology["graph_properties"]["cyclic"] is True

    @pytest.mark.tdd
    def test_bootstrap_graph_edges_present(self, graph_topology):
        """The bootstrap graph edges must all be present."""
        expected_edges = [
            ("intent", "requirements"),
            ("requirements", "design"),
            ("design", "code"),
            ("code", "unit_tests"),
            ("design", "test_cases"),
            ("design", "uat_tests"),
            ("code", "cicd"),
            ("cicd", "running_system"),
            ("running_system", "telemetry"),
            ("telemetry", "intent"),
        ]
        actual_edges = {(t["source"], t["target"]) for t in graph_topology["transitions"]}
        for src, tgt in expected_edges:
            assert (src, tgt) in actual_edges, f"missing edge: {src} → {tgt}"


# ═══════════════════════════════════════════════════════════════════════
# 3. EDGE CONFIG VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestEdgeConfigs:
    """Edge configs must have checklists, convergence rules, and valid evaluator types."""

    @pytest.mark.tdd
    def test_all_referenced_edge_configs_exist(self, graph_topology):
        """Every edge_config path in graph_topology must resolve to a file."""
        for t in graph_topology["transitions"]:
            if "edge_config" in t:
                config_path = CONFIG_DIR / t["edge_config"]
                assert config_path.exists(), \
                    f"transition '{t['name']}' references missing edge config: {t['edge_config']}"

    @pytest.mark.tdd
    def test_edge_configs_have_checklist(self, all_edge_configs):
        """Edge configs with checklists must have at least one check."""
        for name, config in all_edge_configs.items():
            if "checklist" in config:
                assert len(config["checklist"]) > 0, f"edge config '{name}' has empty checklist"

    @pytest.mark.tdd
    def test_checklist_entries_have_required_fields(self, all_edge_configs):
        """Each checklist entry needs name, type, criterion, required."""
        for cfg_name, config in all_edge_configs.items():
            if "checklist" not in config:
                continue
            for i, check in enumerate(config["checklist"]):
                assert "name" in check, f"{cfg_name} check #{i} missing 'name'"
                assert "type" in check, f"{cfg_name} check '{check.get('name', i)}' missing 'type'"
                assert check["type"] in ("human", "agent", "deterministic"), \
                    f"{cfg_name} check '{check['name']}' has invalid type '{check['type']}'"
                assert "criterion" in check, f"{cfg_name} check '{check['name']}' missing 'criterion'"
                assert "required" in check, f"{cfg_name} check '{check['name']}' missing 'required'"

    @pytest.mark.tdd
    def test_deterministic_checks_have_command(self, all_edge_configs):
        """Deterministic checks should have command and pass_criterion (or use $variables)."""
        for cfg_name, config in all_edge_configs.items():
            if "checklist" not in config:
                continue
            for check in config["checklist"]:
                if check["type"] == "deterministic":
                    has_command = "command" in check
                    has_variable = "$" in check.get("criterion", "")
                    # Either has explicit command or uses $variable that will resolve
                    assert has_command or has_variable or "source" in check, \
                        f"{cfg_name} deterministic check '{check['name']}' needs command or $variable"

    @pytest.mark.tdd
    def test_edge_configs_have_convergence(self, all_edge_configs):
        """Edge configs should define convergence rules."""
        for name, config in all_edge_configs.items():
            if "checklist" in config:
                assert "convergence" in config, f"edge config '{name}' missing convergence rule"

    @pytest.mark.tdd
    def test_checklist_names_unique_within_edge(self, all_edge_configs):
        """Check names must be unique within each edge config."""
        for cfg_name, config in all_edge_configs.items():
            if "checklist" not in config:
                continue
            names = [c["name"] for c in config["checklist"]]
            dupes = [n for n in names if names.count(n) > 1]
            assert not dupes, f"{cfg_name} has duplicate check names: {set(dupes)}"


# ═══════════════════════════════════════════════════════════════════════
# 4. PROJECTION PROFILE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestProfiles:
    """Projection profiles must define graph, evaluators, convergence, context."""

    EXPECTED_PROFILES = {"full", "standard", "poc", "spike", "hotfix", "minimal"}

    @pytest.mark.tdd
    def test_all_six_profiles_exist(self):
        """All 6 named profiles must exist as YAML files."""
        actual = {p.stem for p in PROFILES_DIR.glob("*.yml")}
        missing = self.EXPECTED_PROFILES - actual
        assert not missing, f"missing profiles: {missing}"

    @pytest.mark.tdd
    def test_profiles_have_required_fields(self, all_profiles):
        """Each profile needs profile, description, version, graph, evaluators, convergence, context."""
        required_fields = {"profile", "description", "version", "graph", "evaluators", "convergence", "context"}
        for name, profile in all_profiles.items():
            for field in required_fields:
                assert field in profile, f"profile '{name}' missing field '{field}'"

    @pytest.mark.tdd
    def test_profiles_have_vector_types(self, all_profiles):
        """Each profile must declare which vector types it permits."""
        for name, profile in all_profiles.items():
            assert "vector_types" in profile, f"profile '{name}' missing vector_types"
            assert len(profile["vector_types"]) > 0, f"profile '{name}' has empty vector_types"

    @pytest.mark.tdd
    def test_profile_evaluator_types_valid(self, all_profiles):
        """Profile evaluator defaults must use valid evaluator types."""
        valid = {"human", "agent", "deterministic"}
        for name, profile in all_profiles.items():
            for e in profile["evaluators"].get("default", []):
                assert e in valid, f"profile '{name}' has invalid evaluator '{e}'"

    @pytest.mark.tdd
    def test_full_profile_includes_all_edges(self, all_profiles):
        """The 'full' profile must include all edges."""
        full = all_profiles["full"]
        assert full["graph"]["include"] == "all"

    @pytest.mark.tdd
    def test_full_profile_has_all_evaluator_types(self, all_profiles):
        """The 'full' profile must use all 3 evaluator types."""
        full = all_profiles["full"]
        assert set(full["evaluators"]["default"]) == {"human", "agent", "deterministic"}

    @pytest.mark.tdd
    def test_minimal_profile_is_lightest(self, all_profiles):
        """The 'minimal' profile must have the lightest configuration."""
        minimal = all_profiles["minimal"]
        assert minimal["context"]["density"] == "minimal"

    @pytest.mark.tdd
    def test_time_boxed_profiles_have_iteration_budget(self, all_profiles):
        """Profiles with time_boxed budget must specify time_box details."""
        for name, profile in all_profiles.items():
            if profile.get("iteration", {}).get("budget") == "time_boxed":
                assert "time_box" in profile["iteration"], \
                    f"profile '{name}' is time_boxed but missing time_box config"


# ═══════════════════════════════════════════════════════════════════════
# 5. PLUGIN.JSON CROSS-REFERENCE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestPluginJson:
    """Plugin manifest must reference files that exist."""

    @pytest.mark.tdd
    def test_all_commands_exist(self, plugin_json):
        """Every command path in plugin.json must resolve."""
        for cmd_path in plugin_json["commands"]:
            full_path = PLUGIN_ROOT / cmd_path
            assert full_path.exists(), f"plugin.json references missing command: {cmd_path}"

    @pytest.mark.tdd
    def test_all_agents_exist(self, plugin_json):
        """Every agent path in plugin.json must resolve."""
        for agent_path in plugin_json["agents"]:
            full_path = PLUGIN_ROOT / agent_path
            assert full_path.exists(), f"plugin.json references missing agent: {agent_path}"

    @pytest.mark.tdd
    def test_all_config_paths_exist(self, plugin_json):
        """Every config path in plugin.json must resolve."""
        for config_path in plugin_json["config"]:
            full_path = PLUGIN_ROOT / config_path
            assert full_path.exists(), f"plugin.json references missing config: {config_path}"

    @pytest.mark.tdd
    def test_command_count_matches_description(self, plugin_json):
        """plugin.json description should match actual command count."""
        count = len(plugin_json["commands"])
        desc = plugin_json["description"]
        assert str(count) in desc, \
            f"description says different count than actual {count} commands"


# ═══════════════════════════════════════════════════════════════════════
# 6. FEATURE VECTOR TEMPLATE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestFeatureVectorTemplate:
    """Feature vector template must have all required fields for v2.1."""

    @pytest.mark.tdd
    def test_has_core_fields(self, feature_vector_template):
        """Template must have feature, title, intent, status."""
        for field in ("feature", "title", "intent", "status"):
            assert field in feature_vector_template, f"template missing '{field}'"

    @pytest.mark.tdd
    def test_has_vector_type(self, feature_vector_template):
        """Template must declare vector_type."""
        assert "vector_type" in feature_vector_template

    @pytest.mark.tdd
    def test_has_profile(self, feature_vector_template):
        """Template must declare projection profile."""
        assert "profile" in feature_vector_template

    @pytest.mark.tdd
    def test_has_time_box(self, feature_vector_template):
        """Template must have time_box section."""
        assert "time_box" in feature_vector_template
        assert "enabled" in feature_vector_template["time_box"]

    @pytest.mark.tdd
    def test_has_parent_children(self, feature_vector_template):
        """Template must support spawn hierarchy."""
        assert "parent" in feature_vector_template
        assert "children" in feature_vector_template

    @pytest.mark.tdd
    def test_has_trajectory(self, feature_vector_template):
        """Template must have trajectory section with asset states."""
        assert "trajectory" in feature_vector_template
        traj = feature_vector_template["trajectory"]
        for asset in ("requirements", "design", "code", "unit_tests"):
            assert asset in traj, f"trajectory missing '{asset}'"

    @pytest.mark.tdd
    def test_has_constraints(self, feature_vector_template):
        """Template must have constraints section."""
        assert "constraints" in feature_vector_template
        c = feature_vector_template["constraints"]
        assert "acceptance_criteria" in c
        assert "threshold_overrides" in c
        assert "additional_checks" in c


# ═══════════════════════════════════════════════════════════════════════
# 7. REQ KEY CROSS-REFERENCE VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestReqKeyCoverage:
    """All REQ keys in spec must appear in feature vectors."""

    @pytest.mark.tdd
    def test_all_req_keys_in_feature_vectors(self):
        """Every REQ key from implementation requirements must be covered."""
        req_file = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        fv_file = SPEC_DIR / "FEATURE_VECTORS.md"

        # Extract REQ-{CAT}-{SEQ} keys from implementation requirements
        req_keys = set()
        with open(req_file) as f:
            for line in f:
                req_keys.update(re.findall(r'REQ-[A-Z]+-\d+', line))

        # Extract same keys from feature vectors
        fv_content = ""
        with open(fv_file) as f:
            fv_content = f.read()

        uncovered = {k for k in req_keys if k not in fv_content}
        assert not uncovered, f"REQ keys not in feature vectors: {uncovered}"

    @pytest.mark.tdd
    def test_feature_vectors_cover_all_requirements(self):
        """Feature vectors doc should claim full coverage."""
        fv_file = SPEC_DIR / "FEATURE_VECTORS.md"
        with open(fv_file) as f:
            content = f.read()
        assert "35/35 requirements covered" in content or "No orphans" in content

    @pytest.mark.tdd
    def test_commands_reference_req_keys(self):
        """Commands should reference the REQ keys they implement."""
        for cmd_path in COMMANDS_DIR.glob("*.md"):
            with open(cmd_path) as f:
                content = f.read()
            # At least some commands should have Implements: REQ-* comments
            # Not all commands need them, but the set should have some
        # Check that at least 3 commands reference REQ keys
        count = 0
        for cmd_path in COMMANDS_DIR.glob("*.md"):
            with open(cmd_path) as f:
                if "REQ-" in f.read():
                    count += 1
        assert count >= 3, f"Only {count} commands reference REQ keys"


# ═══════════════════════════════════════════════════════════════════════
# 8. EVALUATOR DEFAULTS VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestEvaluatorDefaults:
    """Evaluator defaults must define the 3 evaluator types."""

    @pytest.mark.tdd
    def test_three_evaluator_types_defined(self, evaluator_defaults):
        """Must define human, agent, and deterministic evaluator types."""
        types = evaluator_defaults["evaluator_types"]
        assert "human" in types
        assert "agent" in types
        assert "deterministic" in types

    @pytest.mark.tdd
    def test_evaluator_types_have_required_fields(self, evaluator_defaults):
        """Each evaluator type needs type, description, mechanism, convergence."""
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            assert "type" in evtype, f"evaluator '{name}' missing 'type'"
            assert "description" in evtype, f"evaluator '{name}' missing 'description'"
            assert "mechanism" in evtype, f"evaluator '{name}' missing 'mechanism'"
            assert "convergence" in evtype, f"evaluator '{name}' missing 'convergence'"

    @pytest.mark.tdd
    def test_convergence_rules_defined(self, evaluator_defaults):
        """Convergence rules must be defined."""
        assert "convergence_rules" in evaluator_defaults
        rules = evaluator_defaults["convergence_rules"]
        assert "composition" in rules
        assert rules["composition"] == "all_must_pass"
