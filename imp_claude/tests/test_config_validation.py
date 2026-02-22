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
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, DESIGN_DIR, load_yaml,
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
    """Claude-specific REQ key validation (commands reference REQ keys)."""

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


# ═══════════════════════════════════════════════════════════════════════
# 9. CONSTRAINT DIMENSIONS VALIDATION (Spec §2.6.1)
# ═══════════════════════════════════════════════════════════════════════


class TestConstraintDimensions:
    """Constraint dimensions in graph_topology must define the taxonomy for design disambiguation."""

    EXPECTED_DIMENSIONS = {
        "ecosystem_compatibility", "deployment_target", "security_model",
        "data_governance", "performance_envelope", "build_system",
        "observability", "error_handling",
    }
    MANDATORY_DIMENSIONS = {
        "ecosystem_compatibility", "deployment_target", "security_model", "build_system",
    }
    ADVISORY_DIMENSIONS = {
        "data_governance", "performance_envelope", "observability", "error_handling",
    }
    VALID_RESOLVES_VIA = {"adr", "adr_or_design_section", "design_section"}

    @pytest.mark.tdd
    def test_constraint_dimensions_section_exists(self, graph_topology):
        """Graph topology must have a constraint_dimensions section."""
        assert "constraint_dimensions" in graph_topology

    @pytest.mark.tdd
    def test_all_eight_dimensions_present(self, graph_topology):
        """All 8 constraint dimensions must be defined."""
        dims = set(graph_topology["constraint_dimensions"].keys())
        missing = self.EXPECTED_DIMENSIONS - dims
        assert not missing, f"missing constraint dimensions: {missing}"

    @pytest.mark.tdd
    def test_dimensions_have_required_fields(self, graph_topology):
        """Each dimension needs description, mandatory, resolves_via, examples."""
        for name, dim in graph_topology["constraint_dimensions"].items():
            assert "description" in dim, f"dimension '{name}' missing description"
            assert "mandatory" in dim, f"dimension '{name}' missing mandatory flag"
            assert isinstance(dim["mandatory"], bool), f"dimension '{name}' mandatory must be bool"
            assert "resolves_via" in dim, f"dimension '{name}' missing resolves_via"
            assert dim["resolves_via"] in self.VALID_RESOLVES_VIA, \
                f"dimension '{name}' resolves_via '{dim['resolves_via']}' not in {self.VALID_RESOLVES_VIA}"
            assert "examples" in dim, f"dimension '{name}' missing examples"
            assert len(dim["examples"]) >= 1, f"dimension '{name}' needs at least 1 example"

    @pytest.mark.tdd
    def test_mandatory_dimensions_correctly_flagged(self, graph_topology):
        """Exactly 4 dimensions must be mandatory."""
        dims = graph_topology["constraint_dimensions"]
        actual_mandatory = {n for n, d in dims.items() if d["mandatory"]}
        assert actual_mandatory == self.MANDATORY_DIMENSIONS, \
            f"mandatory mismatch: expected {self.MANDATORY_DIMENSIONS}, got {actual_mandatory}"

    @pytest.mark.tdd
    def test_advisory_dimensions_correctly_flagged(self, graph_topology):
        """Exactly 4 dimensions must be advisory (not mandatory)."""
        dims = graph_topology["constraint_dimensions"]
        actual_advisory = {n for n, d in dims.items() if not d["mandatory"]}
        assert actual_advisory == self.ADVISORY_DIMENSIONS, \
            f"advisory mismatch: expected {self.ADVISORY_DIMENSIONS}, got {actual_advisory}"

    @pytest.mark.tdd
    def test_mandatory_dimensions_resolve_via_adr(self, graph_topology):
        """Mandatory dimensions must resolve via ADR (not just design section)."""
        dims = graph_topology["constraint_dimensions"]
        for name in self.MANDATORY_DIMENSIONS:
            assert dims[name]["resolves_via"] in ("adr", "adr_or_design_section"), \
                f"mandatory dimension '{name}' should resolve via ADR, got '{dims[name]['resolves_via']}'"


# ═══════════════════════════════════════════════════════════════════════
# 10. REQUIREMENTS→DESIGN CONSTRAINT DIMENSION CHECKS
# ═══════════════════════════════════════════════════════════════════════


class TestRequirementsDesignDimensionChecks:
    """Requirements→Design edge must have checklist items for constraint dimension resolution."""

    MANDATORY_CHECKS = [
        "ecosystem_compatibility_resolved",
        "deployment_target_resolved",
        "security_model_resolved",
        "build_system_resolved",
    ]

    @pytest.fixture
    def req_design_config(self):
        return load_yaml(EDGE_PARAMS_DIR / "requirements_design.yml")

    @pytest.mark.tdd
    def test_mandatory_dimension_checks_present(self, req_design_config):
        """Checklist must include a check for each mandatory constraint dimension."""
        check_names = [c["name"] for c in req_design_config["checklist"]]
        for name in self.MANDATORY_CHECKS:
            assert name in check_names, f"missing mandatory dimension check: {name}"

    @pytest.mark.tdd
    def test_mandatory_dimension_checks_required(self, req_design_config):
        """Each mandatory dimension check must be required: true."""
        checks_by_name = {c["name"]: c for c in req_design_config["checklist"]}
        for name in self.MANDATORY_CHECKS:
            assert checks_by_name[name]["required"] is True, \
                f"dimension check '{name}' must be required"

    @pytest.mark.tdd
    def test_mandatory_dimension_checks_are_agent_type(self, req_design_config):
        """Dimension checks are agent-evaluated (not deterministic)."""
        checks_by_name = {c["name"]: c for c in req_design_config["checklist"]}
        for name in self.MANDATORY_CHECKS:
            assert checks_by_name[name]["type"] == "agent", \
                f"dimension check '{name}' should be type 'agent'"

    @pytest.mark.tdd
    def test_advisory_dimensions_check_present(self, req_design_config):
        """Advisory dimensions check must exist and be optional."""
        checks_by_name = {c["name"]: c for c in req_design_config["checklist"]}
        assert "advisory_dimensions_considered" in checks_by_name
        assert checks_by_name["advisory_dimensions_considered"]["required"] is False

    @pytest.mark.tdd
    def test_dimension_checks_reference_project_constraints(self, req_design_config):
        """Dimension check criteria should reference project_constraints.yml."""
        checks_by_name = {c["name"]: c for c in req_design_config["checklist"]}
        for name in self.MANDATORY_CHECKS:
            criterion = checks_by_name[name]["criterion"]
            assert "project_constraints" in criterion or "constraint_dimensions" in criterion, \
                f"dimension check '{name}' criterion should reference project_constraints"

    @pytest.mark.tdd
    def test_source_analysis_section_exists(self, req_design_config):
        """Requirements→Design must have source_analysis section."""
        assert "source_analysis" in req_design_config
        assert len(req_design_config["source_analysis"]) >= 3

    @pytest.mark.tdd
    def test_source_analysis_checks_have_required_fields(self, req_design_config):
        """Each source_analysis check needs name, criterion, required."""
        for check in req_design_config["source_analysis"]:
            assert "name" in check, f"source_analysis check missing 'name'"
            assert "criterion" in check, f"source_analysis check '{check.get('name')}' missing 'criterion'"
            assert "required" in check, f"source_analysis check '{check.get('name')}' missing 'required'"

    @pytest.mark.tdd
    def test_agent_guidance_includes_dimension_loading(self, req_design_config):
        """Agent guidance must include constraint dimension loading step."""
        guidance = req_design_config["agent_guidance"]
        assert "LOAD CONSTRAINT DIMENSIONS" in guidance or "constraint_dimensions" in guidance

    @pytest.mark.tdd
    def test_context_guidance_requires_project_constraints(self, req_design_config):
        """Context guidance must list project_constraints.yml as required."""
        required_ctx = req_design_config["context_guidance"]["required"]
        ctx_str = " ".join(str(c) for c in required_ctx)
        assert "project_constraints" in ctx_str


# ═══════════════════════════════════════════════════════════════════════
# 11. PROJECT CONSTRAINTS TEMPLATE — DIMENSION BINDINGS
# ═══════════════════════════════════════════════════════════════════════


class TestProjectConstraintsDimensions:
    """Project constraints template must have binding fields for all constraint dimensions."""

    @pytest.mark.tdd
    def test_constraint_dimensions_section_exists(self, project_constraints_template):
        """Template must have constraint_dimensions section."""
        assert "constraint_dimensions" in project_constraints_template

    @pytest.mark.tdd
    def test_all_topology_dimensions_have_bindings(self, graph_topology, project_constraints_template):
        """Every dimension in graph_topology must have a binding in project_constraints template."""
        topology_dims = set(graph_topology["constraint_dimensions"].keys())
        template_dims = set(project_constraints_template["constraint_dimensions"].keys())
        missing = topology_dims - template_dims
        assert not missing, f"dimensions in topology but not in template: {missing}"

    @pytest.mark.tdd
    def test_ecosystem_compatibility_has_fields(self, project_constraints_template):
        """Ecosystem compatibility binding must have language, version, runtime, frameworks."""
        eco = project_constraints_template["constraint_dimensions"]["ecosystem_compatibility"]
        for field in ("language", "version", "runtime", "frameworks"):
            assert field in eco, f"ecosystem_compatibility missing field '{field}'"

    @pytest.mark.tdd
    def test_deployment_target_has_fields(self, project_constraints_template):
        """Deployment target binding must have platform, cloud_provider."""
        dep = project_constraints_template["constraint_dimensions"]["deployment_target"]
        for field in ("platform", "cloud_provider"):
            assert field in dep, f"deployment_target missing field '{field}'"

    @pytest.mark.tdd
    def test_security_model_has_fields(self, project_constraints_template):
        """Security model binding must have authentication, authorisation, data_protection."""
        sec = project_constraints_template["constraint_dimensions"]["security_model"]
        for field in ("authentication", "authorisation", "data_protection"):
            assert field in sec, f"security_model missing field '{field}'"

    @pytest.mark.tdd
    def test_build_system_has_fields(self, project_constraints_template):
        """Build system binding must have tool, module_structure."""
        bld = project_constraints_template["constraint_dimensions"]["build_system"]
        for field in ("tool", "module_structure"):
            assert field in bld, f"build_system missing field '{field}'"

    @pytest.mark.tdd
    def test_advisory_dimensions_present(self, project_constraints_template):
        """All 4 advisory dimensions must be present in template."""
        dims = project_constraints_template["constraint_dimensions"]
        for name in ("data_governance", "performance_envelope", "observability", "error_handling"):
            assert name in dims, f"advisory dimension '{name}' missing from template"


# ═══════════════════════════════════════════════════════════════════════
# 12. VERSION CONSISTENCY
# ═══════════════════════════════════════════════════════════════════════


class TestVersionConsistency:
    """Version references must be consistent across spec, plugin, and configs."""

    @pytest.mark.tdd
    def test_plugin_version_is_2_8(self, plugin_json):
        """plugin.json version must be 2.8.0."""
        assert plugin_json["version"] == "2.8.0"

    @pytest.mark.tdd
    def test_graph_topology_version_is_2_7(self, graph_topology):
        """graph_topology.yml version must be 2.7.0."""
        assert graph_topology["graph_properties"]["version"] == "2.7.0"

    @pytest.mark.tdd
    def test_plugin_description_mentions_event_sourcing_or_iterate(self, plugin_json):
        """Plugin description should mention core methodology concepts."""
        desc = plugin_json["description"]
        assert "event sourcing" in desc or "iterate" in desc

    @pytest.mark.tdd
    def test_plugin_description_mentions_event_sourcing(self, plugin_json):
        """Plugin description should mention event sourcing."""
        assert "event sourcing" in plugin_json["description"]


# ═══════════════════════════════════════════════════════════════════════
# Consciousness Loop — Signal Source Validation
# ═══════════════════════════════════════════════════════════════════════


class TestFeedbackLoopConfig:
    """Validate feedback_loop.yml signal source configuration."""

    REQUIRED_SIGNAL_SOURCES = {
        "gap", "test_failure", "refactoring",
        "source_finding", "process_gap",
        "runtime_feedback", "ecosystem",
    }

    @pytest.mark.tdd
    def test_feedback_loop_config_exists(self):
        """feedback_loop.yml must exist in edge_params."""
        assert (EDGE_PARAMS_DIR / "feedback_loop.yml").exists()

    @pytest.mark.tdd
    def test_feedback_loop_has_sources_section(self, all_edge_configs):
        """feedback_loop.yml must have a sources section."""
        feedback = all_edge_configs["feedback_loop"]
        assert "sources" in feedback

    @pytest.mark.tdd
    def test_feedback_loop_signal_sources_are_complete(self, all_edge_configs):
        """All 7 signal source types must be defined."""
        feedback = all_edge_configs["feedback_loop"]
        sources = feedback.get("sources", {})
        found_signals = set()
        for key, val in sources.items():
            if isinstance(val, dict) and "signal_source" in val:
                found_signals.add(val["signal_source"])
        missing = self.REQUIRED_SIGNAL_SOURCES - found_signals
        assert not missing, f"Missing signal sources: {missing}"

    @pytest.mark.tdd
    def test_each_source_has_description(self, all_edge_configs):
        """Each signal source must have a description."""
        feedback = all_edge_configs["feedback_loop"]
        for key, val in feedback.get("sources", {}).items():
            if isinstance(val, dict) and "signal_source" in val:
                assert "description" in val, f"Source {key} missing description"

    @pytest.mark.tdd
    def test_each_source_has_trigger(self, all_edge_configs):
        """Each signal source must have a trigger description."""
        feedback = all_edge_configs["feedback_loop"]
        for key, val in feedback.get("sources", {}).items():
            if isinstance(val, dict) and "signal_source" in val:
                assert "trigger" in val, f"Source {key} missing trigger"

    @pytest.mark.tdd
    def test_intent_raised_schema_defined(self, all_edge_configs):
        """feedback_loop.yml must define the intent_raised event schema."""
        feedback = all_edge_configs["feedback_loop"]
        assert "intent_raised_schema" in feedback
        schema = feedback["intent_raised_schema"]
        assert schema.get("event_type") == "intent_raised"

    @pytest.mark.tdd
    def test_intent_raised_schema_has_required_fields(self, all_edge_configs):
        """intent_raised schema must include all required fields."""
        feedback = all_edge_configs["feedback_loop"]
        schema = feedback.get("intent_raised_schema", {})
        fields = schema.get("fields", [])
        field_names = set()
        for f in fields:
            if isinstance(f, dict):
                field_names.update(f.keys())
        required = {"timestamp", "project", "intent_id", "trigger", "delta",
                    "signal_source", "vector_type", "affected_req_keys",
                    "prior_intents", "edge_context", "severity"}
        missing = required - field_names
        assert not missing, f"intent_raised schema missing fields: {missing}"


class TestTDDIntentGeneration:
    """Validate TDD edge config has intent generation for failures and refactoring."""

    @pytest.mark.tdd
    def test_tdd_guidance_mentions_intent_raised(self, all_edge_configs):
        """TDD agent guidance must mention intent_raised event."""
        tdd = all_edge_configs["tdd"]
        guidance = tdd.get("agent_guidance", "")
        assert "intent_raised" in guidance

    @pytest.mark.tdd
    def test_tdd_guidance_mentions_stuck_delta(self, all_edge_configs):
        """TDD agent guidance must mention stuck delta threshold (>3 iterations)."""
        tdd = all_edge_configs["tdd"]
        guidance = tdd.get("agent_guidance", "")
        assert "3 iteration" in guidance or "> 3" in guidance

    @pytest.mark.tdd
    def test_tdd_guidance_mentions_refactoring_signal(self, all_edge_configs):
        """TDD agent guidance must mention refactoring as a signal source."""
        tdd = all_edge_configs["tdd"]
        guidance = tdd.get("agent_guidance", "")
        assert "refactoring" in guidance


class TestRequirementsLineage:
    """Validate that Claude ADR references consciousness loop requirements."""

    CONSCIOUSNESS_REQS = ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]

    @pytest.mark.tdd
    def test_adr_011_references_all_consciousness_reqs(self):
        """ADR-011 must reference all consciousness loop requirements."""
        adr_path = DESIGN_DIR / "adrs/ADR-011-consciousness-loop-at-every-observer.md"
        with open(adr_path) as f:
            content = f.read()
        for req in self.CONSCIOUSNESS_REQS:
            assert req in content, f"ADR-011 missing {req}"


# ═══════════════════════════════════════════════════════════════════════
# 14. PROCESSING PHASES VALIDATION (Spec §4.3)
# ═══════════════════════════════════════════════════════════════════════


class TestProcessingPhases:
    """Evaluator defaults must declare processing_phase for each evaluator type."""

    @pytest.mark.tdd
    def test_human_is_conscious(self, evaluator_defaults):
        """Human evaluator must be classified as conscious processing phase."""
        human = evaluator_defaults["evaluator_types"]["human"]
        assert human.get("processing_phase") == "conscious"

    @pytest.mark.tdd
    def test_agent_is_conscious(self, evaluator_defaults):
        """Agent evaluator must be classified as conscious processing phase."""
        agent = evaluator_defaults["evaluator_types"]["agent"]
        assert agent.get("processing_phase") == "conscious"

    @pytest.mark.tdd
    def test_deterministic_is_reflex(self, evaluator_defaults):
        """Deterministic evaluator must be classified as reflex processing phase."""
        det = evaluator_defaults["evaluator_types"]["deterministic"]
        assert det.get("processing_phase") == "reflex"

    @pytest.mark.tdd
    def test_all_evaluator_types_have_processing_phase(self, evaluator_defaults):
        """Every evaluator type must declare a processing_phase field."""
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            assert "processing_phase" in evtype, \
                f"evaluator '{name}' missing processing_phase field"

    @pytest.mark.tdd
    def test_processing_phase_values_valid(self, evaluator_defaults):
        """processing_phase values must be 'conscious', 'affect', or 'reflex'."""
        valid = {"conscious", "affect", "reflex"}
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            phase = evtype.get("processing_phase")
            assert phase in valid, \
                f"evaluator '{name}' has invalid processing_phase '{phase}'"

    @pytest.mark.tdd
    def test_all_evaluator_types_have_processing_phases_list(self, evaluator_defaults):
        """Every evaluator type must declare a processing_phases list field."""
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            assert "processing_phases" in evtype, \
                f"evaluator '{name}' missing processing_phases list field"
            assert isinstance(evtype["processing_phases"], list), \
                f"evaluator '{name}' processing_phases must be a list"

    @pytest.mark.tdd
    def test_agent_spans_conscious_and_affect(self, evaluator_defaults):
        """Agent evaluator must declare both conscious and affect processing phases."""
        agent = evaluator_defaults["evaluator_types"]["agent"]
        phases = agent["processing_phases"]
        assert "conscious" in phases, "agent missing conscious in processing_phases"
        assert "affect" in phases, "agent missing affect in processing_phases"

    @pytest.mark.tdd
    def test_affect_phase_has_evaluator(self, evaluator_defaults):
        """At least one evaluator must include 'affect' in its processing_phases."""
        found = False
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            if "affect" in evtype.get("processing_phases", []):
                found = True
                break
        assert found, "no evaluator is tagged with processing_phases containing 'affect'"

    @pytest.mark.tdd
    def test_processing_phases_section_exists(self, evaluator_defaults):
        """evaluator_defaults.yml must have a processing_phases section."""
        assert "processing_phases" in evaluator_defaults

    @pytest.mark.tdd
    def test_processing_phases_has_all_three(self, evaluator_defaults):
        """processing_phases must define reflex, affect, and conscious."""
        phases = evaluator_defaults["processing_phases"]
        assert "reflex" in phases
        assert "affect" in phases
        assert "conscious" in phases

    @pytest.mark.tdd
    def test_processing_phases_have_descriptions(self, evaluator_defaults):
        """Each processing phase must have description, analogy, includes, fires_when."""
        for name, phase in evaluator_defaults["processing_phases"].items():
            assert "description" in phase, f"phase '{name}' missing description"
            assert "analogy" in phase, f"phase '{name}' missing analogy"
            assert "includes" in phase, f"phase '{name}' missing includes"
            assert "fires_when" in phase, f"phase '{name}' missing fires_when"


# ═══════════════════════════════════════════════════════════════════════
# 15. SENSORY SYSTEMS REQUIREMENTS VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestSensoryRequirements:
    """Claude-specific: design doc validation for sensory requirements."""

    @pytest.mark.tdd
    def test_design_doc_covers_sense_feature_vector(self):
        """Design doc feature vector coverage must include REQ-F-SENSE-001."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "REQ-F-SENSE-001" in content

    @pytest.mark.tdd
    def test_design_doc_claims_all_feature_vectors(self):
        """Design doc must claim all feature vectors covered (11 including SUPV-001)."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "11/11 feature vectors covered" in content


# ═══════════════════════════════════════════════════════════════════════
# 16. CONTEXT SOURCES VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestContextSources:
    """Context sources (URI-based external AD collections) must be defined in template."""

    @pytest.mark.tdd
    def test_template_has_context_sources_field(self, project_constraints_template):
        """project_constraints_template.yml must contain context_sources."""
        assert "context_sources" in project_constraints_template

    @pytest.mark.tdd
    def test_context_sources_is_list(self, project_constraints_template):
        """context_sources parsed value must be a list."""
        assert isinstance(project_constraints_template["context_sources"], list)

    @pytest.mark.tdd
    def test_context_sources_default_empty(self, project_constraints_template):
        """Default template must have empty context_sources list."""
        assert project_constraints_template["context_sources"] == []

    @pytest.mark.tdd
    def test_context_source_entry_schema(self):
        """Commented examples must show uri, scope, description fields."""
        with open(CONFIG_DIR / "project_constraints_template.yml") as f:
            raw = f.read()
        assert "uri:" in raw
        assert "scope:" in raw
        assert "description:" in raw

    @pytest.mark.tdd
    def test_valid_scopes_documented(self):
        """Template comments must mention adrs, data_models, templates, policy, standards."""
        with open(CONFIG_DIR / "project_constraints_template.yml") as f:
            raw = f.read()
        for scope in ("adrs", "data_models", "templates", "policy", "standards"):
            assert scope in raw, f"scope '{scope}' not documented in template"

    @pytest.mark.tdd
    def test_init_documents_context_sources_step(self):
        """aisdlc-init.md must contain 'Resolve Context Sources' step."""
        with open(COMMANDS_DIR / "aisdlc-init.md") as f:
            content = f.read()
        assert "Resolve Context Sources" in content


# ═══════════════════════════════════════════════════════════════════════
# 17. START COMMAND VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestStartCommand:
    """Validate /aisdlc-start command exists and is properly registered."""

    @pytest.mark.tdd
    def test_start_command_exists(self):
        """aisdlc-start.md must exist in commands directory."""
        assert (COMMANDS_DIR / "aisdlc-start.md").exists()

    @pytest.mark.tdd
    def test_plugin_registers_start_command(self, plugin_json):
        """plugin.json must list the start command."""
        assert "./commands/aisdlc-start.md" in plugin_json["commands"]

    @pytest.mark.tdd
    def test_plugin_has_13_commands(self, plugin_json):
        """plugin.json must have 13 commands."""
        assert len(plugin_json["commands"]) == 13

    @pytest.mark.tdd
    def test_default_profile_in_template(self, project_constraints_template):
        """project_constraints_template must have default_profile field."""
        assert "default_profile" in project_constraints_template.get("project", {})

    @pytest.mark.tdd
    def test_adr_012_exists(self):
        """ADR-012 (two-command UX layer) must exist."""
        adr_path = DESIGN_DIR / "adrs/ADR-012-two-command-ux-layer.md"
        assert adr_path.exists(), "ADR-012 not found"

    @pytest.mark.tdd
    def test_adr_012_references_ux_requirements(self):
        """ADR-012 must reference REQ-UX-001 through REQ-UX-005."""
        adr_path = DESIGN_DIR / "adrs/ADR-012-two-command-ux-layer.md"
        with open(adr_path) as f:
            content = f.read()
        for i in range(1, 6):
            assert f"REQ-UX-{i:03d}" in content, f"ADR-012 missing REQ-UX-{i:03d}"


# ═══════════════════════════════════════════════════════════════════════
# 18. MULTI-AGENT COORDINATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════


class TestMultiAgentCoordination:
    """Validate multi-agent coordination requirements and design artifacts.

    NOTE — Design-stage coverage only (Phase 1a):
    These tests verify that spec, design, and ADR documents define the coordination
    protocol correctly and consistently (presence/wording checks). They do NOT test
    behavioural protocol semantics. When the serialiser engine is implemented, add:
      - Competing claims: two agents claim same feature+edge → one gets edge_started,
        other gets claim_rejected
      - Stale claim emission: no event within timeout → claim_expired
      - Serialiser ordering: deterministic resolution across platforms (lexicographic
        agent_id, monotonic sequence numbers)
      - Single-agent / multi-agent mode transitions: exactly-one-writer invariant holds
      - Role-based authority: convergence outside role → convergence_escalated
      - Inbox semantics: inbox deletion does not lose committed events
    """

    COORD_REQS = ["REQ-COORD-001", "REQ-COORD-002", "REQ-COORD-003",
                  "REQ-COORD-004", "REQ-COORD-005"]

    @pytest.mark.tdd
    def test_adr_013_exists(self):
        """ADR-013 (multi-agent coordination) must exist."""
        adr_path = DESIGN_DIR / "adrs/ADR-013-multi-agent-coordination.md"
        assert adr_path.exists(), "ADR-013 not found"

    @pytest.mark.tdd
    def test_adr_013_references_coord_requirements(self):
        """ADR-013 must reference REQ-COORD-001 through REQ-COORD-005."""
        adr_path = DESIGN_DIR / "adrs/ADR-013-multi-agent-coordination.md"
        with open(adr_path) as f:
            content = f.read()
        for req in self.COORD_REQS:
            assert req in content, f"ADR-013 missing {req}"

    @pytest.mark.tdd
    def test_design_doc_has_multi_agent_section(self):
        """Design doc must have §1.10 Multi-Agent Coordination."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "1.10 Multi-Agent Coordination" in content

    @pytest.mark.tdd
    def test_design_doc_covers_coord_feature_vector(self):
        """Design doc feature vector coverage must include REQ-F-COORD-001."""
        design_path = DESIGN_DIR / "AISDLC_V2_DESIGN.md"
        with open(design_path) as f:
            content = f.read()
        assert "REQ-F-COORD-001" in content

    @pytest.mark.tdd
    def test_adr_013_mentions_no_lock_files(self):
        """ADR-013 must explicitly state no lock files."""
        adr_path = DESIGN_DIR / "adrs/ADR-013-multi-agent-coordination.md"
        with open(adr_path) as f:
            content = f.read()
        assert "No lock files" in content or "no lock files" in content

    @pytest.mark.tdd
    def test_adr_013_mentions_inbox_serialiser(self):
        """ADR-013 must describe inbox/serialiser pattern."""
        adr_path = DESIGN_DIR / "adrs/ADR-013-multi-agent-coordination.md"
        with open(adr_path) as f:
            content = f.read()
        assert "inbox" in content.lower()
        assert "serialiser" in content.lower()

    @pytest.mark.tdd
    def test_adr_013_mentions_event_sourced_claims(self):
        """ADR-013 must describe event-sourced claims."""
        adr_path = DESIGN_DIR / "adrs/ADR-013-multi-agent-coordination.md"
        with open(adr_path) as f:
            content = f.read()
        assert "edge_claim" in content
        assert "claim_rejected" in content


# ═══════════════════════════════════════════════════════════════════════
# 19. FUNCTOR ENCODING VALIDATION (Spec §2.9, ADR-017)
# ═══════════════════════════════════════════════════════════════════════


class TestFunctorEncoding:
    """Validate functor encoding sections in profiles, edge params, and feature vector template."""

    VALID_FUNCTIONAL_UNITS = {
        "evaluate", "construct", "classify", "route",
        "propose", "sense", "emit", "decide",
    }
    VALID_CATEGORIES = {"F_D", "F_P", "F_H"}
    VALID_VALENCE = {"high", "medium", "low"}
    VALID_MODE = {"headless", "interactive", "autopilot"}
    # Category-fixed units: emit is always F_D, decide is always F_H
    CATEGORY_FIXED = {"emit": "F_D", "decide": "F_H"}

    @pytest.mark.tdd
    def test_all_profiles_have_encoding_section(self, all_profiles):
        """Every profile must have an encoding section."""
        for name, profile in all_profiles.items():
            assert "encoding" in profile, f"profile '{name}' missing encoding section"

    @pytest.mark.tdd
    def test_profile_encoding_has_required_fields(self, all_profiles):
        """Each profile encoding needs strategy, mode, valence, functional_units."""
        for name, profile in all_profiles.items():
            enc = profile["encoding"]
            for field in ("strategy", "mode", "valence", "functional_units"):
                assert field in enc, f"profile '{name}' encoding missing '{field}'"

    @pytest.mark.tdd
    def test_profile_functional_units_are_valid(self, all_profiles):
        """All 8 functional units must be defined with valid categories."""
        for name, profile in all_profiles.items():
            units = profile["encoding"]["functional_units"]
            actual_units = set(units.keys())
            missing = self.VALID_FUNCTIONAL_UNITS - actual_units
            assert not missing, f"profile '{name}' missing functional units: {missing}"
            for unit, category in units.items():
                assert category in self.VALID_CATEGORIES, \
                    f"profile '{name}' unit '{unit}' has invalid category '{category}'"

    @pytest.mark.tdd
    def test_category_fixed_units_correct(self, all_profiles):
        """emit must always be F_D, decide must always be F_H."""
        for name, profile in all_profiles.items():
            units = profile["encoding"]["functional_units"]
            for unit, expected_cat in self.CATEGORY_FIXED.items():
                assert units[unit] == expected_cat, \
                    f"profile '{name}' category-fixed unit '{unit}' must be {expected_cat}, got {units[unit]}"

    @pytest.mark.tdd
    def test_profile_valence_valid(self, all_profiles):
        """Profile valence must be high, medium, or low."""
        for name, profile in all_profiles.items():
            assert profile["encoding"]["valence"] in self.VALID_VALENCE, \
                f"profile '{name}' has invalid valence '{profile['encoding']['valence']}'"

    @pytest.mark.tdd
    def test_profile_mode_valid(self, all_profiles):
        """Profile mode must be headless, interactive, or autopilot."""
        for name, profile in all_profiles.items():
            assert profile["encoding"]["mode"] in self.VALID_MODE, \
                f"profile '{name}' has invalid mode '{profile['encoding']['mode']}'"

    @pytest.mark.tdd
    def test_edge_params_functional_unit_valid(self, all_edge_configs):
        """functional_unit values in edge param checklists must be valid."""
        valid_units = {"evaluate", "construct", "classify", "route",
                       "propose", "sense", "emit", "decide"}
        for cfg_name, config in all_edge_configs.items():
            for section_key in ("checklist", "source_analysis"):
                if section_key not in config:
                    continue
                items = config[section_key]
                if not isinstance(items, list):
                    # traceability.yml has layer_* dicts
                    continue
                for item in items:
                    if isinstance(item, dict) and "functional_unit" in item:
                        assert item["functional_unit"] in valid_units, \
                            f"{cfg_name} check '{item.get('name', '?')}' has invalid functional_unit '{item['functional_unit']}'"

    @pytest.mark.tdd
    def test_feature_vector_template_functor_optional(self, feature_vector_template):
        """Feature vector template functor section must exist with required fields."""
        assert "functor" in feature_vector_template
        functor = feature_vector_template["functor"]
        for field in ("encoding_source", "mode", "valence", "overrides"):
            assert field in functor, f"functor missing '{field}'"

    @pytest.mark.tdd
    def test_feature_vector_template_escalations(self, feature_vector_template):
        """Each trajectory entry must have an escalations list."""
        traj = feature_vector_template["trajectory"]
        for asset in ("requirements", "design", "code", "unit_tests", "uat_tests"):
            assert "escalations" in traj[asset], \
                f"trajectory '{asset}' missing escalations field"
            assert isinstance(traj[asset]["escalations"], list), \
                f"trajectory '{asset}' escalations must be a list"
