# Validates: REQ-F-NAMEDCOMP-001 (Named Composition Library — NC-001)
# Validates: REQ-INTENT-002 (Intent as Spec — typed composition in escalate output)
# Reference: ADR-S-026 §3, specification/features/NAMEDCOMP_DESIGN_RECOMMENDATIONS.md §Phase 1
"""Tests for named composition registry schema, dispatch table, and project-local shadow rule."""

import pathlib

import pytest
import yaml

from genesis.config_loader import load_named_compositions, resolve_composition


# ─── Fixtures ────────────────────────────────────────────────────────────────

PLUGIN_ROOT = pathlib.Path(__file__).parent.parent / "code" / ".claude-plugin" / "plugins" / "genesis"
NAMED_COMP_FILE = PLUGIN_ROOT / "config" / "named_compositions.yml"


@pytest.fixture
def registry():
    """Load the library named_compositions registry."""
    return load_named_compositions(PLUGIN_ROOT)


@pytest.fixture
def raw_yaml():
    """Parse named_compositions.yml directly."""
    with open(NAMED_COMP_FILE) as f:
        return yaml.safe_load(f)


# ─── P1: Registry Schema ─────────────────────────────────────────────────────

class TestRegistrySchema:
    """named_compositions.yml exists and has the correct top-level schema."""

    def test_file_exists(self):
        assert NAMED_COMP_FILE.exists(), "named_compositions.yml must exist"

    def test_has_version_field(self, raw_yaml):
        assert "version" in raw_yaml

    def test_has_scope_field(self, raw_yaml):
        assert raw_yaml.get("scope") == "library"

    def test_has_compositions_list(self, raw_yaml):
        assert isinstance(raw_yaml.get("compositions"), list)
        assert len(raw_yaml["compositions"]) > 0

    def test_has_gap_type_dispatch(self, raw_yaml):
        assert isinstance(raw_yaml.get("gap_type_dispatch"), dict)
        assert len(raw_yaml["gap_type_dispatch"]) > 0

    def test_four_named_compositions_present(self, raw_yaml):
        names = {c["name"] for c in raw_yaml["compositions"]}
        assert {"PLAN", "POC", "SCHEMA_DISCOVERY", "DATA_DISCOVERY"}.issubset(names)


class TestCompositionFields:
    """Each composition has required fields."""

    @pytest.fixture(params=["PLAN", "POC", "SCHEMA_DISCOVERY", "DATA_DISCOVERY"])
    def composition(self, request, raw_yaml):
        name = request.param
        return next(c for c in raw_yaml["compositions"] if c["name"] == name)

    def test_has_name(self, composition):
        assert "name" in composition

    def test_has_version(self, composition):
        assert "version" in composition
        assert composition["version"].startswith("v")

    def test_has_scope(self, composition):
        assert composition.get("scope") in ("library", "project-local")

    def test_has_governance(self, composition):
        assert composition.get("governance") in ("consensus", "review")

    def test_has_description(self, composition):
        assert isinstance(composition.get("description"), str)
        assert len(composition["description"]) > 0

    def test_has_parameters_list(self, composition):
        params = composition.get("parameters", [])
        assert isinstance(params, list)

    def test_has_output_type(self, composition):
        assert "output_type" in composition

    def test_has_body(self, composition):
        assert isinstance(composition.get("body"), list)
        assert len(composition["body"]) > 0

    def test_body_has_functor_and_args(self, composition):
        for step in composition["body"]:
            assert "functor" in step
            assert "args" in step


class TestGapTypeDispatch:
    """gap_type_dispatch table has required entries and correct structure."""

    def test_required_gap_types_present(self, raw_yaml):
        dispatch = raw_yaml["gap_type_dispatch"]
        required_types = {
            "missing_schema", "missing_requirements", "missing_design",
            "unknown_risk", "unknown_domain",
        }
        assert required_types.issubset(set(dispatch.keys()))

    def test_each_entry_has_macro_and_version(self, raw_yaml):
        for gap_type, entry in raw_yaml["gap_type_dispatch"].items():
            assert "macro" in entry, f"{gap_type} missing macro"
            assert "version" in entry, f"{gap_type} missing version"

    def test_each_entry_has_default_bindings(self, raw_yaml):
        for gap_type, entry in raw_yaml["gap_type_dispatch"].items():
            assert "default_bindings" in entry, f"{gap_type} missing default_bindings"
            assert isinstance(entry["default_bindings"], dict), f"{gap_type} default_bindings not a dict"

    def test_missing_schema_maps_to_schema_discovery(self, raw_yaml):
        entry = raw_yaml["gap_type_dispatch"]["missing_schema"]
        assert entry["macro"] == "SCHEMA_DISCOVERY"

    def test_missing_requirements_maps_to_plan(self, raw_yaml):
        entry = raw_yaml["gap_type_dispatch"]["missing_requirements"]
        assert entry["macro"] == "PLAN"
        assert entry["default_bindings"].get("unit_type") == "capability"

    def test_unknown_risk_maps_to_poc(self, raw_yaml):
        entry = raw_yaml["gap_type_dispatch"]["unknown_risk"]
        assert entry["macro"] == "POC"


# ─── P1: load_named_compositions() ───────────────────────────────────────────

class TestLoadNamedCompositions:
    """load_named_compositions() returns correct merged registry."""

    def test_returns_dict(self, registry):
        assert isinstance(registry, dict)

    def test_has_compositions_list(self, registry):
        assert isinstance(registry["compositions"], list)
        assert len(registry["compositions"]) >= 4

    def test_has_gap_type_dispatch(self, registry):
        assert isinstance(registry["gap_type_dispatch"], dict)

    def test_library_count_tracked(self, registry):
        assert "_library_count" in registry
        assert registry["_library_count"] >= 4

    def test_project_local_count_zero_without_workspace(self, registry):
        assert registry["_project_local_count"] == 0

    def test_load_with_nonexistent_workspace_root(self, tmp_path):
        """Should succeed gracefully when workspace root has no named_compositions dir."""
        reg = load_named_compositions(PLUGIN_ROOT, workspace_root=tmp_path)
        assert len(reg["compositions"]) >= 4

    def test_load_with_project_local_shadow(self, tmp_path):
        """Project-local entry shadows library entry by {name, version}."""
        nc_dir = tmp_path / ".ai-workspace" / "named_compositions"
        nc_dir.mkdir(parents=True)
        local_file = nc_dir / "custom.yml"
        local_file.write_text(
            "compositions:\n"
            "  - name: PLAN\n"
            "    version: v1\n"
            "    scope: project-local\n"
            "    governance: review\n"
            "    description: 'Local PLAN override'\n"
            "    parameters: []\n"
            "    output_type: work_order\n"
            "    body: [{functor: CUSTOM, args: {}}]\n"
        )
        reg = load_named_compositions(PLUGIN_ROOT, workspace_root=tmp_path)
        plan = next(c for c in reg["compositions"] if c["name"] == "PLAN" and c["version"] == "v1")
        assert plan["scope"] == "project-local"
        assert plan["description"] == "Local PLAN override"

    def test_project_local_count_incremented_on_shadow(self, tmp_path):
        nc_dir = tmp_path / ".ai-workspace" / "named_compositions"
        nc_dir.mkdir(parents=True)
        local_file = nc_dir / "custom.yml"
        local_file.write_text(
            "compositions:\n"
            "  - name: PLAN\n"
            "    version: v1\n"
            "    scope: project-local\n"
            "    governance: review\n"
            "    description: 'Local override'\n"
            "    parameters: []\n"
            "    output_type: work_order\n"
            "    body: [{functor: X, args: {}}]\n"
        )
        reg = load_named_compositions(PLUGIN_ROOT, workspace_root=tmp_path)
        assert reg["_project_local_count"] == 1


# ─── P1: resolve_composition() ───────────────────────────────────────────────

class TestResolveComposition:
    """resolve_composition() dispatch table lookup."""

    def test_resolve_known_gap_type(self, registry):
        comp, status = resolve_composition("missing_schema", registry)
        assert status == "resolved"
        assert comp is not None
        assert comp["macro"] == "SCHEMA_DISCOVERY"
        assert comp["version"] == "v1"

    def test_resolve_unknown_gap_type_returns_no_dispatch_entry(self, registry):
        comp, status = resolve_composition("nonexistent_gap_type", registry)
        assert comp is None
        assert status == "no_dispatch_entry"

    def test_caller_bindings_override_defaults(self, registry):
        comp, status = resolve_composition(
            "missing_requirements",
            registry,
            extra_bindings={"unit_type": "module"},
        )
        assert status == "resolved"
        assert comp["bindings"]["unit_type"] == "module"

    def test_default_bindings_preserved_when_no_extra(self, registry):
        comp, status = resolve_composition("missing_requirements", registry)
        assert status == "resolved"
        assert comp["bindings"]["unit_type"] == "capability"
        assert comp["bindings"]["criteria"] == "user_value"

    def test_resolve_placeholder_macro_returns_unresolvable(self, registry):
        """spec_drift maps to EVOLVE which is not yet a defined composition."""
        comp, status = resolve_composition("spec_drift", registry)
        # EVOLVE is in dispatch table but not in compositions list
        assert comp is not None
        assert comp["macro"] == "EVOLVE"
        assert status == "unresolvable"

    def test_resolved_composition_has_three_fields(self, registry):
        comp, _ = resolve_composition("missing_design", registry)
        assert set(comp.keys()) == {"macro", "version", "bindings"}
