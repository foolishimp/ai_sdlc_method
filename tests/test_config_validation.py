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
    AGENTS_DIR, PLUGIN_ROOT, SPEC_DIR, DOCS_DIR, load_yaml,
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
        assert "39/39 requirements covered" in content or "No orphans" in content

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
    def test_plugin_version_is_2_5(self, plugin_json):
        """plugin.json version must be 2.5.0."""
        assert plugin_json["version"] == "2.5.0"

    @pytest.mark.tdd
    def test_graph_topology_version_is_2_5(self, graph_topology):
        """graph_topology.yml version must be 2.5.0."""
        assert graph_topology["graph_properties"]["version"] == "2.5.0"

    @pytest.mark.tdd
    def test_plugin_description_mentions_constraint_dimensions(self, plugin_json):
        """Plugin description should mention constraint dimensions."""
        assert "constraint dimensions" in plugin_json["description"]

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
    """Validate that consciousness loop requirements exist and trace correctly."""

    CONSCIOUSNESS_REQS = ["REQ-LIFE-005", "REQ-LIFE-006", "REQ-LIFE-007", "REQ-LIFE-008"]

    @pytest.mark.tdd
    def test_consciousness_reqs_exist(self):
        """REQ-LIFE-005 through REQ-LIFE-008 must exist in implementation requirements."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        for req in self.CONSCIOUSNESS_REQS:
            assert req in content, f"{req} not found in implementation requirements"

    @pytest.mark.tdd
    def test_consciousness_reqs_trace_to_spec(self):
        """Each consciousness requirement must trace to the formal spec."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        # Each REQ-LIFE-005..008 should reference Asset Graph Model
        assert "Asset Graph Model §7.7" in content

    @pytest.mark.tdd
    def test_adr_011_references_all_consciousness_reqs(self):
        """ADR-011 must reference all consciousness loop requirements."""
        adr_path = DOCS_DIR / "design/claude_aisdlc/adrs/ADR-011-consciousness-loop-at-every-observer.md"
        with open(adr_path) as f:
            content = f.read()
        for req in self.CONSCIOUSNESS_REQS:
            assert req in content, f"ADR-011 missing {req}"

    @pytest.mark.tdd
    def test_requirement_count_updated(self):
        """Total requirement count should reflect additions (was 35, now 39)."""
        req_path = SPEC_DIR / "AISDLC_IMPLEMENTATION_REQUIREMENTS.md"
        with open(req_path) as f:
            content = f.read()
        assert "**39**" in content or "| **Total** | **39**" in content


# ═══════════════════════════════════════════════════════════════════════
# 14. PROCESSING REGIMES VALIDATION (Spec §4.3)
# ═══════════════════════════════════════════════════════════════════════


class TestProcessingRegimes:
    """Evaluator defaults must declare processing_regime for each evaluator type."""

    @pytest.mark.tdd
    def test_human_is_conscious(self, evaluator_defaults):
        """Human evaluator must be classified as conscious processing regime."""
        human = evaluator_defaults["evaluator_types"]["human"]
        assert human.get("processing_regime") == "conscious"

    @pytest.mark.tdd
    def test_agent_is_conscious(self, evaluator_defaults):
        """Agent evaluator must be classified as conscious processing regime."""
        agent = evaluator_defaults["evaluator_types"]["agent"]
        assert agent.get("processing_regime") == "conscious"

    @pytest.mark.tdd
    def test_deterministic_is_reflex(self, evaluator_defaults):
        """Deterministic evaluator must be classified as reflex processing regime."""
        det = evaluator_defaults["evaluator_types"]["deterministic"]
        assert det.get("processing_regime") == "reflex"

    @pytest.mark.tdd
    def test_all_evaluator_types_have_processing_regime(self, evaluator_defaults):
        """Every evaluator type must declare a processing_regime field."""
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            assert "processing_regime" in evtype, \
                f"evaluator '{name}' missing processing_regime field"

    @pytest.mark.tdd
    def test_processing_regime_values_valid(self, evaluator_defaults):
        """processing_regime values must be 'conscious' or 'reflex'."""
        valid = {"conscious", "reflex"}
        for name, evtype in evaluator_defaults["evaluator_types"].items():
            regime = evtype.get("processing_regime")
            assert regime in valid, \
                f"evaluator '{name}' has invalid processing_regime '{regime}'"

    @pytest.mark.tdd
    def test_processing_regimes_section_exists(self, evaluator_defaults):
        """evaluator_defaults.yml must have a processing_regimes section."""
        assert "processing_regimes" in evaluator_defaults

    @pytest.mark.tdd
    def test_processing_regimes_has_conscious_and_reflex(self, evaluator_defaults):
        """processing_regimes must define both conscious and reflex regimes."""
        regimes = evaluator_defaults["processing_regimes"]
        assert "conscious" in regimes
        assert "reflex" in regimes

    @pytest.mark.tdd
    def test_processing_regimes_have_descriptions(self, evaluator_defaults):
        """Each processing regime must have description, analogy, includes, fires_when."""
        for name, regime in evaluator_defaults["processing_regimes"].items():
            assert "description" in regime, f"regime '{name}' missing description"
            assert "analogy" in regime, f"regime '{name}' missing analogy"
            assert "includes" in regime, f"regime '{name}' missing includes"
            assert "fires_when" in regime, f"regime '{name}' missing fires_when"
